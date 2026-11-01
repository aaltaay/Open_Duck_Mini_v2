import json
R=json.load(open('bom.json'))
o=["# BOM (final, end to end)","","Last updated: 2026-11-01 2:10 PM ET. Prices read on supplier pages 2026-11-01, before shipping and tax. Nothing purchased.","",
"Rules: every quantity comes from CAD/STL measurement (HARDWARE_AUDIT.md, PRINT_CHECK.md, CABLE_MAP.md, MOUNTING.md) or a cited source. Anything that could not be verified is marked BLOCKER with what is needed. Spares are 10 to 20% or the pack minimum, whichever is larger.","",
"Columns: Need = measured requirement; Buy = what to order; Line = price for the Buy quantity.",""]
secs=[]
for x in R:
    if x['sec'] not in secs: secs.append(x['sec'])
tot={}
for s in secs:
    o+=["## "+s,"","| # | Item | Spec | Need | Buy | Pack | Line $ | Supplier | Link | Ships to USA | Verified |","|---|---|---|---|---|---|---|---|---|---|---|"]
    t=0
    for x in R:
        if x['sec']!=s: continue
        t+=float(x['line'])
        o.append(f"| {x['i']} | {x['item']} | {x['spec']} | {x['need']} | {x['buy']} | {x['pack']} | {x['line']} | {x['sup']} | {x['link']} | {x['ships']} | {x['ver']} |")
    tot[s]=t; o+=["",f"Subtotal: ${t:.2f}",""]
core=sum(tot[s] for s in secs[:4])
o+=["## Totals","","| Scope | $ |","|---|---|"]
for s in secs: o.append(f"| {s} | {tot[s]:.2f} |")
o+=[f"| Build total (robot + fasteners + cables + filament) | {core:.2f} |",
f"| Build + expression pack | {core+tot[secs[4]]:.2f} |",
f"| Build + expression + tools | {core+tot[secs[4]]+tot[secs[5]]:.2f} |","",
"Previous BOM (before this audit): core $684.99, grand $730.94 with lab changes. The build total now adds fasteners, inserts, bearings, filament, wire, connectors and heat shrink that were missing or unverified, and moves the Castle Link to Tools.","",
"Not costed (not verified, BLOCKER for exact cost): shipping and order minimums (Bolt Depot, Mouser, DigiKey, CNC Kitchen), sales tax, a USB-C PD supply for the Pinecil, a 16 to 20 AWG stripper, a multimeter, digital calipers, a heat gun or lighter for heat shrink.","",
"## Contingency (not in totals)","",
"| # | Item | Qty | $ | Trigger |","|---|---|---|---|---|",
"| X1 | Extra Molex 50-37-5033 housings (Mouser $0.14) | 20 | 2.80 | Kit 15 cm servo cables too short on test fit (CABLE_MAP S-hops) |",
"| X2 | Extra Molex 08-70-1040 terminals (Mouser $0.23) | 60 | 13.80 | Same as X1 (10 made leads at 22 AWG) |",
"| X3 | 1 m Micro-B to USB-C cable | 1 | not priced | USB route W12 longer than 50 cm on test fit |","",
"## Removed from the previous BOM","",
"- Barrel jack lead (old row 12): the lab build feeds the adapter through its screw terminal H1, so 0 needed.",
"- Braided cable sheath (old row 21): not required by any measured route; price was unverified. Dropped.",
"- Adafruit 4646 BNO055: replaced by 2472 because 4646 holes do not match the CAD pilots (MOUNTING.md).",
"- Castle Link V4 moved to Tools.","",
"## BLOCKERS that affect this BOM","",
"See HARDWARE_AUDIT.md section 6 for the full list with what is needed to clear each one."]
for x in R:
    if 'BLOCKER' in x['ver'] or ' NO' in x['ver'] or x['ver'].startswith('NO'):
        o.append(f"- {x['i']} {x['item']}: {x['ver']}")
open('/workspace/lab_push/altaay_lab/BOM.md','w').write("\n".join(o)+"\n")
print(core)
