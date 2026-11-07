"""Servo bus access with the Runtime's own libraries, plus error counting.

pypot (FeetechSTS3215IO) is opened exactly like Runtime scripts/check_voltage.py:
FeetechSTS3215IO(port, baudrate=1000000, use_sync_read=True). Registers that pypot's table
lacks (firmware 0 and 1, register 86) and multi-register blocks are read with pypot's own READ
and SYNC READ packet classes and send path, the code its getters run.

Ordering rule (important): rustypot opens the port with TIOCEXCL (serialport 4.7.0,
src/posix/tty.rs line 131), so any later open by a non-root user fails with EBUSY, and pypot's
open on Linux briefly reopens the port at 9600 baud (abstract_io.py _open). So a process that
needs both libraries opens pypot FIRST, then lets the Runtime HWI open rustypot, and never
reopens pypot while rustypot is in use.

Error counting:
  pypot: timeouts are counted on the instance's _real_read; bad packets are classified
  (checksum, length, header) by wrapping pypot's v1 DxlStatusPacket/DxlPacketHeader parsers,
  which raise ValueError on any of them (pypot/dynamixel/protocol/v1.py).
  rustypot: CountingIO wraps HWI.io and sorts the error text that rustypot returns
  ("Checksum error", "Parsing error", "Timeout error", "Operation timed out"), and a pyo3
  PanicException, which is what the flush-then-assert in rustypot's send_instruction_packet
  raises when bytes are still arriving (rustypot c8b8223 src/protocol/mod.rs lines 71 to 77).
"""
import os
import threading
import time
from collections import Counter

from . import sts3215

_ACTIVE = []          # error counters that receive pypot parse classifications
_PATCHED = False
_LOCK = threading.Lock()


class BusErrors:
    """Counts bus errors by library, kind and servo ID."""

    def __init__(self):
        self.kinds = Counter()
        self.by_id = Counter()
        self.events = []          # (time, library, kind, id, text), capped
        self.max_events = 2000

    def add(self, lib, kind, sid=None, text=""):
        with _LOCK:
            self.kinds[f"{lib}.{kind}"] += 1
            if sid is not None:
                self.by_id[(lib, kind, sid)] += 1
            if len(self.events) < self.max_events:
                self.events.append((time.time(), lib, kind, sid, str(text)[:200]))

    def reset(self):
        with _LOCK:
            self.kinds.clear(); self.by_id.clear(); self.events.clear()

    def count(self, pattern=""):
        return sum(v for k, v in self.kinds.items() if pattern in k)

    def checksum_errors(self):
        return self.count("checksum")

    def snapshot(self):
        return dict(self.kinds)


def _classify_packet(data):
    pkt = bytearray(data)
    if len(pkt) < 4 or pkt[0] != 0xFF or pkt[1] != 0xFF:
        return "header", None
    sid = pkt[2]
    if len(pkt) != 4 + pkt[3]:
        return "length", sid
    if (255 - (sum(pkt[2:-1]) % 256)) != pkt[-1]:
        return "checksum", sid
    return "parse", sid


def install_pypot_classifier(errors):
    """Route pypot packet parse failures into `errors` (process wide, idempotent)."""
    global _PATCHED
    from pypot.dynamixel.protocol import v1
    if errors not in _ACTIVE:
        _ACTIVE.append(errors)
    if _PATCHED:
        return
    orig_status = v1.DxlStatusPacket.from_string.__func__
    orig_header = v1.DxlPacketHeader.from_string.__func__

    def status_from_string(cls, data):
        try:
            return orig_status(cls, data)
        except ValueError:
            kind, sid = _classify_packet(data)
            for e in _ACTIVE:
                e.add("pypot", kind, sid, bytes(data).hex())
            raise

    def header_from_string(cls, data):
        try:
            return orig_header(cls, data)
        except ValueError:
            for e in _ACTIVE:
                e.add("pypot", "header", None, bytes(data).hex())
            raise

    v1.DxlStatusPacket.from_string = classmethod(status_from_string)
    v1.DxlPacketHeader.from_string = classmethod(header_from_string)
    _PATCHED = True


def make_flush_safe(io):
    """pypot flushes input AND output before every packet (abstract_io.py __real_send -> flush ->
    flushInput + flushOutput). Output flush = TCOFLUSH, which on the Pi's cdc-acm driver unlinks
    write URBs still in flight (linux rpi-6.12.y drivers/usb/class/cdc-acm.c lines 893 to 904,
    acm_tty_flush_buffer), and on a pty drops bytes not yet read. A sync write (no reply) sent just
    before, by rustypot or by pypot itself, can then be lost. This instance-level replacement waits
    for the output to drain (tcdrain) and flushes only the input. pypot's files are not changed."""
    import termios

    def safe_flush(_force_lock=False):
        s = io._serial
        try:
            termios.tcdrain(s.fd)
        except (termios.error, OSError, AttributeError):
            pass
        s.reset_input_buffer()
    io.flush = safe_flush
    return io


