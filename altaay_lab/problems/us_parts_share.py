#!/usr/bin/env python3
"""Roll up the US-parts study from the worksheet rows and the judgments below.

Reads altaay_lab/compliance/DOMESTIC_ROWS.csv. Writes altaay_lab/problems/US_PARTS.csv.
Prints the share scenarios. This is arithmetic on cited prices. It is not legal advice.

Run from the repo root:
  python3 altaay_lab/problems/us_parts_share.py
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROWS = HERE.parent / "compliance" / "DOMESTIC_ROWS.csv"
OUT = HERE / "US_PARTS.csv"
CENT = Decimal("0.01")

# result, us_candidate, why, us_incorporated (blank if not a pass), buy_url, evidence_url, twin
# A pass is a US-made part that meets the printed specs of the current line.
J = {}


def add(line, result, candidate, why, us_inc="", buy="", evidence="", twin=""):
    J[line] = {
        "result": result,
        "us_candidate": candidate,
        "why": why,
        "us_incorporated_usd": us_inc,
        "buy_url": buy,
        "evidence_url": evidence,
        "twin_followup": twin,
    }


add(
    "pla",
    "pass",
    "3DXTech ECOMAX PLA, 1.75 mm, two 1 kg spools",
    "Pass on the specs the current line prints: PLA, 1.75 mm, nozzle 210 C inside the Overture 190 to 220 C window. "
    "The maker page says the filament is made in the USA at the Grand Rapids, Michigan plant, from NatureWorks virgin resin. "
    "A data-sheet page that says its figures come from the manufacturer prints tensile strength 56 MPa and modulus 2865 MPa (ISO 527). "
    "Overture Easy PLA does not print a tensile number in BOM.md, so 56 MPa is not a beat of a published Overture tensile. "
    "Bed recommendation on that data-sheet page is 23 C, against the Overture bed window 25 to 60 C. That is a start setting, not a limit of the resin. "
    "Price is $36.00 a spool (cited). Two spools are $72.00 (calc only). The share uses the same full-spool basis as the current pla row, not the printed grams.",
    "72.00",
    "https://www.3dxtech.com/products/ecomax-r-pla",
    "https://www.spoolscout.com/data-sheets/3dxtech/pla-ecomax-pla",
    "No actuator change and no retrain. A re-slice is the follow-up if the 1.24 g/cm3 density changes the grams. Do not change the selected PLA in this study.",
)

add(
    "servo",
    "fail",
    "none",
    "No US-made serial-bus servo was found that meets 30 kg.cm at 12 V, 0.222 s/60 deg, 45.2 x 24.7 x 35 mm, the 25T spline, and half-duplex TTL with 4096 counts. "
    "ProModeler DS270DLHV is $54.99 and 270 oz-in, which is 19.44 kg.cm (calc only), under 30 kg.cm. The DL series text on that page tops out at 360 oz-in, which is 25.92 kg.cm (calc only). The page does not print a US factory sentence or a serial bus. "
    "GearWurx Mini-Torxis is $79.99, 700 oz-in (4.9 N.m on the page) and 0.13 s per 60 deg, and it fails the bus (PWM), the travel (180 deg), and the mass (158 g against 55 g). The page does not print a country of origin. "
    "Teknic describes itself as a US manufacturer in Victor, NY, and ClearPath models start at $249. The user manual lists the smallest frame as NEMA 23 with a body length code of 82 mm. That is not this pocket, and the command is step or Teknic software, not the Feetech bus. "
    "Glentek says it manufactures in El Segundo, California. The small GMB2005-8 continuous torque on the category page is 0.27 Nm, under 2.942 Nm, and no catalog price was printed. "
    "The Feetech page footer prints a Shenzhen address. Not a pass.",
    "",
    "",
    "https://www.feetech.cn/en/525603",
    "Any real swap changes mass, the torque curve, the case, the spline, and the bus. Run C would have to be trained again. Not done here.",
)

add(
    "bec",
    "fail",
    "Pololu D42V110F12, considered and rejected",
    "Castle page: 20 A peak, continuous 15 A at 16 V input, output adjustable 4.9 V to 12.5 V, input up to 12S (50.4 V). The same page says the product is designed in Olathe, Kansas. It does not say manufactured there. Designed is not the manufacture sentence the worksheet uses, so the line stays unknown and foreign. "
    "Pololu D42V110F12 is made in Las Vegas (the page says so) at $69.95, fixed 12 V, typical maximum about 9 A, input 12 V to 60 V. It misses the 20 A peak, the adjustable 4.9 V to 12.5 V window, and a 3S pack that sags under 12 V. Run C pack peak is 15.6 A (sim pass only, problems/PROBLEMS.md). Not a pass.",
    "",
    "https://www.pololu.com/product/5677",
    "https://castlecreations.com/products/voltage-regulator-cc-bec-pro-20a-010-0004-01",
    "A lower-current regulator changes the servo rail and the walk. Not a BOM change.",
)

add(
    "cell",
    "fail",
    "none",
    "No catalog 21700 made in the United States was opened with the P45B class the lab already cites: about 4.5 Ah, charge to 4.20 V, high discharge, 21.4 mm by 70 mm, 70 g. "
    "The Molicel sheet named in DOMESTIC_CONTENT.md prints a Canada facility and a Taiwan facility, not a United States factory. A US shop selling a Lishen cell is a seller, not a US factory. Not a pass.",
    "",
    "",
    "https://www.molicel.com/wp-content/uploads/INR21700P45B_1.2_Product-Data-Sheet-of-INR-21700-P45B-80109.pdf",
    "A different cell changes mass, sag, and the charge window. The 3S pack and run C stay as they are.",
)

add(
    "pi",
    "fail",
    "none",
    "No US-made board was opened that runs the same Pi software, the CSI camera, and this GPIO map. The worksheet already counts the Zero 2 W as United Kingdom or Japan. A different computer is a new design, not an equivalent. Not a pass.",
    "",
    "",
    "https://pip-assets.raspberrypi.com/categories/1163-pcn/documents/RP-004862-PC-1-PCN21,%20Raspberry%20Pi%20Zero%202%20W,%20Change%20of%20country%20of%20origin.pdf",
    "A board swap is a new computer and a new policy runtime. Not done here.",
)

add(
    "cam",
    "fail",
    "none",
    "The line is the Raspberry Pi Camera Module 3 on the Pi CSI port (wiring harness). No US-made module with that connector and equal sensor performance was opened. Not a pass.",
    "",
    "",
    "https://www.adafruit.com/product/5657",
    "A different camera changes the CSI cable and the dock vision path. Not done here.",
)

add(
    "imu",
    "fail",
    "none",
    "The breakout is the BNO055 on I2C, used for fused orientation (wiring and the freeze notes). No US-made BNO055 board with a manufacture sentence was opened. An industrial IMU on another bus would drop the current reader. Not a pass.",
    "",
    "",
    "https://www.adafruit.com/product/2472",
    "A different IMU is a new driver and a new orientation frame. Not done here.",
)

add(
    "bms",
    "fail",
    "none",
    "The billed board is a 2S protection board. The walking pack is 3S (problems/STS12.md, problems/NEST3.md). A US-made 2S board would still be the wrong series count. No US 3S board with a matching trip current and a manufacture sentence was opened. Not a pass.",
    "",
    "",
    "https://power.tenergy.com/protection-circuit-module-pcb-for-7-2v-7-4v-2s-li-ion-battery-pack-working-10a-cutoff-22a-ntc",
    "The 3S protection board is already an open design item. This study does not pick one.",
)

add(
    "pa6",
    "fail",
    "none",
    "The shin allowable is the Bambu PA6-CF sheet already cited in twin/structure/shin_eye/SHIN_EYE.md: tensile 102 MPa in X-Y and 48 MPa in Z, modulus 4430 MPa. No US-made PA6-CF page was opened that prints all three at or above those figures. A weaker nylon would miss the shin margins. Not a pass.",
    "",
    "",
    "",
    "Do not swap the shin filament without those three numbers and a new coupon.",
)

add(
    "tpu",
    "fail",
    "none",
    "Overture TPU on the bill is 95A, nozzle 210 to 240 C (BOM.md line 28). No US-compounded 95A TPU page with shore, nozzle, and a price was opened. A softer shore would change the soles and the sit pads. Not a pass.",
    "",
    "",
    "",
    "Shore hardness feeds the foot and the sit pads. No swap.",
)

WIRE_WHY = (
    "BNTECHGO silicone is the current reel. Calmont publishes silicone cable and a high-temperature construction, and the company is a US wire maker, "
    "but no priced reel in 16, 20, 22, or 26 AWG with a matching strand, a 200 C class, and a country sentence was opened. Not a pass."
)
for w in ("wire16", "wire20", "wire22", "wire26"):
    add(w, "fail", "none", WIRE_WHY, "", "", "https://www.calmont.com/resources/silicone/", "Wire gauge stays as drawn. No swap.")

FAMILY = (
    "No United States datasheet and country-of-origin sentence for an equivalent of this line was opened. "
    "The worksheet already counts unknown origin as foreign. This study does not pass the line."
)


def money(x):
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def dec(s):
    if s is None or str(s).strip() == "":
        return None
    return Decimal(str(s))


def main():
    src = list(csv.DictReader(ROWS.open(encoding="utf-8")))
    out = []
    for row in src:
        lid = row["line_id"]
        inc = dec(row["incorporated_usd"])
        role = row["role"]
        origin = row["origin_bucket"]
        if lid in J:
            jud = J[lid]
        elif role != "component":
            jud = {
                "result": "not_in_share",
                "us_candidate": "",
                "why": "Not a component of the walking duck on the worksheet (tool, nest, process aid, or the controller). Left out of the share.",
                "us_incorporated_usd": "",
                "buy_url": "",
                "evidence_url": "",
                "twin_followup": "",
            }
        elif inc is None:
            jud = {
                "result": "unpriced",
                "us_candidate": "",
                "why": "Incorporated cost is BLOCKER on the worksheet, so the line is not in the 5.23 percent. No priced US substitute was opened.",
                "us_incorporated_usd": "",
                "buy_url": "",
                "evidence_url": "",
                "twin_followup": "",
            }
        elif origin == "domestic":
            jud = {
                "result": "already_domestic",
                "us_candidate": "current part",
                "why": "The worksheet already counts this line as United States. No swap.",
                "us_incorporated_usd": format(inc, "f"),
                "buy_url": "",
                "evidence_url": row["origin_source"],
                "twin_followup": "",
            }
        else:
            jud = {
                "result": "fail",
                "us_candidate": "none",
                "why": FAMILY,
                "us_incorporated_usd": "",
                "buy_url": "",
                "evidence_url": "",
                "twin_followup": "",
            }
        out.append({
            "line_id": lid,
            "part": row["part"],
            "role": role,
            "incorporated_usd": row["incorporated_usd"],
            "origin_now": origin,
            "result": jud["result"],
            "us_candidate": jud["us_candidate"],
            "why": jud["why"],
            "us_incorporated_usd": jud["us_incorporated_usd"],
            "price_delta_usd": "",
            "buy_url": jud["buy_url"],
            "evidence_url": jud["evidence_url"],
            "twin_followup": jud["twin_followup"],
        })

    domestic = Decimal("0")
    foreign = Decimal("0")
    passes = []
    for r in out:
        if r["role"] != "component" or r["incorporated_usd"] == "":
            continue
        inc = Decimal(r["incorporated_usd"])
        if r["origin_now"] == "domestic":
            domestic += inc
        else:
            foreign += inc
        if r["result"] == "pass":
            passes.append(r)
            old = inc
            new = Decimal(r["us_incorporated_usd"])
            r["price_delta_usd"] = format(money(new - old), "f")

    # Baseline must match the worksheet the study builds on.
    base_d, base_f, base_t = money(domestic), money(foreign), money(domestic + foreign)
    if (base_d, base_f, base_t) != (Decimal("47.33"), Decimal("858.03"), Decimal("905.36")):
        raise SystemExit("baseline drifted: %s %s %s" % (base_d, base_f, base_t))

    d2, f2 = domestic, foreign
    for r in passes:
        old = Decimal(r["incorporated_usd"])
        new = Decimal(r["us_incorporated_usd"])
        f2 -= old
        d2 += new
    t2 = d2 + f2

    fields = list(out[0].keys())
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out)

    counts = {}
    for r in out:
        counts[r["result"]] = counts.get(r["result"], 0) + 1

    print("baseline_domestic", base_d)
    print("baseline_foreign", base_f)
    print("baseline_total", base_t)
    print("baseline_share", money(domestic / (domestic + foreign) * 100))
    print("pass_count", len(passes), ",".join(r["line_id"] for r in passes))
    print("allpass_domestic", money(d2))
    print("allpass_foreign", money(f2))
    print("allpass_total", money(t2))
    print("allpass_share", money(d2 / t2 * 100))
    print("allpass_per_duck_parts", "957.75")
    print("allpass_buy_today", money(Decimal("1204.26") - Decimal("35.98") + Decimal("72.00")))
    print("set65", "none")
    print("set75", "none")
    print("counts", " ".join("%s=%d" % (k, counts[k]) for k in sorted(counts)))
    print("csv_bytes", OUT.stat().st_size)


if __name__ == "__main__":
    main()
