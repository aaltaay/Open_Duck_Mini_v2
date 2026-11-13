#!/usr/bin/env python3
"""Domestic-component share for one duck, from ORDER.csv.

This is a worksheet, not a customs ruling. It reads altaay_lab/bom/order/ORDER.csv
and applies the row table below. Prices that ORDER.csv leaves blank are the
BOM.md line prices named in BOM_FALLBACK, from the page read recorded in that
file, not re-opened here.

Run from the repo root:
  python3 altaay_lab/compliance/domestic_share.py
The script writes altaay_lab/compliance/DOMESTIC_ROWS.csv beside itself.
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORDER = HERE.parent / "bom" / "order" / "ORDER.csv"
OUT = HERE / "DOMESTIC_ROWS.csv"
CENT = Decimal("0.01")
Q = Decimal("0.0001")

# Not incorporated into the walking duck.
TOOLS = {
    "pinecil", "tips", "sdread", "usbc", "l2", "nozzle",
    "t3", "t4", "t5", "t6", "t7b", "t9", "t10",
    "t11", "t12", "t13", "t14", "t15", "t16", "t17", "t18", "t19",
}
# Wiped off, or a process aid that is not an article left in the duck.
PROCESS = {"flux", "alcohol"}
# Stays outside the body. PARTS_CHECK.csv line 15.
OUTSIDE = {"controller"}
# Nest article, not a component of the walking duck.
# wells and well-route stay components. FLUSH_CONTACTS.md section 6 puts the
# gold inlays in sit_seat and the ideal-diode paths in the trunk. No price yet.
NEST = {
    "adapter", "felt1", "felt2", "foam", "gate", "jack", "nestpla",
    "ring", "sun", "wall", "pin", "feed",
}

# num/den of the purchased unit that is incorporated in the duck.
# Spares and nest-only pieces are left out.
FRACTION = {
    "foil": (Decimal("0.3"), Decimal("15")),       # BOM.md E10, about 0.3 m of the 15 m roll
    "kapton": (Decimal("0.2"), Decimal("33")),     # BOM.md line 33, about 0.2 m of 33 m
    "r2k2": (Decimal("2"), Decimal("25")),
    "r100": (Decimal("3"), Decimal("20")),
    "fs16": (Decimal("48"), Decimal("100")),       # 48 duck inserts. 6 of the 54 are nest.
    "pa6": (Decimal("46"), Decimal("500")),        # ORDER.md, 46.00 g of a 0.5 kg spool
}

# Board with header, CanaKit page opened this session. The ORDER.csv kit price
# buys a case, a supply, an HDMI adapter, and an OTG cable that are not incorporated.
PI_BOARD = Decimal("19.60")

# BOM.md line price for an ORDER line whose price cell is empty.
# Tuple: incorporated dollars before rounding, source note.
def d(s):
    return Decimal(s)

BOM_FALLBACK = {
    "waveshare": (d("4.99"), "BOM.md line 2, $4.99 for 1, page read 2026-11-01"),
    "sd": (d("21.25"), "BOM.md line 4, $21.25 for 1, page read 2026-11-01"),
    "button": (d("10.37"), "BOM.md line 10b, $10.37 for 1, search index 2026-11-04"),
    "xt30": (d("8.58") * d("2") / d("10"), "BOM.md line 12, $8.58 for 10 pairs, duck uses 2"),
    "foot": (d("14.70") * d("4") / d("5"), "BOM.md line 13, $14.70 for 5, duck uses 4"),
    "sg90": (d("19.99") * d("2") / d("10"), "BOM.md line 14, $19.99 for 10, duck uses 2"),
    "holder": (d("7.74") * d("2"), "BOM.md lines L3 and DK3, $7.74 each, duck uses 2"),
    "fuse15": (d("0.44"), "BOM.md line L4, $0.44 each, duck uses 1"),
    "fuse5": (d("0.44"), "BOM.md line DK4, $0.44 each, duck uses 1"),
    "bearing": (d("7.74") * d("3") / d("10"), "BOM.md line 18, $7.74 for 10, duck uses 3"),
    "vhb": (d("19.00") * d("1.2") / (d("5") * d("0.9144")), "BOM.md line 29, $19.00 for 5 yd, duck uses 1.2 m"),
    "spoxh": (d("1.43") * d("7") / d("10"), "BOM.md line 21, $1.43 for 10, duck uses 7"),
    "spoxt": (d("5.40") * d("17") / d("30"), "BOM.md line 22, $5.40 for 30, duck uses 17"),
    "kk-term": (d("2.55") * d("28") / d("30"), "BOM.md line 22b, $2.55 for 30, ORDER need 28 incorporated"),
    "wire16": (d("19.98") * d("1.3") / (d("50") * d("0.3048")), "BOM.md line L5, $19.98 for 50 ft, duck uses 1.3 m"),
    "wire20": (d("12.48") * d("2.8") / (d("50") * d("0.3048")), "BOM.md line 23, $12.48 for 50 ft, duck uses 2.8 m"),
    "wire22": (d("16.98") * d("3.6") / (d("150") * d("0.3048")), "BOM.md line 24, $16.98 for 150 ft, duck uses 3.6 m"),
    "wire26": (d("15.98") * d("12.7") / (d("175") * d("0.3048")), "BOM.md line 25, $15.98 for 175 ft, duck uses 12.7 m"),
    "shrink": (d("14.99") * d("42") / d("180"), "BOM.md line 26, $14.99 for 180, duck uses 42 sleeves"),
    "tie": (d("9.41") * d("78") / d("100"), "BOM.md line 32, $9.41 for 100. 75 on the cables plus up to 3, high end 78"),
    "mount": (d("58.00") * d("27") / d("100"), "BOM.md line 34, $58.00 for 100, 27 fitted. Spares are not incorporated"),
    "mounts": (d("72.41") * d("24") / d("100"), "BOM.md line 34b, $72.41 for 100, 24 fitted"),
    "pla": (d("29.98") * d("1346.71") / d("2000"), "BOM.md line 27, $29.98 for 2 kg. ORDER.md duck PLA 1346.71 g"),
    "tpu": (d("23.99") * d("75.1") / d("1000"), "BOM.md line 28, $23.99 for 1 kg. PRINT_PLAN.md TPU 75.1 g"),
    "speaker": (d("14.82"), "BOM.md line E1, $14.82 for 1"),
    "led": (d("6.89") * d("3") / d("10"), "BOM.md line E3, $6.89 for 10, duck uses 3"),
    "glass": (d("8.89") * d("2") / d("60"), "BOM.md line E4, $8.89 for 60, duck uses 2"),
    "reflector": (d("9.15"), "BOM.md line E5, $9.15 for 1"),
    "camcable": (d("2.94"), "BOM.md line E7, $2.94 for 1"),
    "fs17a": (d("1.98") * d("18") / d("33"), "BOM.md line 17a, $1.98 for 33, duck uses 18. 2 of the ORDER need are nest"),
    "fs17b": (d("0.84") * d("12") / d("14"), "BOM.md line 17b, $0.84 for 14, duck uses 12"),
    "fs17c": (d("0.18") * d("2") / d("3"), "BOM.md line 17c, $0.18 for 3, duck uses 2"),
    "fs17d": (d("3.83") * d("78") / d("100"), "BOM.md line 17d, $3.83 for 100, duck uses 78"),
    "fs17e": (d("1.65") * d("28") / d("33"), "BOM.md line 17e, $1.65 for 33, duck uses 28"),
    "fs17f": (d("1.80") * d("13") / d("20"), "BOM.md line 17f, $1.80 for 20, duck uses 13"),
    "fs17g": (d("0.90") * d("4") / d("10"), "BOM.md line 17g, $0.90 for 10, duck uses 4"),
    "fs17h": (d("9.49") * d("32") / d("400"), "BOM.md line 17h, $9.49 for 400 pieces, duck uses 32"),
    "fs17i": (d("0.50") * d("4") / d("5"), "BOM.md line 17i, $0.50 for 5, duck uses 4"),
    "fs17j": (d("1.08") * d("10") / d("12"), "BOM.md line 17j, $1.08 for 12, duck uses 10. 4 of the ORDER need are nest"),
    "fs17k": (d("0.60") * d("2") / d("5"), "BOM.md line 17k, $0.60 for 5, duck uses 2"),
    "fs17l": (d("3.36") * d("8") / d("48"), "BOM.md line 17l, $3.36 for 48, duck uses 8"),
}

# Bottle price is known. The amount left on the screws is not.
BOTTLE_NOT_SPLIT = {
    "loctite": "BOM.md line 19, $9.90 for the 6 mL bottle. The incorporated fraction was not measured.",
    "solder": "ORDER.csv unit $17.14 for 50 g, in stock (cited, checked 2026-11-12). Grams left in the joints were not measured.",
}

ORIGIN = {
    "reg5": (
        "domestic",
        "United States",
        "https://www.pololu.com/product/4892 opened this session. The page says the boards are manufactured in-house at the Las Vegas facility.",
    ),
    "mounts": (
        "domestic",
        "United States",
        "BOM.md line 34b records a Hisco page read 2026-11-02 that printed country of origin US. Not re-opened this session.",
    ),
    # The Seeed 7.4 V line (COO CHINA on that page) is superseded. The Waveshare
    # 12 V page cited in problems/NEST3.md did not print a country of origin.
    # Unknown origin stays foreign under 48 CFR 25.003. Do not reuse the Seeed sentence.
    "pi": (
        "foreign_cited",
        "United Kingdom or Japan",
        "https://www.canakit.com/raspberry-pi-zero-2-w.html opened this session prints Made in UK. Raspberry Pi PCN 21, opened this session, says manufacturing moved from Sony UK to Sony Inazawa, Japan, in September 2023. Neither is the United States in 48 CFR 25.003.",
    ),
}


def money(x):
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def blank(s):
    return s is None or str(s).strip() == ""


def role_of(line_id):
    if line_id in TOOLS:
        return "not_component", "tool, not incorporated"
    if line_id in PROCESS:
        return "not_component", "process aid, not an article left in the duck"
    if line_id in OUTSIDE:
        return "not_component", "stays outside the duck"
    if line_id in NEST:
        return "not_component", "nest article, not a component of the walking duck"
    return "component", "incorporated in the walking duck"


def order_unit(row):
    if blank(row["unit_price_usd"]):
        return None
    return Decimal(row["unit_price_usd"])


def incorporated_from_order(line_id, row):
    unit = order_unit(row)
    if unit is None:
        return None
    if line_id == "pi":
        return PI_BOARD, "cited, CanaKit header board $19.60 this session, sold out. ORDER.csv kit is $89.95 and is not the component cost."
    if line_id in FRACTION:
        num, den = FRACTION[line_id]
        return unit * num / den, "calc only, ORDER.csv unit times %s/%s" % (num, den)
    need = Decimal(row["need"]) if not blank(row["need"]) else None
    buy = Decimal(row["buy_qty"]) if not blank(row["buy_qty"]) else None
    pack = Decimal(row["pack_covers"]) if not blank(row["pack_covers"]) else None
    if need is None or buy is None or pack is None or buy == 0:
        return None
    pieces_per = pack / buy
    return unit * need / pieces_per, "calc only, ORDER.csv unit times need over pieces per purchase"


def main():
    rows = list(csv.DictReader(ORDER.open(encoding="utf-8")))
    out_rows = []
    domestic = Decimal("0")
    foreign = Decimal("0")
    for row in rows:
        lid = row["line_id"]
        role, why = role_of(lid)
        origin_bucket, origin, origin_src = ("not_applicable", "", "")
        price_label = ""
        inc = None
        inc_label = ""
        if role != "component":
            price_label = "not in the duck share"
        elif lid in BOTTLE_NOT_SPLIT:
            unit = order_unit(row)
            if unit is not None:
                price_label = "cited, ORDER.csv unit $%s. Incorporated fraction BLOCKER." % unit
            else:
                price_label = "cited, %s Incorporated fraction BLOCKER." % BOTTLE_NOT_SPLIT[lid]
            inc_label = "BLOCKER"
            origin_bucket = "foreign_unknown"
            origin = "unknown, counted foreign"
            origin_src = "No country-of-origin sentence was opened for this line. 48 CFR 25.003 treats components of unknown origin as foreign."
        else:
            got = incorporated_from_order(lid, row)
            if got is not None:
                inc, inc_label = got
                price_label = "cited, ORDER.csv" if lid != "pi" else inc_label
            elif lid in BOM_FALLBACK:
                inc, price_label = BOM_FALLBACK[lid]
                inc_label = "calc only from the BOM.md price in the note. Page not re-opened."
                price_label = "cited, " + price_label
            else:
                price_label = "BLOCKER"
                inc_label = "BLOCKER"
            if lid in ORIGIN:
                origin_bucket, origin, origin_src = ORIGIN[lid]
            elif role == "component":
                origin_bucket = "foreign_unknown"
                origin = "unknown, counted foreign"
                origin_src = "No country-of-origin sentence was opened for this line. 48 CFR 25.003 treats components of unknown origin as foreign."
        inc_cents = ""
        if inc is not None and role == "component" and lid not in BOTTLE_NOT_SPLIT:
            inc_cents = money(inc)
            if origin_bucket == "domestic":
                domestic += inc_cents
            else:
                foreign += inc_cents
        out_rows.append({
            "line_id": lid,
            "part": row["part"],
            "role": role,
            "why": why,
            "incorporated_usd": "" if inc_cents == "" else format(inc_cents, "f"),
            "price_label": price_label,
            "origin": origin,
            "origin_bucket": origin_bucket,
            "origin_source": origin_src,
            "order_unit_usd": row["unit_price_usd"],
            "order_line_usd": row["line_usd"],
        })

    total = domestic + foreign
    # strictly greater than 65 percent, and 75 percent
    need65 = (Decimal("0.65") * total - domestic)
    need75 = (Decimal("0.75") * total - domestic)
    # same-price conversion required so domestic exceeds the threshold
    # (D+C)/T > 0.65 => C > 0.65*T - D
    foreign_lines = [r for r in out_rows if r["incorporated_usd"] and r["origin_bucket"] != "domestic" and r["role"] == "component"]
    foreign_lines.sort(key=lambda r: Decimal(r["incorporated_usd"]), reverse=True)
    # Smallest set of lines whose costs exceed the 65 percent gap. The six largest
    # sum to less than the gap, so seven is the minimum count.
    picked = []
    running = Decimal("0")
    for r in foreign_lines:
        if running > need65:
            break
        picked.append(r)
        running += Decimal(r["incorporated_usd"])

    # Favorable reading: only cited-foreign stays foreign. Unknown priced lines count domestic.
    # Unpriced lines count as zero. This is not the rule in 25.003.
    cited_foreign = sum((Decimal(r["incorporated_usd"]) for r in out_rows if r["origin_bucket"] == "foreign_cited"), Decimal("0"))
    priced = total
    fav_d = priced - cited_foreign
    fav_share = fav_d / priced if priced else Decimal("0")

    fields = list(out_rows[0].keys())
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out_rows)

    print("rows", len(out_rows))
    print("domestic", money(domestic))
    print("foreign", money(foreign))
    print("total", money(total))
    print("share", (domestic / total * 100).quantize(Decimal("0.01")))
    print("gap65", money(need65))
    print("gap75", money(need75))
    print("favorable_domestic", money(fav_d))
    print("favorable_foreign", money(cited_foreign))
    print("favorable_share", (fav_share * 100).quantize(Decimal("0.01")))
    print("favorable_still_short65", money(Decimal("0.65") * priced - fav_d))
    print("SET")
    acc = Decimal("0")
    for r in picked:
        acc += Decimal(r["incorporated_usd"])
        print(" ", r["line_id"], r["incorporated_usd"], r["origin_bucket"], "running", money(acc))
    print("set_sum", money(acc))
    print("set_count", len(picked))
    # 2029 set
    picked75 = []
    acc = Decimal("0")
    for r in foreign_lines:
        if acc > need75:
            break
        picked75.append(r["line_id"])
        acc += Decimal(r["incorporated_usd"])
    print("set75", ",".join(picked75), "sum", money(acc))
    blockers = [r["line_id"] for r in out_rows if r["role"] == "component" and r["incorporated_usd"] == ""]
    print("component_blockers", ",".join(blockers))
    print("csv", OUT.name, "bytes", OUT.stat().st_size)


if __name__ == "__main__":
    main()
