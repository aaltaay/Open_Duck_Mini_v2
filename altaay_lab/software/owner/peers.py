"""Who may open the setup page, and who may open the home page.

Setup answers only the temporary network (and loopback when a demo asks).
The home page answers RFC1918 and IPv6 unique-local addresses, and it refuses
the temporary setup subnet. Loopback is off unless the desktop demo asks.
"""

from __future__ import annotations

import ipaddress
import shutil
import subprocess

from .net import AP_ADDRESS

SETUP_NET = ipaddress.ip_network("192.168.4.0/24")
HOME_V4 = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
)


def _parse(ip):
    text = str(ip or "").split("%", 1)[0].strip()
    if text.startswith("::ffff:"):
        text = text.split("::ffff:", 1)[1]
    return ipaddress.ip_address(text)


def setup_peer_ok(ip, allow_loopback=False):
    try:
        addr = _parse(ip)
    except ValueError:
        return False
    if addr.is_loopback:
        return bool(allow_loopback)
    return addr in SETUP_NET


def status_peer_ok(ip, allow_loopback=False):
    try:
        addr = _parse(ip)
    except ValueError:
        return False
    if addr.is_loopback:
        return bool(allow_loopback)
    if addr.version == 4 and addr in SETUP_NET:
        return False
    if (
        addr.is_link_local
        or addr.is_multicast
        or addr.is_unspecified
        or addr.is_reserved
    ):
        return False
    if addr.version == 4:
        return any(addr in net for net in HOME_V4)
    return bool(addr.is_private)


def parse_ip_addr(text):
    """Lines from `ip -4 -o addr show`. Returns address strings."""
    found = []
    for line in str(text or "").splitlines():
        parts = line.split()
        if "inet" not in parts:
            continue
        idx = parts.index("inet")
        if idx + 1 >= len(parts):
            continue
        raw = parts[idx + 1].split("/", 1)[0]
        if raw not in found:
            found.append(raw)
    return found


def lan_ipv4_addrs():
    """Home-network IPv4 addresses. The setup subnet and loopback are skipped."""
    text = ""
    if shutil.which("ip"):
        try:
            text = subprocess.check_output(
                ["ip", "-4", "-o", "addr", "show"],
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            text = ""
    good = []
    for raw in parse_ip_addr(text):
        if status_peer_ok(raw, allow_loopback=False):
            good.append(raw)
    return good


def choose_status_bind(explicit, lan):
    if explicit:
        return explicit
    if not lan:
        return None
    addrs = lan_ipv4_addrs()
    return addrs[0] if addrs else None


# Kept so a reader can see the setup address next to the peer check.
SETUP_BIND = AP_ADDRESS
