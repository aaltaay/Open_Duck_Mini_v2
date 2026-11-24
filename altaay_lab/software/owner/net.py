"""Temporary setup network and the home Wi-Fi join.

The passphrase is written into a root-only file. It is not placed on a
command line. Tests use MockNet and never start a radio.

Addresses and the Wi-Fi channel are set points, not measurements.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess

from .pairing import BANNED
from .store import write_text

# Set points for the temporary network. Not a measurement of a room.
AP_ADDRESS = "192.168.4.1"
AP_CIDR = "192.168.4.1/24"
AP_DHCP_FROM = "192.168.4.10"
AP_DHCP_TO = "192.168.4.50"
AP_CHANNEL = 6
AP_INTERFACE = "wlan0"
SETUP_PORT = 80
STATUS_PORT = 8080


class NetError(RuntimeError):
    pass


def check_passphrase(passphrase):
    text = str(passphrase or "")
    if len(text) < 8 or len(text) > 63:
        raise NetError("the setup passphrase must be 8 to 63 characters")
    if any(ch in text for ch in "\n\r\x00"):
        raise NetError("the setup passphrase has a broken character")
    if text.lower() in BANNED:
        raise NetError("that passphrase is a factory default and is refused")
    return text


def clean_ssid(ssid):
    text = " ".join(str(ssid or "").split())
    if not text or len(text) > 32:
        raise NetError("the network name must be 1 to 32 characters")
    if any(ch in text for ch in "\n\r\"\\"):
        raise NetError("the network name cannot contain a quote")
    return text


def hostapd_conf(ssid, passphrase, interface=AP_INTERFACE, channel=AP_CHANNEL):
    ssid = clean_ssid(ssid)
    passphrase = check_passphrase(passphrase)
    lines = [
        "interface=%s" % interface,
        "ssid=%s" % ssid,
        "hw_mode=g",
        "channel=%d" % int(channel),
        "wpa=2",
        "wpa_passphrase=%s" % passphrase,
        "wpa_key_mgmt=WPA-PSK",
        "rsn_pairwise=CCMP",
        "",
    ]
    return "\n".join(lines)


def dnsmasq_conf(interface=AP_INTERFACE):
    # Captive DNS is only on the setup interface, and only while setup runs.
    return "\n".join([
        "interface=%s" % interface,
        "bind-interfaces",
        "dhcp-range=%s,%s,255.255.255.0,2h" % (AP_DHCP_FROM, AP_DHCP_TO),
        "address=/#/%s" % AP_ADDRESS,
        "",
    ])


def ap_commands(hostapd_conf_path, dns_conf_path, hostapd_pid, dns_pid, interface=AP_INTERFACE):
    """Argv lists. The passphrase stays in the hostapd file, not in argv."""
    return [
        ["ip", "addr", "replace", AP_CIDR, "dev", interface],
        ["hostapd", "-B", "-P", hostapd_pid, hostapd_conf_path],
        ["dnsmasq", "--conf-file=%s" % dns_conf_path, "--pid-file=%s" % dns_pid],
    ]


def stop_pidfile(pid_path):
    """Stop the process that wrote this pid file. Missing file is fine."""
    if not os.path.isfile(pid_path):
        return
    with open(pid_path, encoding="utf-8") as handle:
        text = handle.read().strip()
    if not text.isdigit():
        return
    try:
        os.kill(int(text), signal.SIGTERM)
    except OSError:
        return


def wifi_supplicant_conf(ssid, passphrase, open_net):
    ssid = clean_ssid(ssid)
    if open_net:
        body = 'network={\n  ssid="%s"\n  key_mgmt=NONE\n}\n' % ssid
    else:
        secret = check_passphrase(passphrase)
        body = 'network={\n  ssid="%s"\n  psk="%s"\n}\n' % (ssid, secret)
    # Commands name the file. They do not carry the passphrase.
    return body


class MockNet:
    """Records what a live network would do. Starts nothing."""

    def __init__(self):
        self.events = []
        self.ap_up = False

    def start_ap(self, ssid, passphrase, address):
        check_passphrase(passphrase)
        clean_ssid(ssid)
        self.events.append({
            "op": "start_ap",
            "ssid": ssid,
            "address": address,
            "passphrase_len": len(passphrase),
        })
        self.ap_up = True

    def stop_ap(self):
        self.events.append({"op": "stop_ap"})
        self.ap_up = False

    def join_wifi(self, ssid, passphrase, open_net):
        clean_ssid(ssid)
        if not open_net:
            check_passphrase(passphrase)
        self.events.append({
            "op": "join_wifi",
            "ssid": ssid,
            "open": bool(open_net),
            "has_pass": bool(passphrase) and not open_net,
        })

    def speak(self, text):
        self.events.append({"op": "speak", "text": text})

    def set_timezone(self, name):
        self.events.append({"op": "timezone", "name": name})

    def set_hostname(self, name):
        self.events.append({"op": "hostname", "name": name})


class LiveNet:
    """Bookworm path. hostapd and dnsmasq, files mode 0600, no passphrase argv.

    Not used by tests. Never done on hardware.
    """

    def __init__(self, state, runner=None):
        self.state = state
        self.runner = runner or _run
        self.ap_up = False

    def start_ap(self, ssid, passphrase, address):
        if address != AP_ADDRESS:
            raise NetError("the setup address is fixed")
        os.makedirs(self.state, exist_ok=True)
        hostapd = os.path.join(self.state, "hostapd-setup.conf")
        dns = os.path.join(self.state, "dnsmasq-setup.conf")
        hostapd_pid = os.path.join(self.state, "hostapd-setup.pid")
        dns_pid = os.path.join(self.state, "dnsmasq-setup.pid")
        write_text(hostapd, hostapd_conf(ssid, passphrase), 0o600)
        write_text(dns, dnsmasq_conf(), 0o600)
        if not shutil.which("hostapd"):
            raise NetError("hostapd is not installed")
        for cmd in ap_commands(hostapd, dns, hostapd_pid, dns_pid):
            if cmd[0] == "ip" and not shutil.which("ip"):
                continue
            if cmd[0] == "dnsmasq" and not shutil.which("dnsmasq"):
                continue
            self.runner(cmd)
        self.ap_up = True

    def stop_ap(self):
        stop_pidfile(os.path.join(self.state, "hostapd-setup.pid"))
        stop_pidfile(os.path.join(self.state, "dnsmasq-setup.pid"))
        self.ap_up = False

    def join_wifi(self, ssid, passphrase, open_net):
        conf = os.path.join(self.state, "home-wifi.conf")
        write_text(conf, wifi_supplicant_conf(ssid, passphrase, open_net), 0o600)
        if shutil.which("wpa_supplicant"):
            self.runner([
                "wpa_supplicant", "-B", "-i", AP_INTERFACE, "-c", conf,
            ])

    def speak(self, text):
        spoken = os.path.join(self.state, "spoken.txt")
        write_text(spoken, text + "\n", 0o600)
        if shutil.which("espeak-ng"):
            # The text is the pairing sentence. It is not the home passphrase.
            self.runner(["espeak-ng", "-s", "140", text])

    def set_timezone(self, name):
        if shutil.which("timedatectl"):
            self.runner(["timedatectl", "set-timezone", name])

    def set_hostname(self, name):
        if shutil.which("hostnamectl"):
            self.runner(["hostnamectl", "set-hostname", name])


def _run(cmd):
    subprocess.run(cmd, check=False, timeout=30)
