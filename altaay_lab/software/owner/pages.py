"""HTML for the setup page and the home status page. No remote assets."""

from __future__ import annotations

from .pairing import spoken_line, wifi_qr_payload
from .privacy import PRIVACY, SENSOR_GAP
from .qr_card import qr_svg

DEMO_BANNER = "Desktop demo, not the robot."


def _esc(value):
    text = "" if value is None else str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _page(title, body, demo):
    banner = ""
    if demo:
        banner = '<p class="banner">%s</p>' % _esc(DEMO_BANNER)
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<style>
  :root { color-scheme: light; }
  body { margin: 0; background: #f4efe6; color: #1c1915;
    font: 18px/1.45 "Iowan Old Style", Palatino, Georgia, serif; }
  main { max-width: 40rem; margin: 0 auto; padding: 1.25rem 1.1rem 3rem; }
  h1 { font-size: 2rem; line-height: 1.15; margin: 0.2rem 0 0.6rem; }
  h2 { font-size: 1.15rem; margin: 1.4rem 0 0.4rem; }
  .banner { background: #e2a100; color: #1c1915; font-weight: 700;
    padding: 0.55rem 0.8rem; border-radius: 0.4rem; }
  .card { background: #fffdf8; border: 1px solid #e4dccb; border-radius: 0.6rem;
    padding: 0.8rem 1rem; margin: 0.7rem 0; }
  .num { font-size: 2rem; font-variant-numeric: tabular-nums; margin: 0.1rem 0; }
  label { display: block; margin: 0.7rem 0 0.2rem; font-weight: 700; }
  input[type=text], input[type=password], select {
    width: 100%%; box-sizing: border-box; font: inherit; padding: 0.45rem 0.5rem;
    border: 1px solid #b7ad9c; border-radius: 0.35rem; background: white; }
  button { font: inherit; background: #1c1915; color: #fffdf8; border: 0;
    border-radius: 0.4rem; padding: 0.55rem 1rem; margin-top: 1rem; cursor: pointer; }
  .quiet { color: #5c564c; font-size: 0.95rem; }
  .qr svg { width: 14rem; height: 14rem; background: white; }
  table { width: 100%%; border-collapse: collapse; }
  td, th { text-align: left; padding: 0.25rem 0.4rem 0.25rem 0; border-bottom: 1px solid #e4dccb; }
  .err { background: #f8e4d8; padding: 0.5rem 0.7rem; border-radius: 0.4rem; }
  a { color: #1c1915; }
</style>
</head>
<body>
<main>
%s
%s
</main>
</body>
</html>
""" % (_esc(title), banner, body)


def setup_page(ssid, code, error, demo, saved_name=""):
    payload = wifi_qr_payload(ssid, code)
    picture = qr_svg(payload)
    err = ""
    if error:
        err = '<p class="err">%s</p>' % _esc(error)
    body = """
<h1>Set up this duck</h1>
<p>No cloud account. The temporary network turns off when you save this page.</p>
<div class="card qr">%s</div>
<p>Network <strong>%s</strong></p>
<p>Pairing code <strong>%s</strong></p>
<p class="quiet">%s</p>
%s
<form method="post" action="/setup" autocomplete="off">
  <label for="pairing_code">Pairing code</label>
  <input id="pairing_code" name="pairing_code" type="text" autocapitalize="characters" required>
  <label for="name">Name</label>
  <input id="name" name="name" type="text" maxlength="24" value="%s" required>
  <label for="timezone">Timezone</label>
  <input id="timezone" name="timezone" type="text" list="zones" value="UTC" required>
  <datalist id="zones">
    <option value="UTC">
    <option value="America/New_York">
    <option value="America/Chicago">
    <option value="America/Denver">
    <option value="America/Los_Angeles">
    <option value="Europe/London">
    <option value="Europe/Paris">
    <option value="Asia/Tokyo">
    <option value="Australia/Sydney">
  </datalist>
  <label for="kid_mode">Who is this duck for?</label>
  <select id="kid_mode" name="kid_mode">
    <option value="kid" selected>Kid mode (mail and open questions stay off)</option>
    <option value="adult">Adult mode</option>
  </select>
  <label for="home_ssid">Home Wi-Fi name</label>
  <input id="home_ssid" name="home_ssid" type="text" required>
  <label for="home_passphrase">Home Wi-Fi passphrase</label>
  <input id="home_passphrase" name="home_passphrase" type="password" autocomplete="new-password">
  <label><input type="checkbox" name="home_open" value="yes"> This home network has no passphrase</label>
  <div class="card"><p>%s</p></div>
  <button type="submit">Save and join the home network</button>
</form>
<p class="quiet">The setup address on the duck is 192.168.4.1 (set point). This page does not ask for a cloud account.</p>
""" % (
        picture,
        _esc(ssid),
        _esc(code),
        _esc(spoken_line(ssid, code)),
        err,
        _esc(saved_name),
        _esc(PRIVACY),
    )
    return _page("Set up this duck", body, demo)


def setup_done_page(name, kid_mode, demo):
    who = "Kid mode is on." if kid_mode else "Adult mode is on. Mail still needs a key kept outside this duck."
    body = """
<h1>%s is set up</h1>
<p>The temporary network is closing. %s</p>
<p>On the home network, open port 8080 on this duck. That page answers only a device on the home network.</p>
<p>%s</p>
""" % (_esc(name), _esc(who), _esc(PRIVACY))
    return _page("Setup saved", body, demo)


def login_page(error, demo):
    err = '<p class="err">%s</p>' % _esc(error) if error else ""
    body = """
<h1>Duck status</h1>
<p>This page answers only a device on the home network. Use the pairing code from setup.</p>
%s
<form method="post" action="/login" autocomplete="off">
  <label for="pairing_code">Pairing code</label>
  <input id="pairing_code" name="pairing_code" type="password" required>
  <button type="submit">Show status</button>
</form>
""" % err
    return _page("Duck status", body, demo)


def _fmt(value):
    if value is None:
        return "No reading yet"
    if isinstance(value, float):
        return "%.2f" % value
    return str(value)


def status_page(owner, summary, demo):
    name = owner.get("name") or "Duck"
    kid = "On" if owner.get("kid_mode", True) else "Off"
    zone = owner.get("timezone") or "UTC"
    docks = summary.get("docks") or []
    rows = []
    if not docks:
        rows.append("<tr><td colspan=\"3\">No dock in the log yet</td></tr>")
    for row in docks:
        rows.append(
            "<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (_esc(row.get("t")), _esc(row.get("kind")), _esc(row.get("ok", "")))
        )
    note = SENSOR_GAP
    if demo:
        note = "Demo log, not a measurement. " + note
    body = """
<h1>%s</h1>
<p class="quiet">%s. Timezone %s. Kid mode %s.</p>
<p>%s</p>
<div class="card"><p class="quiet">Battery, pack volts</p><p class="num">%s</p></div>
<div class="card"><p class="quiet">Falls in the log</p><p class="num">%s</p></div>
<div class="card"><p class="quiet">Knee temperature, C</p><p class="num">%s</p></div>
<div class="card"><p class="quiet">Last mode</p><p class="num">%s</p></div>
<h2>Last docks</h2>
<table>
<tr><th>Time</th><th>Kind</th><th>Ok</th></tr>
%s
</table>
<p><a href="/logs">Download the supervisor log</a></p>
<p class="quiet">%s</p>
<p class="quiet">Port 8080 is a set point. No other page is opened by this service.</p>
""" % (
        _esc(name),
        _esc(PRIVACY),
        _esc(zone),
        _esc(kid),
        _esc(note),
        _esc(_fmt(summary.get("pack_v"))),
        _esc(_fmt(summary.get("falls"))),
        _esc(_fmt(summary.get("knee_c"))),
        _esc(summary.get("mode") or "No reading yet"),
        "".join(rows),
        _esc(note),
    )
    return _page(name, body, demo)
