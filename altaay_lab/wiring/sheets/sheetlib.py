"""sheetlib: drawing library for the per-subsystem wiring sheets (used by make_sheets.py).

Every sheet is drawn in millimetres on an A3 landscape page (420 x 297 mm) with the y axis pointing down.
Rules this library enforces, so a sheet cannot drift away from wiring/netlist.yaml:
  - a wire is looked up in the netlist by its two end pins; an unknown pair stops the run;
  - the wire is drawn from the terminal of one pin to the terminal of the other pin as placed on the sheet;
  - its label (cable id, branch, gauge, cut length, colour code) is built from the netlist row;
  - every segment is horizontal or vertical (a diagonal stops the run);
  - crossings get a hop arc and are counted; labels on other wires, wires through blocks and
    collinear overlaps are reported as layout warnings.
Nothing here holds wiring data: the data is in netlist.yaml, the placement is in make_sheets.py.
"""
import os
import math
import hashlib
import subprocess
import collections

import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle, Polygon
from matplotlib.lines import Line2D
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextToPath

FONT = "Carlito"
plt.rcParams.update({
    "svg.fonttype": "path",            # glyphs as paths: the SVG looks the same on any phone or browser
    "svg.hashsalt": "odm-wiring-sheets",
    "font.family": FONT,
    "path.simplify": False,
})

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.normpath(os.path.join(HERE, "..", ".."))
NETLIST_PATH = os.environ.get("ODM_NETLIST", os.path.join(LAB, "wiring", "netlist.yaml"))
PT = 25.4 / 72.0                       # mm per point
W, H = 420.0, 297.0                    # A3 landscape
FR = 10.0                              # frame inset (zone labels live in the 10 mm margin)
COLS, ROWS = 8, "ABCDEF"

INK, GREY, LIGHT, FAINT = "#1f2a33", "#5f6b75", "#9aa5ad", "#d5dbe0"
LS = 7.4                               # wire label size (pt)
TS = 8.2                               # terminal name size (pt)

# insulation colours (netlist "color" field) and IEC 60757 codes
WIRE_RGB = {"red": "#d62828", "black": "#1b1b1b", "yellow": "#f5c518", "white": "#ffffff", "green": "#23964a",
            "blue": "#1f6fd1", "orange": "#f28c00", "brown": "#7a4b2a", "kit": "#a9a9a9", "holder lead": "#a9a9a9",
            "black jacket": "#2b2b2b", "white ribbon": "#ffffff", "none": "#9a9a9a",
            "lane_p": "#c62828", "lane_d": "#1f6fd1", "lane_s": "#2e7d32"}
CODE = {"red": "RD", "black": "BK", "yellow": "YE", "white": "WH", "green": "GN", "blue": "BU", "orange": "OG",
        "brown": "BN", "kit": "", "holder lead": "", "black jacket": "BK", "white ribbon": "", "none": "bare",
        "lane_p": "", "lane_d": "", "lane_s": ""}
UNSET = {"kit", "holder lead"}         # colour not set by the netlist: drawn grey with white dashes
BRANCH = {"line": "line", "load": "load", "lead1": "lead 1", "lead2": "lead 2", "tail": "tail", "stem": "stem",
          "a": "a", "b": "b", "pullup": "pull-up", "jumper": "jumper", "joint": "joint"}

PI_NAMES = {1: "3V3", 2: "5V", 3: "GPIO2", 4: "5V", 5: "GPIO3", 6: "GND", 7: "GPIO4", 8: "GPIO14", 9: "GND",
            10: "GPIO15", 11: "GPIO17", 12: "GPIO18", 13: "GPIO27", 14: "GND", 15: "GPIO22", 16: "GPIO23", 17: "3V3",
            18: "GPIO24", 19: "GPIO10", 20: "GND", 21: "GPIO9", 22: "GPIO25", 23: "GPIO11", 24: "GPIO8", 25: "GND",
            26: "GPIO7", 27: "GPIO0", 28: "GPIO1", 29: "GPIO5", 30: "GND", 31: "GPIO6", 32: "GPIO12", 33: "GPIO13",
            34: "GND", 35: "GPIO19", 36: "GPIO16", 37: "GPIO26", 38: "GPIO20", 39: "GND", 40: "GPIO21"}  # pinout.xyz


def ny_date():
    """Date and time from `TZ=America/New_York date`, as the brief asks."""
    env = dict(os.environ, TZ="America/New_York")
    return subprocess.run(["date", "+%Y-%m-%d %H:%M %Z"], env=env, capture_output=True, text=True,
                          check=True).stdout.strip()


# ------------------------------------------------------------------ netlist
class Netlist:
    def __init__(self, path=NETLIST_PATH):
        raw = open(path, "rb").read()
        self.path = path
        self.sha = hashlib.sha256(raw).hexdigest()[:12]
        d = yaml.safe_load(raw)
        self.meta = d["meta"]
        self.rev = str(d["meta"]["rev"])
        self.comps = {c["id"]: c for c in d["components"]}
        self.pins = {f'{c["id"]}.{p["pin"]}': (c, p) for c in d["components"] for p in c["pins"]}
        self.cables = {c["id"]: c for c in d["cables"]}
        self.active = [c["id"] for c in d["cables"] if c["status"] == "active"]
        self.wires = []
        self.by_ends = {}
        for i, w in enumerate(d["wires"]):
            w = dict(w)
            w["n"] = i + 1                                   # row number in the netlist wires list
            self.wires.append(w)
            key = frozenset((w["from"], w["to"]))
            if key in self.by_ends:
                raise SystemExit(f"netlist: two wires join {w['from']} and {w['to']}")
            self.by_ends[key] = w
        self.active_wires = [w for w in self.wires if w["cable"] in self.active]

    def wire(self, a, b):
        w = self.by_ends.get(frozenset((a, b)))
        if w is None:
            raise SystemExit(f"no wire between {a} and {b} in netlist.yaml")
        if w["cable"] not in self.active:
            raise SystemExit(f"wire {a} - {b} is on removed cable {w['cable']}")
        return w

    def pin(self, ref):
        if ref not in self.pins:
            raise SystemExit(f"{ref} is not a pin in netlist.yaml")
        return self.pins[ref][1]

    def comp(self, cid):
        return self.comps[cid]

    def joint_of(self, cid):
        """Joint name of a servo from its netlist source text, e.g. '[U] left_hip_yaw ...'."""
        src = self.comps[cid]["source"]
        tok = src.split("[U]")[1].strip().split()[0].strip(",;")
        return tok


# ------------------------------------------------------------------ text metrics
_TTP = TextToPath()
_FP = {}


