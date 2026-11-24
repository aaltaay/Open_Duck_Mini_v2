"""A pairing code made on this duck. There is no factory password.

The code is 8 characters from a 32-letter alphabet (set point). It is the
passphrase for the temporary setup network and the key for the home page.
The alphabet skips 0, O, 1, and I so a spoken code is easier to hear.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
LENGTH = 8
BANNED = frozenset({
    "raspberry", "password", "admin", "duck", "duckie",
    "12345678", "00000000", "aaaaaaaa",
})

_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 '\-]{0,23}$")


def generate_code():
    code = "".join(secrets.choice(ALPHABET) for _ in range(LENGTH))
    if code.lower() in BANNED:
        return generate_code()
    return code


def ssid_for(code):
    return "Duckie-" + code[:4]


def spell(code):
    return " ".join(code)


def spoken_line(ssid, code):
    return (
        "Hello. I am ready for setup. "
        "Join the Wi-Fi network %s. "
        "The pairing code is %s. "
        "Then open the setup page. "
        "There is no cloud account."
    ) % (ssid, spell(code))


def qr_escape(text):
    out = []
    for ch in str(text):
        if ch in "\\;,:\" ":
            out.append("\\")
        out.append(ch)
    return "".join(out)


def wifi_qr_payload(ssid, passphrase):
    """Text a phone camera reads as a WPA network. Set point, ZXing WIFI form."""
    return "WIFI:T:WPA;S:%s;P:%s;;" % (qr_escape(ssid), qr_escape(passphrase))


def new_salt():
    return secrets.token_hex(16)


def pairing_hash(salt_hex, code):
    raw = bytes.fromhex(salt_hex) + normalize_code(code).encode("ascii")
    return hashlib.sha256(raw).hexdigest()


def normalize_code(code):
    return "".join(str(code or "").split()).upper()


def pairing_ok(owner, code):
    if not owner or not code:
        return False
    try:
        got = pairing_hash(owner["pairing_salt"], code)
    except (KeyError, ValueError):
        return False
    stored = str(owner.get("pairing_sha256") or "")
    if len(got) != len(stored) or not stored:
        return False
    return hmac.compare_digest(got, stored)


def name_ok(name):
    return bool(_NAME.match(str(name or "").strip()))


def clean_name(name):
    return " ".join(str(name or "").split())
