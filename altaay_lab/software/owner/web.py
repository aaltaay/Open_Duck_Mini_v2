"""Local HTTP for setup and for the home status page.

Neither server is bound to every interface by this module's CLI. The peer
check runs before any page body is built.
"""

from __future__ import annotations

import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from . import pages, status_data, store
from .pairing import pairing_ok
from .peers import setup_peer_ok, status_peer_ok
from .setup_flow import SetupError


class _Handler(BaseHTTPRequestHandler):
    server_version = "odm"
    sys_version = ""
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        # Status only. The path is not written, so a passphrase cannot land in the log line.
        code = args[1] if len(args) > 1 else ""
        try:
            code = str(code)
        except Exception:
            code = ""
        if code:
            return


def _send(handler, status, body, content_type="text/html; charset=utf-8", extra=None):
    data = body.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.send_header("Referrer-Policy", "no-referrer")
    for key, value in extra or []:
        handler.send_header(key, value)
    handler.end_headers()
    handler.wfile.write(data)


def _form(handler):
    length = int(handler.headers.get("Content-Length", "0") or "0")
    if length < 0 or length > 10000:
        return None
    raw = handler.rfile.read(length).decode("utf-8", errors="replace")
    parsed = parse_qs(raw, keep_blank_values=True)
    return {key: values[0] if values else "" for key, values in parsed.items()}


class SetupHandler(_Handler):
    def do_GET(self):
        self._route("GET")

    def do_POST(self):
        self._route("POST")

    def _route(self, method):
        peer = self.client_address[0]
        if not setup_peer_ok(peer, self.server.allow_loopback):
            _send(self, 403, "This page is only for the temporary setup network.\n", "text/plain; charset=utf-8")
            return
        path = self.path.split("?", 1)[0]
        if path in ("/generate_204", "/hotspot-detect.html", "/ncsi.txt", "/connecttest.txt"):
            self.send_response(302)
            self.send_header("Location", "/")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if method == "GET" and path in ("/", "/setup"):
            session = self.server.session
            if session.code is None and not session.done:
                try:
                    session.begin()
                except SetupError as exc:
                    _send(self, exc.status, pages.setup_done_page("This duck", True, self.server.demo))
                    return
            page = pages.setup_page(session.ssid, session.code, "", self.server.demo)
            _send(self, 200, page)
            return
        if method == "POST" and path == "/setup":
            form = _form(self)
            if form is None:
                _send(self, 400, "The form was too large.\n", "text/plain; charset=utf-8")
                return
            session = self.server.session
            try:
                owner = session.submit(form)
            except SetupError as exc:
                if session.code:
                    page = pages.setup_page(session.ssid, session.code, str(exc), self.server.demo, form.get("name", ""))
                else:
                    page = "<p>%s</p>" % pages._esc(str(exc))
                _send(self, exc.status, page)
                return
            _send(self, 200, pages.setup_done_page(owner["name"], owner["kid_mode"], self.server.demo))
            threading.Thread(target=_shutdown_soon, args=(self.server,), daemon=True).start()
            return
        _send(self, 404, "Not found.\n", "text/plain; charset=utf-8")


def _shutdown_soon(httpd):
    time.sleep(0.2)
    httpd.shutdown()


class StatusHandler(_Handler):
    def do_GET(self):
        self._route("GET")

    def do_POST(self):
        self._route("POST")

    def _route(self, method):
        peer = self.client_address[0]
        if not status_peer_ok(peer, self.server.allow_loopback):
            _send(
                self,
                403,
                "This page only answers a device on the home network.\n",
                "text/plain; charset=utf-8",
            )
            return
        path = self.path.split("?", 1)[0]
        owner = store.load_owner(self.server.state)
        if owner is None:
            _send(self, 403, "Setup is not finished.\n", "text/plain; charset=utf-8")
            return
        token = _cookie(self).get("odm_session", "")
        signed_in = token in self.server.sessions
        if method == "POST" and path == "/login":
            form = _form(self)
            if form is None:
                _send(self, 400, "The form was too large.\n", "text/plain; charset=utf-8")
                return
            if not pairing_ok(owner, form.get("pairing_code", "")):
                page = pages.login_page("That pairing code does not match.", self.server.demo)
                _send(self, 403, page)
                return
            import secrets
            issued = secrets.token_urlsafe(32)
            self.server.sessions.add(issued)
            page = _status_body(self)
            _send(self, 200, page, extra=[
                ("Set-Cookie", "odm_session=%s; HttpOnly; SameSite=Strict; Path=/" % issued),
            ])
            return
        if not signed_in:
            _send(self, 200 if method == "GET" else 401, pages.login_page("", self.server.demo))
            return
        if method == "GET" and path in ("/", "/status"):
            _send(self, 200, _status_body(self))
            return
        if method == "GET" and path == "/logs":
            text, _trimmed = status_data.log_download(self.server.state)
            _send(
                self,
                200,
                text,
                "text/plain; charset=utf-8",
                extra=[("Content-Disposition", 'attachment; filename="supervisor.jsonl"')],
            )
            return
        _send(self, 404, "Not found.\n", "text/plain; charset=utf-8")


def _status_body(handler):
    owner = store.load_owner(handler.server.state)
    summary = status_data.status_summary(handler.server.state)
    return pages.status_page(owner, summary, handler.server.demo)


def _cookie(handler):
    out = {}
    header = handler.headers.get("Cookie", "")
    for part in header.split(";"):
        if "=" not in part:
            continue
        key, value = part.strip().split("=", 1)
        out[key] = value
    return out


class _Server(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def serve_setup(session, host, port, allow_loopback, demo):
    httpd = _Server((host, port), SetupHandler)
    httpd.session = session
    httpd.allow_loopback = allow_loopback
    httpd.demo = demo
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    httpd.thread = thread
    return httpd


def serve_status(state, host, port, allow_loopback, demo):
    httpd = _Server((host, port), StatusHandler)
    httpd.state = state
    httpd.allow_loopback = allow_loopback
    httpd.demo = demo
    httpd.sessions = set()
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    httpd.thread = thread
    return httpd