def fprop(size, bold=False):
    k = (size, bold)
    if k not in _FP:
        _FP[k] = FontProperties(family=FONT, size=size, weight="bold" if bold else "normal")
    return _FP[k]


def tw(s, size, bold=False):
    """Width of a text in mm."""
    if not s:
        return 0.0
    w, _, _ = _TTP.get_text_width_height_descent(s.replace(" ", " "), fprop(size, bold), ismath=False)
    return w * PT


def th(size):
    return size * PT * 0.95


def lum(hexcol):
    r, g, b = (int(hexcol[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def darker(hexcol, f=0.62):
    r, g, b = (int(hexcol[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % (int(r * f), int(g * f), int(b * f))


# ------------------------------------------------------------------ wire appearance and labels
def core_lw(gauge):
    g = str(gauge)
    for k, v in (("harness", 2.4), ("16 AWG", 2.7), ("20 AWG", 2.2), ("22 AWG", 1.9), ("26 AWG", 1.5), ("kit cable", 1.7),
                 ("BEC lead", 2.2), ("SG90 lead", 1.5), ("USB", 3.0), ("FPC", 4.6), ("resistor lead", 0.9)):
        if g.startswith(k):
            return v
    return 1.5


def cut_txt(w):
    c = w["cut_mm"]
    if c is None:
        return "as shipped"
    if c == 0:
        return "0 mm, soldered direct"
    return f"{int(c)} mm"


def label_parts(w):
    head = w["cable"] + (" " + BRANCH[w["branch"]] if w.get("branch") else "")
    g = "kit" if w["gauge"] == "kit cable" else w["gauge"]
    body = f"{g}  {cut_txt(w)}"
    code = CODE[w["color"]]
    if code:
        body += f"  {code}"
    return head, body


def label_size(w):
    head, body = label_parts(w)
    return 0.9 + tw(head, LS, True) + 0.9 + 0.9 + tw(body, LS) + 0.9, 3.5


# ------------------------------------------------------------------ geometry helpers
def seg_dir(p, q):
    return (q[0] > p[0]) - (q[0] < p[0]), (q[1] > p[1]) - (q[1] < p[1])


def rect_overlap(a, b, pad=0.0):
    return a[0] < b[2] + pad and b[0] < a[2] + pad and a[1] < b[3] + pad and b[1] < a[3] + pad


def seg_in_rect(p, q, r, pad=0.0):
    """True if the orthogonal segment pq passes through the rectangle r=(x0,y0,x1,y1)."""
    x0, x1 = sorted((p[0], q[0]))
    y0, y1 = sorted((p[1], q[1]))
    return x0 < r[2] - pad and x1 > r[0] + pad and y0 < r[3] - pad and y1 > r[1] + pad


OUT = {"L": (-1, 0), "R": (1, 0), "U": (0, -1), "D": (0, 1)}


# ------------------------------------------------------------------ the book (all sheets, two passes)
class Book:
    def __init__(self):
        self.net = Netlist()
        self.date = ny_date()
        self.pass_no = 1
        self.terms = {}          # sheet no -> {ref: (x, y)}
        self.full = collections.defaultdict(list)   # wire n -> [sheet no]
        self.sheets = []
        self.warnings = []
        self.complete = False

    def zone(self, x, y):
        col = min(COLS, max(1, int((x - FR) // ((W - 2 * FR) / COLS)) + 1))
        row = ROWS[min(len(ROWS) - 1, max(0, int((y - FR) // ((H - 2 * FR) / len(ROWS)))))]
        return f"{row}{col}"

    def term_where(self, ref, this_sheet, short=True):
        """'sheet N C3' for a terminal drawn on another sheet (the lowest such sheet)."""
        for s in sorted(self.terms):
            if s != this_sheet and ref in self.terms[s]:
                z = self.zone(*self.terms[s][ref])
                return f"sheet {s} {z}" if short else f"sheet {s}, zone {z}"
        if self.pass_no == 1 or not self.complete:
            return "sheet ?"
        raise SystemExit(f"cross-reference: {ref} is not drawn on any sheet other than {this_sheet}")

    def pin_where(self, ref, this_sheet):
        """'sheet N C3' where the wires at terminal ref are drawn in full (not just as stubs)."""
        sheets = sorted({s for w in self.net.active_wires if ref in (w["from"], w["to"])
                         for s in self.full.get(w["n"], []) if s != this_sheet})
        for s in sheets:
            if ref in self.terms.get(s, {}):
                return f"sheet {s} {self.zone(*self.terms[s][ref])}"
        return self.term_where(ref, this_sheet)

    def other_wires(self, ref, sheet):
        """Wires at terminal ref that are not drawn in full on this sheet: list of (wire, far_ref)."""
        out = []
        for w in self.net.active_wires:
            if ref in (w["from"], w["to"]):
                if sheet.no in self.full.get(w["n"], []) and self.pass_no == 2:
                    continue
                if any(r["w"]["n"] == w["n"] for r in sheet.routes):
                    continue
                out.append((w, w["to"] if w["from"] == ref else w["from"]))
        return out

    def where(self, n, far_ref, this_sheet):
        """Sheet and zone where wire n is drawn in full, at its far end."""
        sheets = [s for s in self.full.get(n, []) if s != this_sheet]
        if not sheets:
            return "?" if (self.pass_no == 1 or not self.complete) else None
        s = sheets[0]
        xy = self.terms.get(s, {}).get(far_ref)
        if xy is None:
            return f"sheet {s}"
        return f"sheet {s}, zone {self.zone(*xy)}"


# ------------------------------------------------------------------ one sheet
class Sheet:
    def __init__(self, book, no, key, title, subtitle):
        self.book, self.net = book, book.net
        self.no, self.key, self.title, self.subtitle = no, key, title, subtitle
        self.fig = plt.figure(figsize=(W / 25.4, H / 25.4))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, W)
        self.ax.set_ylim(H, 0)
        self.ax.set_aspect("equal")
        self.ax.axis("off")
        self.T = {}              # ref -> dict(x, y, side, slots)
        self.routes = []         # dict(w, pts, kind, lab, slot keys)
        self.blocks = []         # (x0, y0, x1, y1, name)
        self.freetext = []       # (x0, y0, x1, y1, text) outside blocks
        self.texts = []
        self.flags = []
        self.used_slots = set()
        self.notes = []
        self.warn = []

    # ---------------- text
    def text(self, x, y, s, size=8.0, bold=False, color=INK, ha="left", va="center", rot=0, z=30, free=False,
             italic=False):
        if "\u2014" in s or "\u2013" in s:
            raise SystemExit(f"dash in drawing text: {s!r}")
        self.texts.append(s)
        self.ax.text(x, y, s, fontsize=size, fontweight="bold" if bold else "normal", color=color, ha=ha, va=va,
                     rotation=rot, zorder=z, fontfamily=FONT, fontstyle="italic" if italic else "normal")
        if free:
            w_, h_ = tw(s, size, bold), th(size)
            if rot == 90:
                w_, h_ = h_, w_
            x0 = x - (w_ if ha == "right" else w_ / 2 if ha == "center" else 0)
            y0 = y - (h_ / 2 if va in ("center", "center_baseline") else 0 if va == "top" else h_)
            self.freetext.append((x0, y0, x0 + w_, y0 + h_, s))

    def lines(self, x, y, rows, size=7.6, color=INK, step=None, ha="left", bold_first=False, free=True):
        step = step or size * PT * 1.32
        for i, s in enumerate(rows):
            self.text(x, y + i * step, s, size, bold=bold_first and i == 0, color=color, ha=ha, free=free)
        return y + len(rows) * step

    # ---------------- shapes
    def rect(self, x0, y0, x1, y1, fc="white", ec=INK, lw=0.8, z=5, r=0.0, ls="-"):
        if r:
            p = FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc,
                               ec=ec, lw=lw, zorder=z, ls=ls)
        else:
            p = Rectangle((x0, y0), x1 - x0, y1 - y0, fc=fc, ec=ec, lw=lw, zorder=z, ls=ls)
        self.ax.add_patch(p)

    def line(self, pts, color=INK, lw=0.8, z=6, ls="-"):
        self.ax.add_line(Line2D([p[0] for p in pts], [p[1] for p in pts], color=color, lw=lw, zorder=z, ls=ls,
                                solid_capstyle="butt", solid_joinstyle="miter"))

    def region(self, x0, y0, x1, y1, name, sub=None, tx=None):
        self.rect(x0, y0, x1, y1, fc="#f6f8fa", ec="#b7c2cb", lw=0.7, z=1, r=2.5, ls=(0, (5, 2.5)))
        tx = x0 + 2.2 if tx is None else tx
        self.text(tx, y0 + 3.4, name, 8.0, True, "#51606c", free=True, z=2)
        if sub:
            self.text(tx + tw(name, 8.0, True) + 2.0, y0 + 3.4, sub, 7.0, False, "#6f7c86", free=True, z=2)

    # ---------------- terminals
    def term(self, ref, x, y, side, nslots=1, pitch=4.0):
        self.net.pin(ref)
        if ref in self.T:
            raise SystemExit(f"sheet {self.no}: terminal {ref} placed twice")
        self.T[ref] = dict(x=x, y=y, side=side, n=nslots, pitch=pitch)

    def anchor(self, ref, slot=0):
        t = self.T.get(ref)
        if t is None:
            raise SystemExit(f"sheet {self.no}: terminal {ref} is not placed on this sheet")
        if t["side"] == "C":
            return (t["x"], t["y"]), "C"
        if slot >= t["n"]:
            raise SystemExit(f"sheet {self.no}: {ref} has {t['n']} slot(s), slot {slot} asked")
        off = (slot - (t["n"] - 1) / 2) * t["pitch"]
        if t["side"] in "LR":
            return (t["x"], t["y"] + off), t["side"]
        return (t["x"] + off, t["y"]), t["side"]

    def block(self, cid, x0, y0, x1, y1, title, sub=(), pins=(), band="#e8eef3", tsize=9.6, subsize=7.4,
              edge=INK, title_ref=True, center_sub=True, sub_y=None, caption=()):
        """Block with a header band; pins = (pin, side, pos, text[, nslots[, pitch]]) with pos the coordinate along
        the side. A pin whose netlist dir is nc gets a hollow pad with a cross and no terminal."""
        self.rect(x0, y0, x1, y1, fc="white", ec=edge, lw=0.9, z=8, r=1.2)
        bh = 6.2
        self.rect(x0 + 0.35, y0 + 0.35, x1 - 0.35, y0 + bh, fc=band, ec="none", lw=0, z=8.5, r=0.9)
        ref = self.net.comp(cid)["ref"] if cid else ""
        head = f"{ref}  {title}" if (title_ref and ref) else title
        self.text((x0 + x1) / 2, y0 + bh / 2 + 0.25, head, tsize, True, INK, ha="center", z=31)
        yy = sub_y if sub_y is not None else y0 + bh + 3.0
        for s in sub:
            self.text((x0 + x1) / 2 if center_sub else x0 + 2.0, yy, s, subsize, False, GREY,
                      ha="center" if center_sub else "left", z=31)
            yy += subsize * PT * 1.3
        self.blocks.append((x0, y0, x1, y1, cid or title))
        for i, c in enumerate(caption):
            self.text((x0 + x1) / 2, y1 + 3.0 + i * 3.1, c, 6.8, False, GREY, ha="center", free=True)
        for spec in pins:
            pin, side, pos, txt = spec[:4]
            n = spec[4] if len(spec) > 4 else 1
            pitch = spec[5] if len(spec) > 5 else 4.0
            ref_ = f"{cid}.{pin}"
            p = self.net.pin(ref_)
            nc = p["dir"] == "nc"
            ext = max(2.2, (n - 1) * pitch + 2.2)
            if side in "LR":
                xe = x0 if side == "L" else x1
                xo = xe - 1.6 if side == "L" else xe + 1.6
                self.rect(min(xe, xo), pos - ext / 2, max(xe, xo), pos + ext / 2,
                          fc="white" if nc else "#3c4a55", ec=INK, lw=0.6, z=12)
                tx = xe + 1.6 if side == "L" else xe - 1.6
                self.text(tx, pos, txt, TS, not nc, LIGHT if nc else INK, ha="left" if side == "L" else "right", z=31)
                if nc:
                    self._cross(xo + (-1.6 if side == "L" else 1.6), pos)
                else:
                    self.term(ref_, xo, pos, side, n, pitch)
            else:
                ye = y0 if side == "U" else y1
                yo = ye - 1.6 if side == "U" else ye + 1.6
                self.rect(pos - ext / 2, min(ye, yo), pos + ext / 2, max(ye, yo),
                          fc="white" if nc else "#3c4a55", ec=INK, lw=0.6, z=12)
                ty = (y0 + bh + 2.9) if side == "U" else ye - 2.6
                self.text(pos, ty, txt, TS, not nc, LIGHT if nc else INK, ha="center", z=31)
                if nc:
                    self._cross(pos, yo + (-1.6 if side == "U" else 1.6))
                else:
                    self.term(ref_, pos, yo, side, n, pitch)

    def _cross(self, x, y, d=1.0):
        self.line([(x - d, y - d), (x + d, y + d)], INK, 0.8, z=13)
        self.line([(x - d, y + d), (x + d, y - d)], INK, 0.8, z=13)

    def nc_note(self, x, y, s, ha="left"):
        self.text(x, y, s, 6.8, False, GREY, ha=ha, free=True, italic=True)

    def splice(self, cid, x, y, lab_dx=2.0, lab_dy=-2.6, ha="left", r=1.35):
        self.ax.add_patch(Circle((x, y), r, fc=INK, ec="white", lw=0.5, zorder=40))
        ref = self.net.comp(cid)["ref"]
        self.text(x + lab_dx, y + lab_dy, ref, 8.0, True, INK, ha=ha, free=True, z=41)
        self.term(f"{cid}.S", x, y, "C")
        self.blocks.append((x - r, y - r, x + r, y + r, "splice " + cid))

    # ---------------- wires
    def _path(self, A, sa, B, sb, turns, what):
        pts, cur = [A], A
        axis = {"L": "x", "R": "x", "U": "y", "D": "y"}.get(sa)
        for t in turns:
            if isinstance(t, tuple):
                ax_, v = t
            else:
                if axis is None:
                    raise SystemExit(f"sheet {self.no} {what}: first turn from a splice needs ('x', v) or ('y', v)")
                ax_, v = axis, t
            cur = (v, cur[1]) if ax_ == "x" else (cur[0], v)
            pts.append(cur)
            axis = "y" if ax_ == "x" else "x"
        if abs(cur[0] - B[0]) > 1e-6 and abs(cur[1] - B[1]) > 1e-6:
            app = {"L": "x", "R": "x", "U": "y", "D": "y"}.get(sb)
            if app is None:
                app = "y" if axis == "x" else "x"
                pts.append((B[0], cur[1]) if axis == "x" else (cur[0], B[1]))
            elif app == "x":
                pts.append((cur[0], B[1]))
            else:
                pts.append((B[0], cur[1]))
        pts.append(B)
        out = [pts[0]]
        for p in pts[1:]:
            if abs(p[0] - out[-1][0]) < 1e-6 and abs(p[1] - out[-1][1]) < 1e-6:
                continue
            out.append(p)
        clean = [out[0]]
        for i in range(1, len(out) - 1):
            a, b, c = clean[-1], out[i], out[i + 1]
            if (abs(a[0] - b[0]) < 1e-6 and abs(b[0] - c[0]) < 1e-6) or (abs(a[1] - b[1]) < 1e-6 and abs(b[1] - c[1]) < 1e-6):
                continue
            clean.append(b)
        clean.append(out[-1])
        for p, q in zip(clean, clean[1:]):
            if abs(p[0] - q[0]) > 1e-6 and abs(p[1] - q[1]) > 1e-6:
                raise SystemExit(f"sheet {self.no} {what}: diagonal segment {p} -> {q}")
        if len(clean) < 2:
            raise SystemExit(f"sheet {self.no} {what}: zero-length wire")
        if sa in OUT and seg_dir(clean[0], clean[1]) != OUT[sa]:
            raise SystemExit(f"sheet {self.no} {what}: leaves {sa} terminal the wrong way {clean[:2]}")
        if sb in OUT and seg_dir(clean[-2], clean[-1]) != tuple(-v for v in OUT[sb]):
            raise SystemExit(f"sheet {self.no} {what}: enters {sb} terminal the wrong way {clean[-2:]}")
        return clean

    def w(self, a, b, *turns, sa=0, sb=0, lab=None):
        """Draw the netlist wire between pins a and b in full, from a's terminal to b's terminal."""
        wire = self.net.wire(a, b)
        A, sda = self.anchor(a, sa)
        B, sdb = self.anchor(b, sb)
        for ref, s in ((a, sa), (b, sb)):
            if self.T[ref]["side"] != "C":
                k = (ref, s)
                if k in self.used_slots:
                    raise SystemExit(f"sheet {self.no}: slot {s} of {ref} used twice")
                self.used_slots.add(k)
        pts = self._path(A, sda, B, sdb, turns, f"{a} - {b}")
        self.routes.append(dict(w=wire, pts=pts, kind="full", lab=lab, ends=(a, b)))
        return pts

    def stub(self, a, b, fx, fy, fdir, *turns, sa=0, lab=None, far=None):
        """Draw the start of the wire a - b from a's terminal to an off-sheet flag at (fx, fy).
        fdir is the way the flag points (L or R). far is the text naming the far end."""
        wire = self.net.wire(a, b)
        A, sda = self.anchor(a, sa)
        if self.T[a]["side"] != "C":
            k = (a, sa)
            if k in self.used_slots:
                raise SystemExit(f"sheet {self.no}: slot {sa} of {a} used twice")
            self.used_slots.add(k)
        pts = self._path(A, sda, (fx, fy), "L" if fdir == "R" else "R", turns, f"stub {a} - {b}")
        self.routes.append(dict(w=wire, pts=pts, kind="stub", lab=lab, ends=(a, b)))
        self.flags.append(dict(x=fx, y=fy, dir=fdir, wire=wire, far=b, text=far))
        return pts

    def stub_group(self, a, bs, fx, fdir, far=None):
        """Several wires from terminal a (one per slot, slot k to bs[k]) running straight into one flag at x=fx."""
        wires, pts_all = [], []
        for k, b in enumerate(bs):
            wire = self.net.wire(a, b)
            A, sda = self.anchor(a, k)
            key = (a, k)
            if key in self.used_slots:
                raise SystemExit(f"sheet {self.no}: slot {k} of {a} used twice")
            self.used_slots.add(key)
            pts = self._path(A, sda, (fx, A[1]), "L" if fdir == "R" else "R", (), f"stub {a} - {b}")
            self.routes.append(dict(w=wire, pts=pts, kind="stub", lab=None, ends=(a, b)))
            wires.append(wire)
            pts_all.append(A[1])
        self.flags.append(dict(x=fx, y=sum(pts_all) / len(pts_all), dir=fdir, wire=wires[0], wires=wires,
                               far=bs[0], text=far, h=max(8.8, (len(bs) - 1) * self.T[a]["pitch"] + 6.0)))

    def lane(self, cid, pts, fam):
        """A harness lane (not a netlist wire): cable cid drawn as an orthogonal polyline in its family colour."""
        for p, q in zip(pts, pts[1:]):
            if abs(p[0] - q[0]) > 1e-6 and abs(p[1] - q[1]) > 1e-6:
                raise SystemExit(f"sheet {self.no} lane {cid}: diagonal segment {p} -> {q}")
        pseudo = dict(cable=cid, branch=None, gauge="harness", color=f"lane_{fam}", cut_mm=None, n=-1,
                      **{"from": cid, "to": cid})
        self.routes.append(dict(w=pseudo, pts=list(pts), kind="lane", lab="none", ends=("", "")))

    # ---------------- finishing
    def _crossings(self):
        segs = []
        for ri, r in enumerate(self.routes):
            for p, q in zip(r["pts"], r["pts"][1:]):
                segs.append((ri, p, q))
        hops, n_cross = collections.defaultdict(list), 0
        for i in range(len(segs)):
            ri, p, q = segs[i]
            for j in range(i + 1, len(segs)):
                rj, u, v = segs[j]
                if ri == rj:
                    continue
                hi = abs(p[1] - q[1]) < 1e-6
                hj = abs(u[1] - v[1]) < 1e-6
                if hi == hj:
                    # collinear overlap check
                    if hi and abs(p[1] - u[1]) < 0.6:
                        a0, a1 = sorted((p[0], q[0]))
                        b0, b1 = sorted((u[0], v[0]))
                        if min(a1, b1) - max(a0, b0) > 0.8:
                            self.warn.append(f"overlap: {self._rname(ri)} and {self._rname(rj)} run on top of each other near y={p[1]:.1f}")
                    if not hi and abs(p[0] - u[0]) < 0.6:
                        a0, a1 = sorted((p[1], q[1]))
                        b0, b1 = sorted((u[1], v[1]))
                        if min(a1, b1) - max(a0, b0) > 0.8:
                            self.warn.append(f"overlap: {self._rname(ri)} and {self._rname(rj)} run on top of each other near x={p[0]:.1f}")
                    continue
                (hp, hq, hr), (vp, vq, vr) = ((p, q, ri), (u, v, rj)) if hi else ((u, v, rj), (p, q, ri))
                x0, x1 = sorted((hp[0], hq[0]))
                y0, y1 = sorted((vp[1], vq[1]))
                cx, cy = vp[0], hp[1]
                if x0 - 1e-6 <= cx <= x1 + 1e-6 and y0 - 1e-6 <= cy <= y1 + 1e-6:
                    at_h_end = abs(cx - x0) < 1e-6 or abs(cx - x1) < 1e-6
                    at_v_end = abs(cy - y0) < 1e-6 or abs(cy - y1) < 1e-6
                    if at_h_end and at_v_end:
                        continue                                  # corner to corner: shared splice or terminal
                    if at_h_end or at_v_end:
                        if not self._shared_node(hr, vr, (cx, cy)):
                            self.warn.append(f"T-junction look: {self._rname(hr)} meets {self._rname(vr)} at ({cx:.1f}, {cy:.1f})")
                        continue
                    n_cross += 1
                    hops[hr].append((cx, cy))
        return hops, n_cross

    def _shared_node(self, ri, rj, pt):
        for ref in self.routes[ri]["ends"]:
            t = self.T.get(ref)
            if t and t["side"] == "C" and abs(t["x"] - pt[0]) < 1e-6 and abs(t["y"] - pt[1]) < 1e-6:
                return True
        return False

    def _rname(self, ri):
        w = self.routes[ri]["w"]
        return f"{w['cable']}{(' ' + w['branch']) if w.get('branch') else ''} ({w['from']}-{w['to']})"

    def _hop_pts(self, pts, hops, r=1.5):
        out = [pts[0]]
        for p, q in zip(pts, pts[1:]):
            if abs(p[1] - q[1]) < 1e-6:
                hs = sorted([h for h in hops if abs(h[1] - p[1]) < 1e-6 and min(p[0], q[0]) < h[0] < max(p[0], q[0])],
                            key=lambda h: h[0], reverse=q[0] < p[0])
                sgn = 1 if q[0] > p[0] else -1
                for hx, hy in hs:
                    out.append((hx - sgn * r, hy))
                    for k in range(1, 12):
                        a = 3.14159265 * k / 12
                        out.append((hx - sgn * r * math.cos(a), hy - r * math.sin(a)))
                    out.append((hx + sgn * r, hy))
            out.append(q)
        return out

    def _draw_wire(self, r, hops):
        w = r["w"]
        col = w["color"]
        rgb = WIRE_RGB[col]
        lw = core_lw(w["gauge"])
        pts = self._hop_pts(r["pts"], hops)
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        z = 20 if r["kind"] == "full" else 19
        if w["gauge"] == "FPC ribbon":
            self.ax.add_line(Line2D(xs, ys, color="#6b7680", lw=lw + 1.2, zorder=z, solid_capstyle="butt",
                                    solid_joinstyle="miter"))
            self.ax.add_line(Line2D(xs, ys, color="#ffffff", lw=lw, zorder=z + 0.1, solid_capstyle="butt",
                                    solid_joinstyle="miter"))
            for d in (-1.1, 1.1):
                pass
            return
        if col == "none":
            self.ax.add_line(Line2D(xs, ys, color=rgb, lw=lw, zorder=z, solid_capstyle="butt", solid_joinstyle="miter"))
            return
        casing = "#2a2a2a" if lum(rgb) > 0.3 else "#000000"
        self.ax.add_line(Line2D(xs, ys, color=casing, lw=lw + 0.9, zorder=z, solid_capstyle="butt",
                                solid_joinstyle="miter"))
        self.ax.add_line(Line2D(xs, ys, color=rgb, lw=lw, zorder=z + 0.1, solid_capstyle="butt",
                                solid_joinstyle="miter"))
        if col in UNSET:
            self.ax.add_line(Line2D(xs, ys, color="white", lw=lw * 0.45, zorder=z + 0.2, ls=(0, (2.2, 2.2)),
                                    solid_capstyle="butt", solid_joinstyle="miter"))

    def _label_spot(self, r):
        lw_, lh = label_size(r["w"])
        pts, lab = r["pts"], r["lab"]
        segs = list(zip(pts, pts[1:]))
        hseg = [(p, q) for p, q in segs if abs(p[1] - q[1]) < 1e-6]
        vseg = [(p, q) for p, q in segs if abs(p[0] - q[0]) < 1e-6]
        if lab == "none":
            return None
        if isinstance(lab, tuple) and lab[0] == "tag":
            # label box at (wx, wy + dy) with a vertical leader to the wire point (wx, wy)
            _, wx, wy, dy = lab
            return ("tag", wx, wy, dy)
        if isinstance(lab, (int, float)):
            cand = [(p, q) for p, q in hseg if min(p[0], q[0]) <= lab <= max(p[0], q[0])]
            if not cand:
                raise SystemExit(f"sheet {self.no} {self._rname(self.routes.index(r))}: no horizontal run at x={lab}")
            p, q = max(cand, key=lambda s: abs(s[0][0] - s[1][0]))
            return (lab, p[1], 0, (p, q))
        if isinstance(lab, tuple) and lab[0] == "y":
            cand = [(p, q) for p, q in vseg if min(p[1], q[1]) <= lab[1] <= max(p[1], q[1])]
            if not cand:
                raise SystemExit(f"sheet {self.no} {self._rname(self.routes.index(r))}: no vertical run at y={lab[1]}")
            p, q = cand[0]
            return (p[0], lab[1], 90, (p, q))
        best = max(hseg, key=lambda s: abs(s[0][0] - s[1][0]), default=None)
        if best is not None and abs(best[0][0] - best[1][0]) >= lw_ + 3:
            p, q = best
            if r["kind"] == "stub":
                # keep the label away from the flag end
                x = (p[0] + q[0]) / 2
            else:
                x = (p[0] + q[0]) / 2
            return (x, p[1], 0, best)
        bestv = max(vseg, key=lambda s: abs(s[0][1] - s[1][1]), default=None)
        if bestv is not None and abs(bestv[0][1] - bestv[1][1]) >= lw_ + 3:
            p, q = bestv
            return (p[0], (p[1] + q[1]) / 2, 90, bestv)
        if best is not None:
            p, q = best
            return ((p[0] + q[0]) / 2, p[1], 0, best)
        p, q = bestv
        return (p[0], (p[1] + q[1]) / 2, 90, bestv)

    def _draw_label(self, r, spot):
        w = r["w"]
        if spot[0] == "tag":
            _, wx, wy, dy = spot
            box = self._draw_label(r, (wx, wy + dy, 0, ((wx - 100, wy + dy), (wx + 100, wy + dy))))
            yb = box[1] if dy > 0 else box[3]
            self.line([(wx, wy), (wx, yb)], "#7a8790", 0.6, z=49, ls=(0, (1.2, 1.0)))
            return box
        x, y, rot, seg = spot
        head, body = label_parts(w)
        hw, bw = tw(head, LS, True), tw(body, LS)
        pad, h = 0.9, 3.5
        L1 = hw + 2 * pad
        L2 = bw + 2 * pad
        total = L1 + L2
        rgb = WIRE_RGB[w["color"]]
        fill = rgb if w["color"] not in ("none",) else "#d9d9d9"
        if w["color"] in UNSET:
            fill = "#cfcfcf"
        tcol = "white" if lum(fill) < 0.55 else INK
        edge = darker(fill) if lum(fill) > 0.25 else "#000000"
        if lum(fill) > 0.9:
            edge = "#6b7680"
        if rot == 0:
            x0 = x - total / 2
            box = (x0, y - h / 2, x0 + total, y + h / 2)
            self.rect(x0, y - h / 2, x0 + L1, y + h / 2, fc=fill, ec=edge, lw=0.6, z=50)
            self.rect(x0 + L1, y - h / 2, x0 + total, y + h / 2, fc="white", ec=edge, lw=0.6, z=50)
            self.text(x0 + L1 / 2, y + 0.15, head, LS, True, tcol, ha="center", z=51)
            self.text(x0 + L1 + pad, y + 0.15, body, LS, False, INK, ha="left", z=51)
            (p, q) = seg
            if not (min(p[0], q[0]) + 0.5 <= box[0] and box[2] <= max(p[0], q[0]) - 0.5):
                self.warn.append(f"label of {self._rname(self.routes.index(r))} is longer than its run")
        else:
            y1 = y + total / 2
            box = (x - h / 2, y1 - total, x + h / 2, y1)
            self.rect(x - h / 2, y1 - L1, x + h / 2, y1, fc=fill, ec=edge, lw=0.6, z=50)
            self.rect(x - h / 2, y1 - total, x + h / 2, y1 - L1, fc="white", ec=edge, lw=0.6, z=50)
            self.text(x + 0.15, y1 - L1 / 2, head, LS, True, tcol, ha="center", rot=90, z=51)
            self.text(x + 0.15, y1 - L1 - pad, body, LS, False, INK, ha="center", va="bottom", rot=90, z=51)
            # va bottom with rotation: text starts at the anchor and runs up
            (p, q) = seg
            if not (min(p[1], q[1]) + 0.5 <= box[1] and box[3] <= max(p[1], q[1]) - 0.5):
                self.warn.append(f"label of {self._rname(self.routes.index(r))} is longer than its run")
        return box

    def _draw_flag(self, f):
        w = f["wire"]
        where = self.book.where(w["n"], f["far"], self.no)
        if where is None:
            raise SystemExit(f"sheet {self.no}: wire {w['cable']} {w['from']}-{w['to']} is only a stub here "
                             f"and is not drawn in full on any other sheet")
        head, body = label_parts(w)
        if f.get("wires"):
            ws = f["wires"]
            head = " ".join(x["cable"] for x in ws)
            cuts = "/".join(str(int(x["cut_mm"])) for x in ws)
            body = f"{ws[0]['gauge']}  {cuts} mm  {CODE[ws[0]['color']]}"
        s1, s2 = LS - 0.4, 6.8
        hw, bw = tw(head, s1, True), tw(body, s1)
        t2 = f"{f['text'] or f['far']}: {where}"
        L1 = hw + 1.6
        wd = max(L1 + bw + 2.4, tw(t2, s2) + 2.4) + 1.2
        h, tip = f.get("h", 8.8), 2.6
        x, y = f["x"], f["y"]
        if f["dir"] == "R":
            poly = [(x, y - h / 2), (x + wd, y - h / 2), (x + wd + tip, y), (x + wd, y + h / 2), (x, y + h / 2)]
            tx = x + 1.0
        else:
            poly = [(x, y - h / 2), (x - wd, y - h / 2), (x - wd - tip, y), (x - wd, y + h / 2), (x, y + h / 2)]
            tx = x - wd + 1.0
        self.ax.add_patch(Polygon(poly, closed=True, fc="#fff3c4", ec="#8a6d00", lw=0.7, zorder=45))
        rgb = WIRE_RGB[w["color"]]
        fill = "#cfcfcf" if w["color"] in UNSET else ("#d9d9d9" if w["color"] == "none" else rgb)
        edge = darker(fill) if lum(fill) > 0.25 else "#000000"
        if lum(fill) > 0.9:
            edge = "#6b7680"
        yl = y - 1.95
        self.rect(tx, yl - 1.55, tx + L1, yl + 1.55, fc=fill, ec=edge, lw=0.5, z=46)
        self.text(tx + L1 / 2, yl + 0.12, head, s1, True, "white" if lum(fill) < 0.55 else INK, ha="center", z=47)
        self.text(tx + L1 + 0.9, yl + 0.12, body, s1, False, INK, z=47)
        self.text(tx + 0.2, y + 2.2, t2, s2, False, "#5b4a00", z=47)
        xs = [p[0] for p in poly]
        box = (min(xs), y - h / 2, max(xs), y + h / 2)
        self.freetext.append(box + (head,))
        return box

    def frame(self):
        ax = self.ax
        self.rect(5, 5, W - 5, H - 5, fc="none", ec=INK, lw=1.0, z=2)
        self.rect(FR, FR, W - FR, H - FR, fc="none", ec=INK, lw=0.6, z=2)
        cw = (W - 2 * FR) / COLS
        rh = (H - 2 * FR) / len(ROWS)
        for i in range(COLS + 1):
            x = FR + i * cw
            for ya, yb in ((5, FR), (H - FR, H - 5)):
                self.line([(x, ya), (x, yb)], INK, 0.5, z=2)
            if i < COLS:
                for yc in (7.5, H - 7.5):
                    self.text(x + cw / 2, yc, str(i + 1), 7.0, False, GREY, ha="center", z=3)
        for j in range(len(ROWS) + 1):
            y = FR + j * rh
            for xa, xb in ((5, FR), (W - FR, W - 5)):
                self.line([(xa, y), (xb, y)], INK, 0.5, z=2)
            if j < len(ROWS):
                for xc in (7.5, W - 7.5):
                    self.text(xc, y + rh / 2, ROWS[j], 7.0, False, GREY, ha="center", z=3)

    def heading(self):
        self.text(14, 17.2, f"Sheet {self.no}   {self.title}", 17, True, INK, free=True)
        self.text(14, 24.2, self.subtitle, 8.2, False, GREY, free=True)

    def title_block(self, n_full, n_stub, n_all, extra=None):
        x0, y0, x1, y1 = 272, 249, W - FR, H - FR
        self.rect(x0, y0, x1, y1, fc="white", ec=INK, lw=0.9, z=8)
        self.line([(x0, y0 + 9.5), (x1, y0 + 9.5)], INK, 0.5, z=9)
        self.line([(x1 - 30, y0), (x1 - 30, y0 + 9.5)], INK, 0.5, z=9)
        self.text(x0 + 2, y0 + 3.0, "OPEN DUCK MINI V2, ALTAAY-LAB BUILD: WIRING", 7.0, True, GREY, z=10)
        self.text(x0 + 2, y0 + 7.0, self.title, 9.8, True, INK, z=10)
        self.text(x1 - 15, y0 + 3.0, "SHEET", 6.6, False, GREY, ha="center", z=10)
        self.text(x1 - 15, y0 + 7.0, f"{self.no} of {self.book.n_sheets}", 9.8, True, INK, ha="center", z=10)
        rows = [
            f"Source: wiring/netlist.yaml rev {self.net.rev} (sha256 {self.net.sha})",
            f"Date: {self.book.date} (TZ=America/New_York date)",
            "Generator: wiring/sheets/make_sheets.py (sheetlib.py)",
            extra or f"Wires drawn in full here: {n_full} of {n_all} in the netlist; stubs to other sheets: {n_stub}",
            "Print A3 or tabloid at 100 %, or Letter fit to page. Lengths in mm.",
        ]
        for i, s in enumerate(rows):
            self.text(x0 + 2, y0 + 13.6 + i * 3.55, s, 7.0, False, INK, z=10)
        self.rect(x0, y1 - 6.4, x1, y1, fc="#b3261e", ec=INK, lw=0.6, z=9)
        self.text((x0 + x1) / 2, y1 - 3.1, "GENERATED, DO NOT EDIT. Change netlist.yaml and run make_sheets.py.",
                  7.6, True, "white", ha="center", z=10)
        self.blocks.append((x0, y0, x1, y1, "title block"))

    def legend(self, x0=FR, y0=249, x1=150, y1=H - FR):
        self.rect(x0, y0, x1, y1, fc="white", ec=INK, lw=0.8, z=8)
        self.text(x0 + 2, y0 + 3.2, "LEGEND", 7.4, True, GREY, z=10)
        xs = x0 + 2
        yy = y0 + 8.0
        samples = [("red", "RD"), ("black", "BK"), ("yellow", "YE"), ("white", "WH"), ("green", "GN"), ("blue", "BU"),
                   ("orange", "OG"), ("brown", "BN")]
        for i, (c, code) in enumerate(samples):
            xx = xs + i * 17.0
            self._sample(xx, yy, xx + 7.5, c, 1.9)
            self.text(xx + 8.5, yy, code, 7.0, True, INK, z=10)
        yy += 5.2
        self._sample(xs, yy, xs + 9, "kit", 1.9)
        self.text(xs + 10.5, yy, "colour not set by the netlist (kit cable, fuse holder lead): as shipped", 7.0, False, INK, z=10)
        yy += 4.6
        self._sample(xs, yy, xs + 9, "none", 0.9)
        self.text(xs + 10.5, yy, "bare resistor lead, no wire", 7.0, False, INK, z=10)
        self.ax.add_patch(Circle((xs + 75.5, yy), 1.3, fc=INK, ec="white", lw=0.5, zorder=12))
        self.text(xs + 78, yy, "solder splice", 7.0, False, INK, z=10)
        self.rect(xs + 100, yy - 1.1, xs + 102.2, yy + 1.1, fc="#3c4a55", ec=INK, lw=0.6, z=12)
        self.text(xs + 103.5, yy, "terminal", 7.0, False, INK, z=10)
        yy += 4.6
        for i, (g, t) in enumerate((("16 AWG", "16"), ("20 AWG", "20"), ("22 AWG", "22"), ("26 AWG", "26"))):
            xx = xs + i * 15.0
            self.line([(xx, yy), (xx + 7, yy)], "#000000", core_lw(g) + 0.9, z=10)
            self.line([(xx, yy), (xx + 7, yy)], "#888888", core_lw(g), z=11)
            self.text(xx + 8, yy, t, 7.0, False, INK, z=10)
        self.text(xs + 60, yy, "AWG: line weight follows the gauge", 7.0, False, INK, z=10)
        yy += 5.0
        # label anatomy
        lx = xs
        demo = dict(cable="P13", gauge="20 AWG", cut_mm=550, color="red")
        head, body = "P13", "20 AWG   550 mm   RD"
        L1 = tw(head, LS, True) + 1.8
        L2 = tw(body, LS) + 1.8
        self.rect(lx, yy - 1.75, lx + L1, yy + 1.75, fc=WIRE_RGB["red"], ec=darker(WIRE_RGB["red"]), lw=0.6, z=11)
        self.rect(lx + L1, yy - 1.75, lx + L1 + L2, yy + 1.75, fc="white", ec=darker(WIRE_RGB["red"]), lw=0.6, z=11)
        self.text(lx + L1 / 2, yy + 0.15, head, LS, True, "white", ha="center", z=12)
        self.text(lx + L1 + 0.9, yy + 0.15, body, LS, False, INK, z=12)
        self.text(lx + L1 + L2 + 2, yy, "= cable id (CABLE_MAP), gauge, cut length, colour code (IEC 60757)", 7.0,
                  False, INK, z=10)
        yy += 5.2
        # hop, nc, flag
        self.line([(xs, yy), (xs + 3, yy)], INK, 1.0, z=10)
        arc = [(xs + 4.5 - 1.5 * math.cos(math.pi * k / 12), yy - 1.5 * math.sin(math.pi * k / 12)) for k in range(13)]
        self.line(arc, INK, 1.0, z=10)
        self.line([(xs + 6, yy), (xs + 9, yy)], INK, 1.0, z=10)
        self.line([(xs + 4.5, yy - 3), (xs + 4.5, yy + 3)], INK, 1.0, z=9)
        self.text(xs + 10.5, yy, "hop: crossing, no contact", 7.0, False, INK, z=10)
        self._cross(xs + 47, yy)
        self.text(xs + 49.5, yy, "nc, not connected", 7.0, False, INK, z=10)
        poly = [(xs + 76, yy - 2.2), (xs + 86, yy - 2.2), (xs + 88, yy), (xs + 86, yy + 2.2), (xs + 76, yy + 2.2)]
        self.ax.add_patch(Polygon(poly, closed=True, fc="#fff3c4", ec="#8a6d00", lw=0.7, zorder=11))
        self.text(xs + 89.5, yy, "wire continues: sheet, zone", 7.0, False, INK, z=10)
        self.blocks.append((x0, y0, x1, y1, "legend"))

    def _sample(self, x0, y, x1, col, lw):
        rgb = WIRE_RGB[col]
        if col != "none":
            self.line([(x0, y), (x1, y)], "#000000" if lum(rgb) < 0.3 else "#2a2a2a", lw + 0.9, z=10)
        self.line([(x0, y), (x1, y)], rgb, lw, z=11)
        if col in UNSET:
            self.ax.add_line(Line2D([x0, x1], [y, y], color="white", lw=lw * 0.45, zorder=12, ls=(0, (2.2, 2.2))))

    def notes_box(self, x0, y0, x1, y1, notes, size=7.0):
        self.rect(x0, y0, x1, y1, fc="white", ec=INK, lw=0.8, z=8)
        self.text(x0 + 2, y0 + 3.2, "NOTES", 7.4, True, GREY, z=10)
        yy = y0 + 7.6
        for i, s in enumerate(notes):
            for k, part in enumerate(self._wrap(f"{i + 1}. {s}", x1 - x0 - 4.5, size)):
                self.text(x0 + 2 + (0 if k == 0 else 3.0), yy, part, size, False, INK, z=10)
                yy += size * PT * 1.25
            yy += 0.5
        if yy > y1 + 0.5:
            self.warn.append(f"notes overflow their box by {yy - y1:.1f} mm")
        self.blocks.append((x0, y0, x1, y1, "notes"))

    @staticmethod
    def _wrap(s, width, size):
        words, out, cur = s.split(" "), [], ""
        for wd in words:
            t = (cur + " " + wd).strip()
            if tw(t, size) <= width or not cur:
                cur = t
            else:
                out.append(cur)
                cur = wd
        if cur:
            out.append(cur)
        return out

    def finish(self):
        hops, n_cross = self._crossings()
        self.n_cross = n_cross
        for i, r in enumerate(self.routes):
            self._draw_wire(r, hops.get(i, []))
        boxes = []
        for i, r in enumerate(self.routes):
            if r["kind"] == "stub":
                continue
            spot = self._label_spot(r)
            if spot is None:
                continue
            boxes.append((self._draw_label(r, spot), i))
        flagboxes = [self._draw_flag(f) for f in self.flags]
        # layout checks
        for k, (b, i) in enumerate(boxes):
            for b2, j in boxes[k + 1:]:
                if rect_overlap(b, b2, 0.3):
                    self.warn.append(f"labels overlap: {self._rname(i)} and {self._rname(j)}")
            for blk in self.blocks:
                if rect_overlap(b, blk[:4], 0.2):
                    self.warn.append(f"label of {self._rname(i)} overlaps {blk[4]}")
            for ft in self.freetext:
                if rect_overlap(b, ft[:4], 0.2):
                    self.warn.append(f"label of {self._rname(i)} overlaps text '{ft[4][:30]}'")
            for j, r in enumerate(self.routes):
                if j == i:
                    continue
                for p, q in zip(r["pts"], r["pts"][1:]):
                    if seg_in_rect(p, q, b, 0.15):
                        self.warn.append(f"label of {self._rname(i)} sits on {self._rname(j)}")
                        break
            for hl in hops.values():
                for (hx, hy) in hl:
                    if b[0] - 1.5 < hx < b[2] + 1.5 and b[1] - 1.5 < hy < b[3] + 1.5:
                        self.warn.append(f"label of {self._rname(i)} covers a hop")
        for i, r in enumerate(self.routes):
            ends = {self.routes[i]["ends"][0].split(".")[0], self.routes[i]["ends"][1].split(".")[0]}
            for p, q in zip(r["pts"], r["pts"][1:]):
                for blk in self.blocks:
                    if blk[4] in ends or blk[4].replace("splice ", "") in ends:
                        continue
                    if seg_in_rect(p, q, blk[:4], 0.3):
                        self.warn.append(f"{self._rname(i)} passes through {blk[4]}")
                for ft in self.freetext:
                    if seg_in_rect(p, q, ft[:4], 0.2):
                        self.warn.append(f"{self._rname(i)} passes through text '{ft[4][:30]}'")
        for t, info in self.T.items():
            if info["side"] == "C":
                continue
            used = sum(1 for (ref, s) in self.used_slots if ref == t)
            if used != info["n"]:
                self.warn.append(f"terminal {t}: {info['n']} slot(s), {used} wire(s) drawn")
        n_full = len({r["w"]["n"] for r in self.routes if r["kind"] == "full"})
        n_stub = len({r["w"]["n"] for r in self.routes if r["kind"] == "stub"})
        self.n_full, self.n_stub = n_full, n_stub
        return hops

    def save(self, outdir, dpi=200):
        svg = os.path.join(outdir, f"{self.key}.svg")
        png = os.path.join(outdir, f"{self.key}.png")
        self.fig.savefig(svg, metadata={"Date": None})
        self.fig.savefig(png, dpi=dpi)
        from PIL import Image
        if os.path.getsize(png) > 950_000:
            im = Image.open(png).convert("RGB")
            im.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(png, optimize=True)
        plt.close(self.fig)
        return svg, png
