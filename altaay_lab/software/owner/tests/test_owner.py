"""Owner setup, signed updates, the home page, and low-pack shutdown.

No hardware. Update keys are minted in a temporary directory and removed.
Run from the repo root:
  python3 -m unittest discover -s altaay_lab/software/owner/tests -v
"""

from __future__ import annotations

import json
import os
import socket
import stat
import subprocess
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request

from altaay_lab.software.companion.config import load_config
from altaay_lab.software.owner import pairing, store
from altaay_lab.software.owner.lowpack import (
    apply_allowed,
    consider,
    should_shut_down,
)
from altaay_lab.software.owner.net import (
    MockNet,
    ap_commands,
    check_passphrase,
    hostapd_conf,
    wifi_supplicant_conf,
)
from altaay_lab.software.owner.pages import DEMO_BANNER
from altaay_lab.software.owner.peers import parse_ip_addr, setup_peer_ok, status_peer_ok
from altaay_lab.software.owner.privacy import PRIVACY
from altaay_lab.software.owner.selftest import run_self_test
from altaay_lab.software.owner.service import child_exit_code, serve, walk_argv
from altaay_lab.software.owner.setup_flow import SetupError, SetupSession, kid_from_form
from altaay_lab.software.owner.update_flow import (
    PUBLIC_KEY,
    UpdateError,
    apply_update,
    build_bundle,
    demo_rollback,
    read_version,
    seed_slot,
)
from altaay_lab.software.owner.web import serve_setup, serve_status
from altaay_lab.software.personality.limits import PACK_WALK_STOP_V

HERE = os.path.dirname(os.path.abspath(__file__))
OWNER = os.path.dirname(HERE)
SOFT = os.path.dirname(OWNER)
REPO = os.path.dirname(os.path.dirname(os.path.dirname(OWNER)))
HOME_SECRET = "home-secret-phrase"


