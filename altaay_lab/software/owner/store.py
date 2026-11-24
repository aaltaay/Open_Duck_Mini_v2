"""State files for one duck. Tests pass a temporary directory.

On the Pi the directory is /var/lib/odm. The home Wi-Fi passphrase is not
stored next to the name, and the pairing code is kept only as a hash after
setup finishes.
"""

from __future__ import annotations

import json
import os

OWNER = "owner.json"
WIFI = "wifi.json"
PAIRING_PLAIN = "pairing_code.txt"
LOG_DIR = "logs"
LOG_NAME = "supervisor.jsonl"
CURRENT = "current"
ROLLBACK = "rollback.json"
HEALTH = "health.json"
SHUTDOWN = "shutdown.json"
SHUTDOWN_REQUEST = "shutdown.request"
VOICE = "voice_config.json"
SPOKEN = "spoken.txt"
SLOTS = "slots"


def ensure(state):
    os.makedirs(state, exist_ok=True)
    return state


def path(state, name):
    return os.path.join(state, name)


def write_text(file_path, text, mode=0o600):
    folder = os.path.dirname(file_path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    data = text.encode("utf-8")
    fd = os.open(file_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    os.chmod(file_path, mode)


def write_json(file_path, body, mode=0o600):
    write_text(file_path, json.dumps(body, indent=2, sort_keys=True) + "\n", mode)


def read_json(file_path):
    with open(file_path, encoding="utf-8") as handle:
        return json.load(handle)


def owner_path(state):
    return path(state, OWNER)


def load_owner(state):
    file_path = owner_path(state)
    if not os.path.isfile(file_path):
        return None
    return read_json(file_path)


def log_path(state):
    return path(state, os.path.join(LOG_DIR, LOG_NAME))


def slot_path(state, slot):
    if slot not in ("a", "b"):
        raise ValueError("slot")
    return path(state, os.path.join(SLOTS, slot))


def read_current(state):
    file_path = path(state, CURRENT)
    if not os.path.isfile(file_path):
        return None
    with open(file_path, encoding="utf-8") as handle:
        slot = handle.read().strip()
    if slot not in ("a", "b"):
        return None
    return slot


def runtime_dir(state):
    """Where a shutdown request lives. /run is empty after a reboot.

    The units set ODM_RUNTIME_DIR to /run/odm. Tests leave it unset and use
    a folder inside the temporary state, which a test can delete to act as
    a reboot.
    """
    override = os.environ.get("ODM_RUNTIME_DIR")
    if override:
        return override
    return os.path.join(state, "run")


def request_path(state):
    return os.path.join(runtime_dir(state), SHUTDOWN_REQUEST)


def write_current(state, slot):
    if slot not in ("a", "b"):
        raise ValueError("slot")
    write_text(path(state, CURRENT), slot + "\n", 0o644)


def hand_off(state):
    """Give the duck user the state dir. Leave Wi-Fi secrets with root.

    No-op unless ODM_OWNER_USER is set, which the setup unit sets on the Pi.
    """
    user = os.environ.get("ODM_OWNER_USER")
    if not user:
        return
    import pwd
    try:
        record = pwd.getpwnam(user)
    except KeyError:
        return
    os.chown(state, record.pw_uid, record.pw_gid)
    os.chmod(state, 0o755)
    for folder, dirs, files in os.walk(state):
        for name in dirs:
            os.chown(os.path.join(folder, name), record.pw_uid, record.pw_gid)
        for name in files:
            file_path = os.path.join(folder, name)
            if name in (WIFI, "home-wifi.conf") or "hostapd" in name or "dnsmasq" in name:
                continue
            try:
                os.chown(file_path, record.pw_uid, record.pw_gid)
            except OSError:
                pass
    secret = path(state, WIFI)
    if os.path.isfile(secret):
        try:
            os.chown(secret, 0, 0)
            os.chmod(secret, 0o600)
        except OSError:
            os.chmod(secret, 0o600)

