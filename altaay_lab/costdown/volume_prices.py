"""Volume prices for every order line. Writes VOLUME.csv.

A cell is filled only when a page printed that quantity break.
An empty price cell is BLOCKER. Qty-1 prices already cited in ORDER.csv
are kept and labeled. This script does not invent a discount.
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ORDER = os.path.join(HERE, "..", "bom", "order", "ORDER.csv")
OUT = os.path.join(HERE, "VOLUME.csv")

# Overrides from pages opened 2026-11-12 for this pass.
# None means BLOCKER. A missing key means "not re-opened; 100 and 1000 stay empty".
# tier text is stored in the note.
OPENED = {
    "servo": dict(p1=20.00, p100=None, p1000=None,
                  note="Seeed page opened this pass. Printed price is 20.00. No 10, 100, or 1000 row on that page. The 2026-11-01 bill's 19.00 at 10 or more was not on the page."),
    "cell": dict(p1=8.99, p100=None, p1000=None,
                 note="illumn page opened this pass. One price, 8.99. No quantity table."),
    "pi": dict(p1=87.95, p100=None, p1000=None,
               note="CanaKit page opened this pass. Starter kit 87.95. Bare board 16.35. No 100 or 1000 row. ORDER.csv had 89.95 for the same kit earlier the same day."),
    "bec": dict(p1=54.95, p100=None, p1000=None,
                note="Horizon Hobby page opened this pass. One price, 54.95."),
    "pa6": dict(p1=None, p100=None, p1000=None,
                note="MatterHackers page opened this pass. No quantity table was printed. The dollar on the page was not in the extract, so the qty-1 figure stays the ORDER.csv cite of 57.99 and is not repeated as a new read."),
    "mcp": dict(p1=2.41, p100=1.82, p1000=None,
                note="DigiKey table: 1 at 2.41, 25 at 2.01, 100 at 1.82. No 1000 row."),
    "dmp": dict(p1=0.44, p100=0.1705, p1000=None,
                note="DigiKey cut tape: 1 at 0.44, 10 at 0.271, 25 at 0.2244, 50 at 0.1952, 100 at 0.1705. Reel starts at 3000 (0.09464), so 1000 is not a printed row."),
    "smaj": dict(p1=0.51, p100=0.1975, p1000=None,
                 note="DigiKey cut tape: 1 at 0.51, 10 at 0.313, 50 at 0.2258, 100 at 0.1975, 500 at 0.14758. Reel starts at 5000 (0.08591), so 1000 is not a printed row."),
}


def money(v):
    if v is None or v == "":
        return ""
    return "%.4f" % float(v) if float(v) < 1 else "%.2f" % float(v)


def main():
    rows_in = list(csv.DictReader(open(ORDER, encoding="utf-8")))
    out = []
    for r in rows_in:
        lid = r["line_id"]
        need = r["need"].strip()
        unit = r["unit_price_usd"].strip()
        label = r["price_label"].strip()
        stock = r["stock"].strip()
        tool = (r["maps_to"] or "").startswith("TL:")
        o = OPENED.get(lid)
        if o:
            p1, p100, p1000 = o["p1"], o["p100"], o["p1000"]
            if p1 is None and unit and not label.startswith("BLOCKER"):
                p1 = float(unit)
                src = "ORDER.csv cited 2026-11-12, page re-opened and no break printed"
            else:
                src = "page opened this pass"
            note = o["note"]
        else:
            p1 = float(unit) if unit else None
            p100 = None
            p1000 = None
            src = "ORDER.csv" if p1 is not None else "none"
            if label.startswith("BLOCKER") or not unit:
                note = "No published break. " + (r["blocker"] or r["note"] or "page not opened")
            else:
                note = "Qty 1 is the ORDER.csv cite. No 100 or 1000 break was printed on a page this pass opened."
        out.append(dict(
            line_id=lid, part=r["part"], need=need, tool="yes" if tool else "no",
            stock=stock, usd_1=money(p1), usd_100=money(p100), usd_1000=money(p1000),
            source=src, url=r["url"], label="cited" if (p1 is not None or p100 is not None) else "BLOCKER",
            note=note,
        ))
    # Alternate servo. Not an order line. 4+ is the last printed tier and has no ceiling.
    out.append(dict(
        line_id="servo_waveshare_74", part="Waveshare ST3215 7.4 V, alternate to the Seeed line",
        need="14", tool="no", stock="",
        usd_1="16.99", usd_100="16.31", usd_1000="16.31",
        source="page opened this pass",
        url="https://www.waveshare.com/st3215-servo.htm?sku=33014",
        label="cited",
        note="Printed tiers: 1 at 16.99, 2 at 16.59, 3 at 16.39, 4 or more at 16.31. No separate 100 or 1000 row. 4 or more has no ceiling on the page, so 100 and 1000 use 16.31. Backlash was not on the page.",
    ))
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)

    def num(s):
        return None if s == "" else float(s)

    by_id = {r["line_id"]: r for r in rows_in}

    def one_duck_pieces(lid):
        """How many priced units one duck buys, so a pack is not multiplied by the piece count."""
        if lid == "servo_waveshare_74":
            return 14.0
        src = by_id[lid]
        buy = float(src["buy_qty"]) if src["buy_qty"].strip() else None
        pack = float(src["pack_covers"]) if src["pack_covers"].strip() else None
        need = float(src["need"]) if src["need"].strip() else None
        if buy is None or need is None:
            return None
        if pack is not None and pack > buy:
            return buy  # one or more packs, not one price per piece
        return buy

    def duck(vol_key, use_waveshare=False):
        """Per-duck repeat parts. Tools excluded. A missing price is a blocker, not a zero."""
        known = 0.0
        blockers = []
        for row in out:
            if row["tool"] == "yes":
                continue
            if row["line_id"] == "servo" and use_waveshare:
                continue
            if row["line_id"] == "servo_waveshare_74" and not use_waveshare:
                continue
            k = one_duck_pieces(row["line_id"])
            price = num(row[vol_key])
            if k is None or price is None:
                blockers.append(row["line_id"])
                continue
            known += price * k
        return round(known, 2), blockers

    print("lines", len(out))
    for n, key in ((1, "usd_1"), (100, "usd_100"), (1000, "usd_1000")):
        known, blockers = duck(key, False)
        print("order", n, "known_repeat", known, "blocker_lines", len(blockers))
        known_w, blockers_w = duck(key, True)
        print("waveshare_swap", n, "known_repeat", known_w, "blocker_lines", len(blockers_w))


if __name__ == "__main__":
    main()