def open_pypot(port, sync_read=True, errors=None, timeout=None):
    """FeetechSTS3215IO(port, baudrate=1000000, use_sync_read=...) as check_voltage.py does,
    with the safe flush above. Timeout: pypot's default 0.05 s; ODM_PYPOT_TIMEOUT overrides it
    (the tests use a longer one because the test machine is shared and the bus is simulated)."""
    from pypot.feetech import FeetechSTS3215IO
    from pypot.dynamixel.io.abstract_io import DxlTimeoutError
    if timeout is None:
        timeout = float(os.environ.get("ODM_PYPOT_TIMEOUT", "0.05"))
    io = FeetechSTS3215IO(port, baudrate=1000000, use_sync_read=sync_read, timeout=timeout)
    make_flush_safe(io)
    if errors is not None:
        install_pypot_classifier(errors)
        orig = io._real_read

        def counted_real_read(instruction_packet, _force_lock=False):
            try:
                return orig(instruction_packet, _force_lock=_force_lock)
            except DxlTimeoutError as e:
                errors.add("pypot", "timeout", None, str(e))
                raise
        io._real_read = counted_real_read
    return io


def read_block(io, sid, addr, length):
    """One READ (instruction 0x02) of `length` bytes at `addr`, via pypot's packet and send path."""
    rp = io._protocol.DxlReadDataPacket(sid, addr, length)
    sp = io._send_packet(rp)
    data = bytes(sp.parameters)
    if len(data) != length:
        raise IOError(f"servo {sid}: asked {length} bytes at {addr}, got {len(data)}")
    return data


def write_block(io, sid, addr, data):
    """One WRITE (instruction 0x03) of the bytes `data` at `addr`, via pypot's packet and send path (the way its
    setters write: _send_packet(..., wait_for_status_packet=False), abstract_io.py line 471). Read the registers back
    to check: a write is not confirmed by itself."""
    wp = io._protocol.DxlWriteDataPacket(sid, addr, list(bytes(data)))
    io._send_packet(wp, wait_for_status_packet=False)


def read_reg(io, sid, name):
    addr, size = sts3215.REG[name]
    return sts3215.le(read_block(io, sid, addr, size), 0, size)


def sync_read_block(io, ids, addr, length, errors=None, info=None):
    """One SYNC READ (0x82) of `length` bytes at `addr` from every ID, kept per ID.

    Same packet and read loop as FeetechSTS3215IO._get_control_value (sts3215_io.py lines 20
    to 41), but it keys each answer by the ID in its status packet and keeps the answers that
    arrived when one servo fails, instead of returning an empty tuple.
    info (dict): also note info["t_req"], the clock time just after the request was handed to the
    port. For that the send is done here with the steps of pypot's __real_send (abstract_io.py:
    flush, write, check the byte count, read the first status packet); without info, pypot's
    _send_packet is called as before.
    The read always runs to its end (every reply, or pypot's own timeout): a read cut short would
    leave its late replies on the bus, and rustypot's next send panics on them (G10; seen on the
    simulated bus under load when the idle-time sampler cut reads at the end of the sleep).
    Returns (dict id -> bytes, list of failed ids).
    """
    from pypot.dynamixel.io.abstract_io import DxlCommunicationError
    rp = io._protocol.DxlSyncReadPacket(list(ids), addr, length)
    got, packets = {}, []
    with io._serial_lock:
        try:
            if info is None:
                packets.append(io._send_packet(rp, _force_lock=True))
            else:
                io.flush(_force_lock=True)
                data = rp.to_string()
                n = io._serial.write(data)
                info["t_req"] = time.monotonic()
                if n != len(data):
                    raise DxlCommunicationError(io, "instruction packet not entirely sent", rp)
                packets.append(io._real_read(rp, _force_lock=True))
            for _ in range(len(ids) - 1):
                packets.append(io._real_read(rp, _force_lock=True))
        except DxlCommunicationError as e:
            if errors is not None:
                errors.add("pypot", "sync_read_incomplete", None, str(e))
    for sp in packets:
        if len(sp.parameters) == length:
            got[sp.id] = bytes(sp.parameters)
    failed = [i for i in ids if i not in got]
    if failed:
        # flush whatever may still be in flight so the next transaction (maybe rustypot's) starts clean
        time.sleep(0.002)
        try:
            io.flush()
        except Exception:
            pass
    return got, failed


def ping(io, sid):
    from pypot.dynamixel.io.abstract_io import DxlCommunicationError
    try:
        return io.ping(sid)
    except DxlCommunicationError:
        return False


def scan(io, ids=range(254)):
    return [i for i in ids if ping(io, i)]


def classify_rustypot_error(exc):
    name = type(exc).__name__
    text = str(exc)
    if name == "PanicException":
        return "panic"
    if "Checksum" in text:
        return "checksum"
    if "timed out" in text or "Timeout" in text:
        return "timeout"
    if "Parsing" in text:
        return "parse"
    if "Incorrect id" in text:
        return "wrong_id"
    return "other"


class CountingIO:
    """Wraps the HWI's rustypot IO object: same calls, plus error counting.

    Exceptions are counted and re-raised unchanged, so the Runtime behaves as without it.
    """

    def __init__(self, io, errors, on_panic=None):
        self._io = io
        self._errors = errors
        self._on_panic = on_panic
        self.calls = Counter()
        self.panicked = False

    def __getattr__(self, name):
        attr = getattr(self._io, name)
        if not callable(attr):
            return attr

        def wrapped(*args, **kwargs):
            self.calls[name] += 1
            try:
                return attr(*args, **kwargs)
            except BaseException as e:      # includes pyo3 PanicException (a BaseException)
                if isinstance(e, (KeyboardInterrupt, SystemExit)):
                    raise
                kind = classify_rustypot_error(e)
                self._errors.add("rustypot", kind, None, f"{name}: {e}")
                if kind == "panic":
                    self.panicked = True
                    if self._on_panic:
                        self._on_panic(e)
                raise
        return wrapped
