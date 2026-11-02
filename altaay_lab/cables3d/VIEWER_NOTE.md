# VIEWER_NOTE: drawing the cables per link

For altaay_lab/viewer/make_viewer_data.py and the exploded parts-check page. Data: altaay_lab/cables3d/cables3d.json.

## Points
- Every point is `{link, p}`: `p` is in mm in the frame of URDF link `link` (yourdfpy link transform with the
  translation x1000), taken at the zero pose. World at any pose: `T_link(q) @ [p, 1]`. The current loader does this.
- `world0` (in route_cables output only) is the same point in URDF world at the zero pose, for checking.
- Consecutive points on the same link are a fixed piece: they move with that link (exploded view: with its subassembly,
  `LINK_SUB[link]`). Consecutive points on different links are a free span across the joint(s) between the two links:
  draw a straight tube between the two moved points (it stretches when the subassemblies explode apart). This is the
  service loop; its real shape is a loose arc, its taut length is in `runs[].spans[]`.

## What to draw
- `cables[].points` is the main run only (kept for the current loader). Branches are in `cables[].runs[]`
  (SD1 stem/a/b and tails, P7 line/load, P11 leads/main, SP1 to SP3 main/tail, D3 and D4 main/jumper, D7 main/channel).
  Draw every run. Suggested loader change, after the `pts` loop in `load_cables3d`:
  `runs = [[(q["link"], q["p"], None) for q in r["points"]] for r in c.get("runs", [])] or [pts]`, then one tube per
  run with that run's `d_mm`.
- Tube diameter: `runs[].d_mm` (bundle estimate, hexagonal packing [L]). For visibility the PNGs draw 1.4 x, at least
  2.4 mm.
- Colours: `cables[].colors` is one hex colour per conductor in netlist order (red, black, yellow, ...); `color` is the
  first. Kit servo cables are `#b8c4cc` (their real colours are not published). A multi-conductor run can be drawn as
  one thin tube per conductor around the centreline (render_cables.py, `c3d_lib.bundle_tubes`).
- Status: `check` is one of "pass", "pass with notes", "fail"; reasons in `findings`; numbers in `length_*_mm`,
  `cut_mm`, `worst_mm`, `required_mm`, `margin_mm`.

## Ties, seats and seated parts
- `retention[]`: one visible part each. `center_mm` is world at the zero pose; `p` is the same point in `link`'s frame
  (move it with that link). `axis` is the cable direction: draw a ring of diameter `bundle_d_mm` + 1.6 mm around it.
  `kind` is "existing printed feature", "adhesive tie mount" or "cable tie"; `gap` is true when the stock CAD has no
  anchor there (stick-on mount proposed, or a free-air bundle tie). `tie` names the tie size for the BOM count.
- `cables[].seats[]` and `runs[].seats[]`: where the cable meets a printed part (hole, channel, edge, none) with
  `center_mm`, `axis`, `part`, `point_index` into that run's points.
- `terminals[]`: the six parts seated by this work (xt30, amp, speaker, led_1, led_2, led_3): `center_mm`,
  `dims_xyz_mm`, `link`, `how`. `cable_ends[]`: every cable end with `p` in its link frame.

## Rebuild
`python3 altaay_lab/cables3d/route_cables.py --scratch <dir>`, then `seats_ties.py`, `check_cables.py --scratch <dir>`,
`make_report.py "<time>"`. Every write of cables3d.json is atomic (temp file, then rename).
