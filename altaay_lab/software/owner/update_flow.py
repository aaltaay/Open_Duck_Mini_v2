"""Signed update bundles and A/B slots.

The signature is Ed25519, checked with openssl and the public key in this
folder. A private key is never read from the repository. Tests mint a key
in a temporary directory and delete it.

After the pointer moves, the walk and supervisor self-tests run. A failure
moves the pointer back. Measured in emulation.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile
import tempfile

from . import selftest, store

PUBLIC_KEY = os.path.join(os.path.dirname(__file__), "update_public_key.pem")
LABEL = "measured in emulation"
# A slot entry whose own checks pass. The checkout guards still run.
PASSING_ENTRY = b"def walk_ok():\n    return True\n\ndef supervisor_ok():\n    return True\n"


class UpdateError(Exception):
    pass


def _openssl(*args):
    try:
        proc = subprocess.run(
            ["openssl", *args],
            check=False,
            capture_output=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise UpdateError("openssl failed") from exc
    return proc.returncode == 0


def sign_bytes(data, private_key_path):
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "manifest.json")
        dst = os.path.join(tmp, "manifest.sig")
        with open(src, "wb") as handle:
            handle.write(data)
        ok = _openssl(
            "pkeyutl", "-sign", "-inkey", private_key_path,
            "-rawin", "-in", src, "-out", dst,
        )
        if not ok or not os.path.isfile(dst):
            raise UpdateError("could not sign the manifest")
        with open(dst, "rb") as handle:
            return handle.read()


def verify_bytes(data, signature, public_key_path):
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "manifest.json")
        dst = os.path.join(tmp, "manifest.sig")
        with open(src, "wb") as handle:
            handle.write(data)
        with open(dst, "wb") as handle:
            handle.write(signature)
        return _openssl(
            "pkeyutl", "-verify", "-pubin", "-inkey", public_key_path,
            "-rawin", "-in", src, "-sigfile", dst,
        )


def _version_ok(version):
    text = str(version or "")
    if not text or len(text) > 32:
        return False
    for ch in text:
        if not (ch.isalnum() or ch in "._-"):
            return False
    return True


def build_bundle(path, version, payload, private_key_path, health=None):
    """Write a tar. payload maps a relative path to bytes. health is optional.

    health {"walk": "fail"} or {"supervisor": "fail"} is how a test asks the
    self-test to fail. It is inside the signed payload.
    """
    if not _version_ok(version):
        raise UpdateError("bad version")
    files = dict(payload or {})
    for name in files:
        if (
            not name
            or name != os.path.normpath(name)
            or name.startswith("/")
            or "/" in name
            or ".." in name.split("/")
        ):
            raise UpdateError("bad payload path")
    if health is not None:
        files["health_request.json"] = json.dumps(health, sort_keys=True).encode("utf-8")
    listed = []
    for name in sorted(files):
        listed.append({
            "path": name,
            "sha256": hashlib.sha256(files[name]).hexdigest(),
        })
    manifest = {"files": listed, "version": version}
    raw = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = sign_bytes(raw, private_key_path)
    with tarfile.open(path, "w") as tar:
        _add(tar, "manifest.json", raw)
        _add(tar, "manifest.json.sig", signature)
        for name in sorted(files):
            _add(tar, "payload/" + name, files[name])
    return path


def _add(tar, name, data):
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mtime = 0
    info.mode = 0o644
    tar.addfile(info, io.BytesIO(data))


def _safe_extract(tar, dest):
    for member in tar.getmembers():
        name = member.name
        if member.issym() or member.islnk() or member.isdev():
            raise UpdateError("refusing a link in the bundle")
        parts = name.split("/")
        if name.startswith("/") or ".." in parts or not name:
            raise UpdateError("bad path in the bundle")
        if name not in ("manifest.json", "manifest.json.sig") and not name.startswith("payload/"):
            raise UpdateError("unexpected file in the bundle")
        if not member.isfile():
            continue
        target = os.path.join(dest, name)
        folder = os.path.dirname(target)
        os.makedirs(folder, exist_ok=True)
        src = tar.extractfile(member)
        if src is None:
            raise UpdateError("missing file in the bundle")
        with open(target, "wb") as handle:
            handle.write(src.read())


def _inactive(current):
    if current == "a":
        return "b"
    return "a"


def read_version(state, slot):
    file_path = os.path.join(store.slot_path(state, slot), "VERSION")
    if not os.path.isfile(file_path):
        return None
    with open(file_path, encoding="utf-8") as handle:
        return handle.read().strip()


def seed_slot(state, slot, version, marker):
    """Put a known-good slot in place. Used by tests and the demo."""
    folder = store.slot_path(state, slot)
    os.makedirs(os.path.join(folder, "payload"), exist_ok=True)
    store.write_text(os.path.join(folder, "VERSION"), version + "\n", 0o644)
    store.write_text(os.path.join(folder, "payload", "marker.txt"), marker, 0o644)
    store.write_current(state, slot)


def apply_update(bundle_path, state, public_key_path=None, self_test=None):
    public_key_path = public_key_path or PUBLIC_KEY
    self_test = self_test or selftest.run_self_test
    store.ensure(state)
    with tempfile.TemporaryDirectory(dir=state) as unpacked:
        try:
            with tarfile.open(bundle_path, "r") as tar:
                _safe_extract(tar, unpacked)
        except tarfile.TarError as exc:
            raise UpdateError("the bundle is not a tar file") from exc
        manifest_path = os.path.join(unpacked, "manifest.json")
        sig_path = os.path.join(unpacked, "manifest.json.sig")
        if not os.path.isfile(manifest_path) or not os.path.isfile(sig_path):
            raise UpdateError("the bundle has no signature")
        with open(manifest_path, "rb") as handle:
            raw = handle.read()
        with open(sig_path, "rb") as handle:
            signature = handle.read()
        if not verify_bytes(raw, signature, public_key_path):
            raise UpdateError("signature check failed")
        try:
            manifest = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise UpdateError("the manifest is not json") from exc
        version = manifest.get("version")
        if not _version_ok(version):
            raise UpdateError("bad version")
        verified = []
        for row in manifest.get("files") or []:
            rel = row.get("path")
            if not rel or "/" in rel or rel in (".", "..") or rel != os.path.normpath(rel):
                raise UpdateError("bad file in the manifest")
            file_path = os.path.join(unpacked, "payload", rel)
            if not os.path.isfile(file_path):
                raise UpdateError("a signed file is missing")
            with open(file_path, "rb") as handle:
                digest = hashlib.sha256(handle.read()).hexdigest()
            if digest != row.get("sha256"):
                raise UpdateError("a signed file was changed")
            verified.append(rel)
        payload_src = os.path.join(unpacked, "payload")
        if os.path.isdir(payload_src):
            for name in os.listdir(payload_src):
                if name not in verified:
                    raise UpdateError("unsigned file in the bundle")
        previous = store.read_current(state)
        slot = _inactive(previous)
        dest = store.slot_path(state, slot)
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        os.makedirs(os.path.join(dest, "payload"), exist_ok=True)
        for name in verified:
            shutil.copy2(
                os.path.join(payload_src, name),
                os.path.join(dest, "payload", name),
            )
        store.write_text(os.path.join(dest, "VERSION"), version + "\n", 0o644)
        store.write_current(state, slot)
        try:
            ok, failures = self_test(dest)
        except Exception as exc:  # noqa: BLE001 - a crashed self-test is a failed update
            ok, failures = False, ["self-test-error"]
            _ = exc
        if ok:
            store.write_json(store.path(state, store.HEALTH), {
                "failures": [],
                "label": LABEL,
                "ok": True,
                "slot": slot,
                "version": version,
            }, 0o644)
            return {
                "ok": True,
                "rolled_back": False,
                "slot": slot,
                "version": version,
                "previous": previous,
                "label": LABEL,
            }
        if previous:
            store.write_current(state, previous)
        else:
            current = store.path(state, store.CURRENT)
            if os.path.isfile(current):
                os.remove(current)
        record = {
            "failed_slot": slot,
            "failed_version": version,
            "failures": list(failures),
            "label": LABEL,
            "restored_slot": previous,
            "restored_version": read_version(state, previous) if previous else None,
        }
        store.write_json(store.path(state, store.ROLLBACK), record, 0o644)
        return {
            "ok": False,
            "rolled_back": True,
            "slot": previous,
            "version": record["restored_version"],
            "failed_version": version,
            "failures": list(failures),
            "label": LABEL,
        }


def demo_rollback():
    """Sign a good slot and a bad update with a throwaway key, then roll back.

    The private key lives only in a temporary directory. This is a desktop
    demo of the test harness, not a robot.
    """
    tmp = tempfile.mkdtemp(prefix="odm-demo-rollback-")
    try:
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
        state = os.path.join(tmp, "state")
        os.makedirs(state)
        seed_slot(state, "a", "1.0.0", "factory\n")
        good = os.path.join(tmp, "good.tar")
        bad = os.path.join(tmp, "bad.tar")
        build_bundle(good, "1.0.1", {
            "marker.txt": b"good\n",
            "slot_entry.py": PASSING_ENTRY,
        }, private)
        build_bundle(
            bad, "1.1.0", {
                "marker.txt": b"bad\n",
                "slot_entry.py": PASSING_ENTRY,
            }, private, health={"walk": "fail"},
        )
        # The seeded slot is the starting point. The bad bundle is the event.
        before_slot = store.read_current(state)
        before = read_version(state, before_slot)
        result = apply_update(bad, state, public)
        lines = [
            "Desktop demo, not the robot.",
            "measured in emulation",
            "slot before: %s version %s" % (before_slot, before),
            "apply 1.1.0 signature: ok",
            "self-test walk: fail",
            "rollback: current is %s version %s" % (result["slot"], result["version"]),
            "failures: %s" % ",".join(result["failures"]),
        ]
        # Confirm the good bundle would have moved the pointer, on a copy of the start.
        state_ok = os.path.join(tmp, "state-ok")
        os.makedirs(state_ok)
        seed_slot(state_ok, "a", "1.0.0", "factory\n")
        good_result = apply_update(good, state_ok, public)
        lines.append("good update landed on %s version %s" % (good_result["slot"], good_result["version"]))
        text = "\n".join(lines) + "\n"
        return {"text": text, "rollback": result, "good": good_result}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
