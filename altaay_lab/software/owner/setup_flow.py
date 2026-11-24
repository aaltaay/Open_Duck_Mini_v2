"""First-boot answers: name, timezone, kid mode, home Wi-Fi, pairing code.

No cloud account field is accepted. Kid mode stays on unless the form says adult.
"""

from __future__ import annotations

import os
import re

from . import store
from .net import NetError, clean_ssid
from .pairing import (
    clean_name,
    generate_code,
    name_ok,
    new_salt,
    normalize_code,
    pairing_hash,
    pairing_ok,
    spoken_line,
    ssid_for,
)
from .privacy import PRIVACY

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None

BANNED_FIELDS = frozenset({
    "cloud", "cloud_account", "account", "email", "token", "password",
    "api_key", "secret", "credential",
})
FAIL_WINDOW_S = 60
FAIL_LIMIT = 8


class SetupError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


class AlreadySetup(SetupError):
    def __init__(self):
        super().__init__("this duck is already set up", 409)


def timezone_ok(name):
    text = str(name or "").strip()
    if not text or len(text) > 64 or "\n" in text or ".." in text:
        return False
    if text != "UTC" and "/" not in text:
        return False
    if ZoneInfo is None:
        return bool(re.match(r"^[A-Za-z0-9_+-]+(/[A-Za-z0-9_+-]+)*$", text))
    try:
        ZoneInfo(text)
    except Exception:
        return False
    return True


def hostname_for(name):
    slug = re.sub(r"[^a-z0-9]+", "-", clean_name(name).lower()).strip("-")
    return (slug or "duckie")[:24]


def kid_from_form(value):
    """Only the exact word adult turns kid mode off."""
    return str(value or "").strip().lower() != "adult"


class SetupSession:
    def __init__(self, state, net, clock=None):
        self.state = state
        self.net = net
        self.clock = clock or __import__("time").time
        self.code = None
        self.ssid = None
        self.fails = []
        self.done = False

    def begin(self):
        store.ensure(self.state)
        if store.load_owner(self.state):
            raise AlreadySetup()
        self.code = generate_code()
        self.ssid = ssid_for(self.code)
        store.write_text(
            store.path(self.state, store.PAIRING_PLAIN),
            self.code + "\n",
            0o600,
        )
        line = spoken_line(self.ssid, self.code)
        self.net.speak(line)
        from .net import AP_ADDRESS
        self.net.start_ap(self.ssid, self.code, AP_ADDRESS)
        return self.code

    def limited(self, now=None):
        now = self.clock() if now is None else now
        self.fails = [t for t in self.fails if now - t < FAIL_WINDOW_S]
        return len(self.fails) >= FAIL_LIMIT

    def note_fail(self, now=None):
        now = self.clock() if now is None else now
        self.fails.append(now)
        return self.limited(now)

    def submit(self, form):
        if self.done or store.load_owner(self.state):
            raise AlreadySetup()
        if self.code is None:
            raise SetupError("setup has not started", 409)
        keys = {str(k) for k in form.keys()}
        banned = sorted(keys & BANNED_FIELDS)
        if banned:
            raise SetupError("this page does not take a cloud account", 400)
        if self.limited():
            raise SetupError("too many tries. Wait a minute and listen for the code again.", 429)
        given = normalize_code(form.get("pairing_code", ""))
        if not pairing_ok(_preview_owner(self.state, self.code), given):
            self.note_fail()
            raise SetupError("that pairing code does not match", 403)
        name = clean_name(form.get("name", ""))
        if not name_ok(name):
            raise SetupError("use a short name: letters, numbers, spaces, or a hyphen", 400)
        zone = str(form.get("timezone", "")).strip()
        if not timezone_ok(zone):
            raise SetupError("that timezone is not a known zone name", 400)
        kid = kid_from_form(form.get("kid_mode"))
        try:
            ssid = clean_ssid(form.get("home_ssid", ""))
        except NetError as exc:
            raise SetupError(str(exc), 400) from exc
        open_net = str(form.get("home_open", "")).lower() in ("yes", "on", "true", "1")
        passphrase = str(form.get("home_passphrase") or "")
        if not open_net:
            if any(ch in passphrase for ch in "\n\r"):
                raise SetupError("the home passphrase has a broken character", 400)
            if not 8 <= len(passphrase) <= 63:
                raise SetupError(
                    "the home passphrase must be 8 to 63 characters, or mark the network as open",
                    400,
                )
        else:
            passphrase = ""
        salt = new_salt()
        owner = {
            "kid_mode": kid,
            "name": name,
            "pairing_salt": salt,
            "pairing_sha256": pairing_hash(salt, self.code),
            "setup_complete": True,
            "timezone": zone,
            "version": 1,
        }
        wifi = {"open": open_net, "ssid": ssid}
        if passphrase:
            wifi["passphrase"] = passphrase
        store.write_json(store.owner_path(self.state), owner, 0o644)
        store.write_json(store.path(self.state, store.WIFI), wifi, 0o600)
        plain = store.path(self.state, store.PAIRING_PLAIN)
        if os.path.isfile(plain):
            os.remove(plain)
        self._write_voice(kid)
        self.net.set_timezone(zone)
        self.net.set_hostname(hostname_for(name))
        self.net.join_wifi(ssid, passphrase, open_net)
        self.net.stop_ap()
        self.net.speak("Setup is finished. The temporary network is off. " + PRIVACY)
        self.done = True
        self.code = None
        store.hand_off(self.state)
        return owner

    def _write_voice(self, kid):
        from altaay_lab.software.companion.config import DEFAULTS
        cfg = dict(DEFAULTS)
        cfg["mode"] = "kid" if kid else "adult"
        cfg["cloud"] = "off"
        store.write_json(store.path(self.state, store.VOICE), cfg, 0o644)


def _preview_owner(state, code):
    """Hash check against the live code, using a throwaway salt in memory.

    submit() compares the typed code to the code this process spoke. The
    stored hash is written only after the rest of the form is valid.
    """
    del state
    salt = "00" * 16
    return {"pairing_salt": salt, "pairing_sha256": pairing_hash(salt, code)}
