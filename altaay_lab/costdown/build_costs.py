"""Write COSTS.csv and score.json. Prices live only in the CSV.

Every dollar is a page read, or arithmetic on those pages (label calc).
A blank unit_usd is a BLOCKER, not a guess.
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
READ = "2026-11-12"

rows = []


def add(id_, group, item, qty, unit, source, label, note, read=READ):
    fmt = "%.4f" if group == "cell_per_wh" else "%.2f"
    unit_s = "" if unit is None else fmt % unit
    line = "" if unit is None else fmt % (qty * unit)
    rows.append(dict(id=id_, group=group, item=item, qty=qty, unit_usd=unit_s, line_usd=line,
                     source_url=source, read_date=read, label=label, note=note))


# Servos read tonight.
add("seeed_c001_qty1", "servo", "Feetech STS3215 C001, Seeed, 1 to 9", 1, 20.00,
    "https://www.seeedstudio.com/STS3215-19kg-cm-7-4V-Serial-Servo-p-6338.html",
    "cited", "Page price 20.00. The 9.90 and 2.50 figures on the same page are not this servo.")
add("seeed_c001_qty10", "servo", "Feetech STS3215 C001, Seeed, 10 or more", 1, 19.00,
    "https://www.seeedstudio.com/STS3215-19kg-cm-7-4V-Serial-Servo-p-6338.html",
    "cited", "Printed break is 10 or more. No 100 and no 1000 price on the page.")
add("seeed_c001_qty100", "servo", "Feetech STS3215 C001 at 100", 100, None,
    "https://www.seeedstudio.com/STS3215-19kg-cm-7-4V-Serial-Servo-p-6338.html",
    "BLOCKER", "Page stops at 10 or more.")
add("seeed_c001_qty1000", "servo", "Feetech STS3215 C001 at 1000", 1000, None,
    "https://www.seeedstudio.com/STS3215-19kg-cm-7-4V-Serial-Servo-p-6338.html",
    "BLOCKER", "Page stops at 10 or more.")
add("waveshare_74_qty1", "servo", "Waveshare ST3215 7.4 V, 19.5 kg.cm", 1, 16.99,
    "https://www.waveshare.com/st3215-servo.htm?sku=33014",
    "cited", "SKU 33014. No printed 100 or 1000 price.")
add("waveshare_74_qty100", "servo", "Waveshare ST3215 7.4 V at 100", 100, None,
    "https://www.waveshare.com/st3215-servo.htm?sku=33014",
    "BLOCKER", "No quantity price printed.")
add("waveshare_74_qty1000", "servo", "Waveshare ST3215 7.4 V at 1000", 1000, None,
    "https://www.waveshare.com/st3215-servo.htm?sku=33014",
    "BLOCKER", "No quantity price printed.")
add("sts3250_qty1", "servo", "Feetech STS3250-C002, OpenELAB", 1, 89.00,
    "https://openelab.com/products/feetech-sts3250-c002-servo-12v",
    "cited", "Live price. The bill still has the 2026-11-01 read of 73.99. No 100 or 1000 price.")
add("sts3250_qty100", "servo", "STS3250-C002 at 100", 100, None,
    "https://openelab.com/products/feetech-sts3250-c002-servo-12v",
    "BLOCKER", "No quantity price printed.")
add("sts3250_qty1000", "servo", "STS3250-C002 at 1000", 1000, None,
    "https://openelab.com/products/feetech-sts3250-c002-servo-12v",
    "BLOCKER", "No quantity price printed.")
add("xl330_qty1", "servo", "Robotis XL330-M288-T", 1, 27.49,
    "https://robotis.us/products/dynamixel-xl330-m288-t",
    "cited", "Stall 0.52 Nm at 5 V on the same page. No quantity break.")
add("xl330_qty100", "servo", "XL330-M288-T at 100", 100, None,
    "https://robotis.us/products/dynamixel-xl330-m288-t", "BLOCKER", "No quantity price.")
add("xl330_qty1000", "servo", "XL330-M288-T at 1000", 1000, None,
    "https://robotis.us/products/dynamixel-xl330-m288-t", "BLOCKER", "No quantity price.")
add("xl430_qty1", "servo", "Robotis XL430-W250-T", 1, 27.50,
    "https://robotis.us/products/dynamixel-xl430-w250-t",
    "cited", "Stall 1.4 Nm at 11.1 V on the same page. No quantity break.")
add("xl430_qty100", "servo", "XL430-W250-T at 100", 100, None,
    "https://robotis.us/products/dynamixel-xl430-w250-t", "BLOCKER", "No quantity price.")
add("xl430_qty1000", "servo", "XL430-W250-T at 1000", 1000, None,
    "https://robotis.us/products/dynamixel-xl430-w250-t", "BLOCKER", "No quantity price.")
add("htd45_qty1", "servo", "Hiwonder HTD-45H", 1, 24.99,
    "https://www.hiwonder.com/products/htd-45h",
    "cited", "Rated 9 to 12.6 V, so not on the 7.2 V bus. No quantity break.")
add("htd45_qty100", "servo", "HTD-45H at 100", 100, None,
    "https://www.hiwonder.com/products/htd-45h", "BLOCKER", "No quantity price.")
add("htd45_qty1000", "servo", "HTD-45H at 1000", 1000, None,
    "https://www.hiwonder.com/products/htd-45h", "BLOCKER", "No quantity price.")
add("qdd_catalog_fit", "servo", "Catalog quasi-direct-drive in the 45 mm case", 1, None,
    "", "BLOCKER", "No catalog actuator in that case was opened. A custom motor is not designed here.")

# Older Feetech prices, not re-opened tonight. Kept so the comparison is not dropped.
OLD = "2026-11-01"
add("c044_seeed_20261101", "servo", "ST-3215-C044 Seeed, 1 unit, earlier read", 1, 21.99,
    "https://www.seeedstudio.com/Feetech-ST-3215-C044-Heavy-Duty-Servo-7-4V-1-191-Gear-Reduction-p-6460.html",
    "cited", "SERVO_UPGRADE_OPTIONS.md P2. Not re-opened tonight. 10 or more was 20.99 then.", read=OLD)
add("c046_seeed_20261101", "servo", "ST-3215-C046 Seeed, 1 unit, earlier read", 1, 21.99,
    "https://www.seeedstudio.com/Feetech-ST-3215-C046-Standard-Torque-Servo-7-4V-1-147-Gear-Reduction-p-6461.html",
    "cited", "SERVO_UPGRADE_OPTIONS.md P3. Not re-opened tonight. Weaker than the C001.", read=OLD)
add("c047_seeed_20261101", "servo", "STS3215 C047 12 V Seeed, 1 unit, earlier read", 1, 22.00,
    "https://www.seeedstudio.com/STS3215-30KG-Serial-Servo-p-6340.html",
    "cited", "SERVO_UPGRADE_OPTIONS.md P4. Not re-opened tonight. Too slow at 7.2 V in that study.", read=OLD)
add("st3235_waveshare_20261101", "servo", "Waveshare ST3235, 1 unit, earlier read", 1, 41.99,
    "https://www.waveshare.com/st3235-servo.htm",
    "cited", "SERVO_UPGRADE_OPTIONS.md W1. Not re-opened tonight.", read=OLD)

# Savings, calc on cited unit prices.
add("save_waveshare_12", "saving", "12 body servos, Waveshare 7.4 V instead of Seeed 10 or more", 1,
    round(12 * (19.00 - 16.99), 2),
    "seeed_c001_qty10 and waveshare_74_qty1",
    "calc", "12 times (19.00 minus 16.99). Backlash of the Waveshare unit was not on the page.")
add("save_drop_sts3250_knees", "saving", "Replace two live STS3250 with two Seeed C001 at the 10 or more price", 1,
    round(2 * (89.00 - 19.00), 2),
    "sts3250_qty1 and seeed_c001_qty10",
    "calc", "Dollar cut only. The C001 stall is under the sim knee torque. Not a recommended cut.")
add("knee_pair_live_vs_bill", "saving", "Two STS3250 tonight versus the bill figure from 2026-11-01", 1,
    round(2 * 89.00 - 147.98, 2),
    "sts3250_qty1",
    "calc", "Positive means the live pair costs more than BOM line 1b (73.99 times 2). Not a saving.")

# Cells. Unit price is one cell. line_usd for qty 2 is the pack.
add("p45b_cell", "cell", "Molicel P45B 21700, one cell", 1, 9.99,
    "https://www.18650batterystore.com/collections/21700-batteries",
    "cited", "Sold out on that page tonight. Sheet re-opened: 4.5 Ah typical, 16.2 Wh, 70 g, 45 A, 15 mOhm.")
add("p50b_cell", "cell", "Molicel P50B 21700, one cell", 1, 11.99,
    "https://www.18650batterystore.com/collections/21700-batteries",
    "cited", "In stock tonight. 5.0 Ah and 60 A are the store title. Sheet figures are the 2026-11-04 read in BATTERY_STUDY.md, not re-opened tonight.")
add("s50s_cell", "cell", "Samsung 50S 21700, one cell", 1, 9.99,
    "https://www.18650batterystore.com/collections/21700-batteries",
    "cited", "In stock tonight. Store title 5000 mAh 25 A. Sheet was not re-opened tonight.")
add("s40t_cell", "cell", "Samsung 40T 21700, one cell", 1, 6.99,
    "https://www.18650batterystore.com/collections/21700-batteries",
    "cited", "Sold out tonight. Store title 4000 mAh 35 A. Mass and resistance still unread.")
add("vtc6_cell", "cell", "Sony Murata VTC6 18650, one cell", 1, 7.99,
    "https://www.18650batterystore.com/collections/18650-batteries",
    "cited", "In stock tonight. Store title 3000 mAh 15 A.")
add("lg_m50_cell", "cell", "LG INR21700-M50, one cell", 1, None,
    "https://www.dnkpower.com/wp-content/uploads/2019/02/LG-INR21700-M50-Datasheet.pdf",
    "BLOCKER", "Sheet opened tonight. Store page tried returned 404. No price.")
add("lipo_pack", "cell", "2S LiPo pack that fits the grown bay", 1, None,
    "", "BLOCKER", "No pack with a size inside the grown bay was opened.")
add("lfp_cell", "cell", "LiFePO4 cell in this bay", 1, None,
    "", "BLOCKER", "No LiFePO4 sheet was opened. The duck charger is set to 8.40 V.")

# Cost per Wh, one cell, calc.
def wh_row(id_, item, price, wh, source):
    add(id_, "cell_per_wh", item, 1, round(price / wh, 4) if price else None, source,
        "calc" if price else "BLOCKER", "unit_usd here is dollars per Wh, not dollars per cell. Wh is %s." % wh)

wh_row("p45b_per_wh", "P45B dollars per Wh", 9.99, 16.2, "p45b_cell and the P45B sheet 16.2 Wh")
wh_row("p50b_per_wh", "P50B dollars per Wh", 11.99, 18.0, "p50b_cell and BATTERY_STUDY.md 18.0 Wh")
wh_row("s50s_per_wh", "50S dollars per Wh", 9.99, 18.0, "s50s_cell and BATTERY_STUDY.md 18.0 Wh")
wh_row("s40t_per_wh", "40T dollars per Wh", 6.99, 14.4, "s40t_cell and BATTERY_STUDY.md 14.4 Wh")
wh_row("vtc6_per_wh", "VTC6 dollars per Wh", 7.99, 11.232, "vtc6_cell. 3.12 Ah times 3.6 V from the earlier Murata read.")
wh_row("lg_m50_per_wh", "M50 dollars per Wh", None, 18.2, "lg_m50_cell")

# Electronics and print. Bill prices not re-opened tonight stay dated.
add("pi_zero2w_adafruit", "compute", "Raspberry Pi Zero 2 W, Adafruit 5291", 1, 19.05,
    "https://www.adafruit.com/product/5291",
    "cited", "BOM line 3. Out of stock when read. Not re-opened tonight.", read=OLD)
add("pi_cheaper_runtime", "compute", "A cheaper board that runs the existing runtime", 1, None,
    "", "BLOCKER", "No such board was opened. The runtime stays on the Pi already chosen (D7).")
add("bec_pro", "power", "Castle CC BEC Pro", 1, 54.95,
    "https://www.horizonhobby.com/product/castle-creations-cc-bec-pro-20a-max-output-12s-max-switching-regulator/CSE010000401.html",
    "cited", "BOM line L1, read 2026-11-01. Not re-opened tonight. POWER.md already compared other bucks.", read=OLD)
add("adapter_a", "power", "Waveshare Bus Servo Adapter A", 1, 4.99,
    "https://www.waveshare.com/bus-servo-adapter-a.htm",
    "cited", "BOM line 2. Not re-opened tonight.", read=OLD)
add("merged_board_qty1", "power", "One board merging charger, servo bus, and the BEC", 1, None,
    "", "BLOCKER", "The charger schematic exists. No board house quoted a merged board.")
add("merged_board_qty100", "power", "Merged board at 100", 100, None, "", "BLOCKER", "No quote.")
add("merged_board_qty1000", "power", "Merged board at 1000", 1000, None, "", "BLOCKER", "No quote.")
add("pla_spool", "print", "Overture Easy PLA 1 kg", 1, 29.98,
    "https://www.amazon.com/dp/B09LCK7QJ2",
    "cited", "BOM line 27. Not re-opened tonight. Print plan needs 1407.2 g, so two spools.", read=OLD)
add("pla_two_spools", "print", "Two PLA spools, one duck, qty-1 price", 2, 29.98,
    "pla_spool", "calc", "No volume price was opened. 100 and 1000 ducks are this unit price times the count, not a discount.")
add("mold_start", "print", "Protolabs injection mold, starting price, one tool", 1, 1495.00,
    "https://www.protolabs.com/help-center/pricing-and-payment-options/",
    "cited", "Page sentence: prices start around 1495, depending on geometry. Not a quote for these parts.")
add("mold_vs_print_1000", "print", "49 print files times the mold start, minus filament for 1000 ducks", 1,
    None, "mold_start and pla_two_spools", "BLOCKER",
    "See note in ELECTRONICS.md. The bound is computed in score.json. Plastic piece price was not quoted, so a saving is not claimed.")

# Battery score. Weights are this study's choice, written in BATTERY.md.
# peak bar 20.6 A is BATTERY_STUDY.md section 8, sim pass only there.
PEAK = 20.6
cells = [
    dict(id="P45B", i=45.0, wh=32.4, g=140.0, usd=9.99 * 2, wh_cell=16.2, gate=True, cycle=None),
    dict(id="P50B", i=60.0, wh=36.0, g=142.0, usd=11.99 * 2, wh_cell=18.0, gate=True, cycle=None),
    dict(id="50S", i=25.0, wh=36.0, g=144.0, usd=9.99 * 2, wh_cell=18.0, gate=True, cycle=None),
    dict(id="40T", i=35.0, wh=28.8, g=None, usd=6.99 * 2, wh_cell=14.4, gate=False, cycle=None),
    dict(id="VTC6", i=15.0, wh=22.464, g=93.2, usd=7.99 * 2, wh_cell=11.232, gate=False, cycle=None),
    dict(id="M50", i=7.275, wh=36.4, g=136.0, usd=None, wh_cell=18.2, gate=False, cycle=500),
]
priced = [c for c in cells if c["usd"] is not None and c["wh_cell"]]
best_per = min(c["usd"] / c["wh"] for c in priced)  # pack dollars per pack Wh
max_wh = max(c["wh"] for c in cells)
passers = [c for c in cells if c["gate"] and c["g"] is not None]
light = min(c["g"] for c in passers)
W = dict(safety=25, peak=20, runtime=15, mass=10, cycle=10, cost=10, ship=5)
scored = []
for c in cells:
    per = None if c["usd"] is None else c["usd"] / c["wh"]
    pts = dict(
        safety=W["safety"],  # every scored cell is a metal-can Li-ion; pouches were not opened
        peak=round(min(1.0, (c["i"] / PEAK) / 2.0) * W["peak"], 2),
        runtime=round(c["wh"] / max_wh * W["runtime"], 2),
        mass=0 if c["g"] is None else round(min(W["mass"], light / c["g"] * W["mass"]), 2),
        cycle=0 if c["cycle"] is None else W["cycle"],
        cost=0 if per is None else round(best_per / per * W["cost"], 2),
        ship=W["ship"],  # every pack here is under 100 Wh
    )
    total = round(sum(pts.values()), 2)
    scored.append(dict(id=c["id"], points=pts, total=total, gate=c["gate"],
                       cycle_known=c["cycle"] is not None))

# Mold bound as a duck count only. The dollars stay in COSTS.csv.
N_FILES = 49
ducks_if_plastic_free = (N_FILES * 1495.0) / (2 * 29.98)
bound = dict(print_files=N_FILES,
             ducks_to_match_filament_if_plastic_free=round(ducks_if_plastic_free, 1),
             note="Calc only. 49 files under print/ times the mold start, divided by two spools. Plastic piece price was not quoted. 49 files are not 49 tools. Not a saving.")

score = dict(weights=W, peak_A=PEAK, peak_source="BATTERY_STUDY.md section 8, their shove figure",
             rule="A cell with a BLOCKER, or under the peak bar, does not win. A lead under 5 points is not a clear win.",
             cells=scored, mold_bound=bound)

path = os.path.join(HERE, "COSTS.csv")
with open(path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
json.dump(score, open(os.path.join(HERE, "score.json"), "w"), indent=1)
print("rows", len(rows))
for s in scored:
    print(s["id"], s["total"], s["points"], "gate", s["gate"])
print("mold ducks", bound["ducks_to_match_filament_if_plastic_free"])