def _text(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def _key(tmp):
    private = os.path.join(tmp, "private.pem")
    public = os.path.join(tmp, "public.pem")
    subprocess.check_call(
        ["openssl", "genpkey", "-algorithm", "ED25519", "-out", private],
        timeout=20,
    )
    subprocess.check_call(
        ["openssl", "pkey", "-in", private, "-pubout", "-out", public],
        timeout=20,
    )
    return private, public


def _open(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.read().decode("utf-8"), resp.headers
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8"), exc.headers


class PairingTests(unittest.TestCase):
    def test_code_is_not_a_factory_password(self):
        seen = set()
        for _ in range(20):
            code = pairing.generate_code()
            seen.add(code)
            self.assertEqual(len(code), pairing.LENGTH)
            self.assertTrue(set(code) <= set(pairing.ALPHABET))
            self.assertNotIn(code.lower(), pairing.BANNED)
        self.assertGreater(len(seen), 1)
        self.assertNotEqual(pairing.generate_code(), "password")

    def test_qr_and_spoken_line_carry_the_code_only(self):
        code = "ABCDEFGH"
        ssid = pairing.ssid_for(code)
        payload = pairing.wifi_qr_payload(ssid, code)
        self.assertIn("WIFI:T:WPA;S:%s;P:%s;;" % (ssid, code), payload)
        spoken = pairing.spoken_line(ssid, code)
        self.assertIn("A B C D E F G H", spoken)
        self.assertNotIn(HOME_SECRET, spoken)
        escaped = pairing.wifi_qr_payload("A;B", "C:D")
        self.assertIn("A\\;B", escaped)
        self.assertIn("C\\:D", escaped)


class SetupTests(unittest.TestCase):
    def _form(self, code, **extra):
        form = {
            "pairing_code": code,
            "name": "Duckie",
            "timezone": "UTC",
            "kid_mode": "kid",
            "home_ssid": "House",
            "home_passphrase": HOME_SECRET,
        }
        form.update(extra)
        return form

    def test_setup_saves_kid_mode_and_forgets_the_plain_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            net = MockNet()
            session = SetupSession(tmp, net)
            code = session.begin()
            self.assertTrue(net.ap_up)
            owner = session.submit(self._form(code))
            self.assertEqual(owner["name"], "Duckie")
            self.assertTrue(owner["kid_mode"])
            self.assertEqual(owner["timezone"], "UTC")
            self.assertNotIn("passphrase", owner)
            self.assertNotIn(HOME_SECRET, json.dumps(owner))
            self.assertFalse(os.path.exists(store.path(tmp, store.PAIRING_PLAIN)))
            self.assertFalse(net.ap_up)
            wifi_path = store.path(tmp, store.WIFI)
            self.assertEqual(stat.S_IMODE(os.stat(wifi_path).st_mode), 0o600)
            wifi = store.read_json(wifi_path)
            self.assertEqual(wifi["passphrase"], HOME_SECRET)
            self.assertTrue(pairing.pairing_ok(store.load_owner(tmp), code))
            joined = [row for row in net.events if row["op"] == "join_wifi"]
            self.assertEqual(joined[0]["ssid"], "House")
            self.assertNotIn("passphrase", joined[0])
            spoken = " ".join(row["text"] for row in net.events if row["op"] == "speak")
            self.assertNotIn(HOME_SECRET, spoken)
            self.assertIn(PRIVACY, spoken)
            cfg = load_config(store.path(tmp, store.VOICE))
            self.assertEqual(cfg["mode"], "kid")
            self.assertEqual(cfg["cloud"], "off")
            with self.assertRaises(SetupError):
                session.submit(self._form(code))

    def test_missing_kid_field_stays_kid_and_adult_is_explicit(self):
        self.assertTrue(kid_from_form(None))
        self.assertTrue(kid_from_form("kid"))
        self.assertFalse(kid_from_form("adult"))
        with tempfile.TemporaryDirectory() as tmp:
            net = MockNet()
            session = SetupSession(tmp, net)
            code = session.begin()
            form = self._form(code)
            del form["kid_mode"]
            owner = session.submit(form)
            self.assertTrue(owner["kid_mode"])

    def test_cloud_field_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = SetupSession(tmp, MockNet())
            code = session.begin()
            form = self._form(code, cloud="me@example.com")
            with self.assertRaises(SetupError) as caught:
                session.submit(form)
            self.assertIn("cloud", str(caught.exception))
            self.assertIsNone(store.load_owner(tmp))

    def test_wrong_code_and_rate_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = SetupSession(tmp, MockNet(), clock=lambda: 1000.0)
            code = session.begin()
            with self.assertRaises(SetupError):
                session.submit(self._form("ZZZZZZZZ"))
            self.assertNotEqual("ZZZZZZZZ", code)
            session.fails = [1000.0] * 8
            self.assertTrue(session.limited(1000.0))
            with self.assertRaises(SetupError) as caught:
                session.submit(self._form(code))
            self.assertEqual(caught.exception.status, 429)

    def test_http_page_shows_the_code_and_saves(self):
        with tempfile.TemporaryDirectory() as tmp:
            net = MockNet()
            session = SetupSession(tmp, net)
            code = session.begin()
            httpd = serve_setup(session, "127.0.0.1", 0, allow_loopback=True, demo=True)
            try:
                base = "http://127.0.0.1:%s" % httpd.server_address[1]
                status, page, _headers = _open(base + "/")
                self.assertEqual(status, 200)
                self.assertIn(code, page)
                self.assertIn(DEMO_BANNER, page)
                self.assertIn("not uploaded", page)
                self.assertIn("<svg", page)
                self.assertNotIn('name="cloud"', page)
                self.assertNotIn('name="password"', page)
                body = urllib.parse.urlencode(self._form(code, name="Quack")).encode()
                status, done, _headers = _open(base + "/setup", data=body)
                self.assertEqual(status, 200, done)
                self.assertIn("Quack is set up", done)
                self.assertFalse(net.ap_up)
                self.assertEqual(store.load_owner(tmp)["name"], "Quack")
            finally:
                httpd.shutdown()
                httpd.server_close()

    def test_setup_refuses_loopback_when_the_demo_flag_is_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = SetupSession(tmp, MockNet())
            session.begin()
            httpd = serve_setup(session, "127.0.0.1", 0, allow_loopback=False, demo=False)
            try:
                status, body, _headers = _open("http://127.0.0.1:%s/" % httpd.server_address[1])
                self.assertEqual(status, 403)
                self.assertIn("temporary setup network", body)
            finally:
                httpd.shutdown()
                httpd.server_close()


class PeerTests(unittest.TestCase):
    def test_home_page_is_lan_only(self):
        self.assertTrue(status_peer_ok("192.168.1.20"))
        self.assertTrue(status_peer_ok("10.1.2.3"))
        self.assertTrue(status_peer_ok("172.16.5.5"))
        self.assertTrue(status_peer_ok("fd12::1"))
        self.assertFalse(status_peer_ok("192.168.4.10"))
        self.assertFalse(status_peer_ok("8.8.8.8"))
        self.assertFalse(status_peer_ok("172.32.0.1"))
        self.assertFalse(status_peer_ok("169.254.1.1"))
        self.assertFalse(status_peer_ok("127.0.0.1"))
        self.assertTrue(status_peer_ok("127.0.0.1", allow_loopback=True))
        self.assertTrue(setup_peer_ok("192.168.4.20"))
        self.assertFalse(setup_peer_ok("192.168.1.20"))
        sample = "2: eth0    inet 192.168.1.20/24 brd 192.168.1.255 scope global eth0\n"
        sample += "3: wlan0    inet 192.168.4.1/24 scope global wlan0\n"
        self.assertEqual(parse_ip_addr(sample), ["192.168.1.20", "192.168.4.1"])


class StatusTests(unittest.TestCase):
    def test_page_shows_the_log_and_hides_it_from_the_public_internet(self):
        with tempfile.TemporaryDirectory() as tmp:
            net = MockNet()
            session = SetupSession(tmp, net)
            code = session.begin()
            session.submit({
                "pairing_code": code,
                "name": "Duckie",
                "timezone": "UTC",
                "kid_mode": "kid",
                "home_ssid": "House",
                "home_open": "yes",
            })
            log = "\n".join([
                '{"t": 1, "kind": "dock_attempt", "mode": "dock", "pack_v": 11.2, "knee_c": 31.5}',
                '{"t": 2, "kind": "dock_result", "mode": "wander", "pack_v": 11.11, "knee_c": 33.25, "ok": true, "falls": 2}',
                "",
            ])
            store.write_text(store.log_path(tmp), log, 0o644)
            store.write_text(os.path.join(tmp, "secret.txt"), "SECRET-FILE", 0o600)
            closed = serve_status(tmp, "127.0.0.1", 0, allow_loopback=False, demo=True)
            try:
                status, body, _headers = _open("http://127.0.0.1:%s/" % closed.server_address[1])
                self.assertEqual(status, 403)
                self.assertNotIn("11.11", body)
                self.assertNotIn("SECRET-FILE", body)
            finally:
                closed.shutdown()
                closed.server_close()
            httpd = serve_status(tmp, "127.0.0.1", 0, allow_loopback=True, demo=True)
            try:
                base = "http://127.0.0.1:%s" % httpd.server_address[1]
                status, page, _headers = _open(base + "/")
                self.assertEqual(status, 200)
                self.assertIn("Pairing code", page)
                self.assertNotIn("11.11", page)
                bad = urllib.parse.urlencode({"pairing_code": "ZZZZZZZZ"}).encode()
                status, _body, _headers = _open(base + "/login", data=bad)
                self.assertEqual(status, 403)
                good = urllib.parse.urlencode({"pairing_code": code}).encode()
                status, page, headers = _open(base + "/login", data=good)
                self.assertEqual(status, 200, page)
                self.assertIn(DEMO_BANNER, page)
                self.assertIn("11.11", page)
                self.assertIn("33.25", page)
                self.assertIn(">2<", page)
                self.assertIn("dock_result", page)
                self.assertIn("not uploaded", page)
                cookie = headers.get("Set-Cookie")
                self.assertIn("HttpOnly", cookie)
                self.assertNotIn(code, cookie)
                token = cookie.split(";", 1)[0]
                status, downloaded, _headers = _open(
                    base + "/logs?file=secret.txt",
                    headers={"Cookie": token},
                )
                self.assertEqual(status, 200)
                self.assertIn("dock_attempt", downloaded)
                self.assertNotIn("SECRET-FILE", downloaded)
                status, locked, _headers = _open(base + "/logs")
                self.assertNotIn("dock_attempt", locked)
            finally:
                httpd.shutdown()
                httpd.server_close()


class UpdateTests(unittest.TestCase):
    def test_repo_key_is_public_and_the_tree_has_no_private_key(self):
        text = _text(PUBLIC_KEY)
        self.assertIn("BEGIN PUBLIC KEY", text)
        self.assertNotIn("PRIVATE", text)
        proc = subprocess.run(
            ["openssl", "pkey", "-pubin", "-in", PUBLIC_KEY, "-noout"],
            check=False,
            capture_output=True,
            timeout=20,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        needle = "BEGIN " + "PRIVATE KEY"
        for folder, dirs, files in os.walk(OWNER):
            dirs[:] = [name for name in dirs if name != "__pycache__"]
            for name in files:
                path = os.path.join(folder, name)
                if os.path.getsize(path) > 1000000:
                    continue
                blob = _bytes(path)
                self.assertNotIn(needle.encode("ascii"), blob, path)

    def test_good_update_then_failed_walk_rolls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            private, public = _key(tmp)
            state = os.path.join(tmp, "state")
            seed_slot(state, "a", "1.0.0", "factory\n")
            good = os.path.join(tmp, "good.tar")
            bad = os.path.join(tmp, "bad.tar")
            build_bundle(good, "1.0.1", {"marker.txt": b"good\n"}, private)
            build_bundle(bad, "1.1.0", {"marker.txt": b"bad\n"}, private, health={"walk": "fail"})
            landed = apply_update(good, state, public)
            self.assertTrue(landed["ok"])
            self.assertEqual(landed["slot"], "b")
            self.assertEqual(read_version(state, "b"), "1.0.1")
            self.assertEqual(store.read_current(state), "b")
            rolled = apply_update(bad, state, public)
            self.assertTrue(rolled["rolled_back"])
            self.assertEqual(rolled["failures"], ["walk"])
            self.assertEqual(store.read_current(state), "b")
            self.assertEqual(read_version(state, "b"), "1.0.1")
            marker = _bytes(os.path.join(store.slot_path(state, "b"), "payload", "marker.txt"))
            self.assertEqual(marker, b"good\n")
            record = store.read_json(store.path(state, store.ROLLBACK))
            self.assertEqual(record["failed_version"], "1.1.0")
            self.assertEqual(record["restored_version"], "1.0.1")
            self.assertEqual(record["label"], "measured in emulation")

    def test_failed_supervisor_rolls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            private, public = _key(tmp)
            state = os.path.join(tmp, "state")
            seed_slot(state, "a", "1.0.0", "factory\n")
            bad = os.path.join(tmp, "bad.tar")
            build_bundle(bad, "9.0.0", {"marker.txt": b"x\n"}, private, health={"supervisor": "fail"})
            rolled = apply_update(bad, state, public)
            self.assertTrue(rolled["rolled_back"])
            self.assertEqual(rolled["failures"], ["supervisor"])
            self.assertEqual(store.read_current(state), "a")
            self.assertEqual(read_version(state, "a"), "1.0.0")

    def test_wrong_key_and_tamper_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            private, public = _key(tmp)
            state = os.path.join(tmp, "state")
            os.makedirs(state)
            bundle = os.path.join(tmp, "bundle.tar")
            build_bundle(bundle, "1.2.0", {"marker.txt": b"ok\n"}, private)
            with self.assertRaises(UpdateError):
                apply_update(bundle, state, PUBLIC_KEY)
            self.assertIsNone(store.read_current(state))
            tampered = os.path.join(tmp, "tampered.tar")
            _repack_changed(bundle, tampered)
            with self.assertRaises(UpdateError):
                apply_update(tampered, state, public)
            self.assertIsNone(store.read_current(state))

    def test_real_self_test_passes_on_a_clean_slot(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "payload"))
            ok, failures = run_self_test(tmp)
            self.assertTrue(ok, failures)

    def test_demo_rollback_command(self):
        proc = subprocess.run(
            [os.environ.get("PYTHON", "python3"), "-m", "altaay_lab.software.owner.run_update", "--demo-rollback"],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("Desktop demo, not the robot.", proc.stdout)
        self.assertIn("measured in emulation", proc.stdout)
        self.assertIn("rollback: current is a version 1.0.0", proc.stdout)
        self.assertIn("self-test walk: fail", proc.stdout)
        result = demo_rollback()
        self.assertTrue(result["rollback"]["rolled_back"])
        self.assertEqual(result["good"]["version"], "1.0.1")


class LowPackTests(unittest.TestCase):
    def test_cited_stop_shuts_down_and_charge_does_not(self):
        self.assertTrue(should_shut_down({"pack_v": PACK_WALK_STOP_V, "mode": "sit"}))
        self.assertTrue(should_shut_down({"pack_v": PACK_WALK_STOP_V - 0.1, "mode": "stuck"}))
        self.assertFalse(should_shut_down({"pack_v": PACK_WALK_STOP_V + 0.01, "mode": "sit"}))
        self.assertFalse(should_shut_down({"pack_v": PACK_WALK_STOP_V, "mode": "charge"}))
        self.assertFalse(should_shut_down({"mode": "sit"}))
        self.assertFalse(should_shut_down(None))
        with tempfile.TemporaryDirectory() as tmp:
            calls = []
            text = '{"t": 1, "mode": "sit", "pack_v": %s}\n' % PACK_WALK_STOP_V
            plan = consider(tmp, calls.append, text)
            self.assertIsNotNone(plan)
            flat = [" ".join(cmd) for cmd in calls]
            self.assertEqual(flat, [
                "/usr/bin/systemctl stop odm-walk.service",
                "/usr/bin/systemctl stop odm-perception.service",
                "/usr/bin/systemctl stop odm-voice.service",
                "/usr/bin/systemctl stop odm-supervisor.service",
                "/usr/bin/systemctl poweroff",
            ])
            self.assertFalse(apply_allowed(tmp))
            proc = subprocess.run(
                ["python3", "-m", "altaay_lab.software.owner.run_lowpack", "--state", tmp, "--apply", "--once"],
                cwd=REPO,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 2, proc.stderr)
            self.assertIn("refusing", proc.stderr)


class ServiceTests(unittest.TestCase):
    def test_units_have_watchdogs_and_the_guard_unit_still_does_not_restart(self):
        for name in (
            "odm-supervisor.service",
            "odm-voice.service",
            "odm-perception.service",
            "odm-walk.service",
        ):
            text = _text(os.path.join(SOFT, name))
            self.assertIn("WatchdogSec=", text, name)
            self.assertIn("StartLimitBurst=3", text, name)
            self.assertIn("StartLimitIntervalSec=300", text, name)
        walk = _text(os.path.join(SOFT, "odm-walk.service"))
        self.assertIn("RestartPreventExitStatus=4 6 7 8 9 10 11", walk)
        self.assertIn("ODM_HW_PWM=1", walk)
        guard = _text(os.path.join(SOFT, "odm-walk-guard.service"))
        self.assertIn("Restart=no", guard)
        argv = walk_argv("/home/duck")
        self.assertIn("--knee-heat", argv)
        source = _text(os.path.join(OWNER, "service.py"))
        self.assertNotIn("import antennas", source)
        self.assertEqual(child_exit_code(6), 0)
        self.assertEqual(child_exit_code(7), 0)
        self.assertEqual(child_exit_code(3), 3)

    def test_voice_exits_cleanly_on_low_pack(self):
        with tempfile.TemporaryDirectory() as tmp:
            sock_path = os.path.join(tmp, "notify.sock")
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            sock.bind(sock_path)
            sock.settimeout(0.2)
            old = os.environ.get("NOTIFY_SOCKET")
            os.environ["NOTIFY_SOCKET"] = sock_path
            stop = threading.Event()
            box = {}

            def run():
                box["code"] = serve("voice", tmp, stop, interval=0.05)

            thread = threading.Thread(target=run)
            thread.start()
            try:
                notes = []
                while len(notes) < 2:
                    try:
                        data, _addr = sock.recvfrom(256)
                    except socket.timeout:
                        break
                    notes.append(data.decode("utf-8"))
                self.assertIn("READY=1", notes)
                store.write_json(store.path(tmp, store.SHUTDOWN_REQUEST), {"reason": "test"}, 0o644)
                thread.join(2)
                self.assertFalse(thread.is_alive())
                self.assertEqual(box["code"], 0)
                heart = store.read_json(store.path(tmp, "heartbeat-voice.json"))
                self.assertIn("not uploaded", heart["privacy"])
            finally:
                stop.set()
                thread.join(2)
                if old is None:
                    os.environ.pop("NOTIFY_SOCKET", None)
                else:
                    os.environ["NOTIFY_SOCKET"] = old
                sock.close()

    def test_passphrase_stays_out_of_command_arguments(self):
        with self.assertRaises(Exception):
            check_passphrase("password")
        with self.assertRaises(Exception):
            check_passphrase("short")
        conf = hostapd_conf("Duckie-ABCD", "ABCDEFGH")
        self.assertIn("wpa_passphrase=ABCDEFGH", conf)
        self.assertNotIn("password", conf)
        commands = ap_commands(
            "/var/lib/odm/hostapd-setup.conf",
            "/var/lib/odm/dnsmasq-setup.conf",
            "/var/lib/odm/hostapd-setup.pid",
            "/var/lib/odm/dnsmasq-setup.pid",
        )
        flat = " ".join(" ".join(cmd) for cmd in commands)
        self.assertNotIn("ABCDEFGH", flat)
        wifi = wifi_supplicant_conf("House", HOME_SECRET, False)
        self.assertIn(HOME_SECRET, wifi)
        self.assertNotIn(HOME_SECRET, flat)


def _repack_changed(src, dest):
    import io
    import tarfile
    files = {}
    with tarfile.open(src, "r") as tar:
        for member in tar.getmembers():
            handle = tar.extractfile(member)
            files[member.name] = b"" if handle is None else handle.read()
    files["payload/marker.txt"] = b"tampered\n"
    with tarfile.open(dest, "w") as tar:
        for name in sorted(files):
            info = tarfile.TarInfo(name)
            info.size = len(files[name])
            info.mtime = 0
            tar.addfile(info, io.BytesIO(files[name]))


if __name__ == "__main__":
    unittest.main()
