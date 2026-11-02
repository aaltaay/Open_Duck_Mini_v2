# VIEWER_NOTE: drawing the fasteners in the exploded view

Source: `altaay_lab/fasteners/fasteners.json` (written by make_fasteners.py, sweep_fasteners.py and report_fasteners.py). Units mm. Same scene as viewer/make_viewer_data.py: robot.urdf at zero joint angles, URDF world frame (x forward, y left, z up), print/ STLs, head internals in the head.stl frame.

## Which records
- `fasteners[]`, one per instance. `kind` is `screw` or `insert`.
- Skip or ghost `status == "NOT FITTED"`: 11 idle-horn screws that stay in the servo bag.
- Ghost in red `status == "LEAVE OUT (D18)"`: the 2 hip roll screws left out by D18.
- `source == "servo_case"`: the 56 factory case screws inside the servos. Draw them as part of the servo, or hide them with the servo.

## Where to draw
- `link`: the URDF link the fastener rides on. Horn screws ride on the part screwed to the horn. The URDF puts the horns on the servo body link, so a horn moves with that part's link.
- `pose_link`: 4x4, row-major, in the frame of `link` at zero pose. Origin is the head seat (the underside of the head). Local +z is the screw axis, pointing into the joint.
  - World pose for joint angles q: `T_link(q) @ pose_link`, with T_link from yourdfpy and translations x1000.
  - At the zero pose, `seat_world` and `axis_world` give the same answer directly.
- Explode: `viewer_sub` is the subassembly id that viewer/LINK_SUB uses, so use the same level-1 vector as the parts. For a level-3 pull, move the screw out along -z of `pose_link`. The viewer uses 11 mm for inserts.

## What to draw (local frame of pose_link)
- Screw shank: a cylinder of diameter `d`, from z = 0 to z = `draw_length_mm`.
  - `length_mm` is the stock length.
  - `length_mm` is null where no length is published: factory case screws, SG90 bag screws. Then `draw_length_mm` is a stand-in.
- Head: a cylinder of diameter `head.dk` and height `head.k`, from z = -`head.k` to z = 0.
  - If `washer` is present (eye screws), move the head out by `washer.t`.
  - `head.type` names the model in `meta.head_models`.
- Insert: a brass cylinder of diameter 4.6 (`d`) and length 5.7, from z = 0 to z = 5.7. Origin is the bore entry, flush with the part face; +z points into the bore. `screw` names the screw that ends in it.

## Colour
- `color` is a hex string set by `color_key` (the spec family).
- `meta.colors` is the legend. Use the counts from the records, without the NOT FITTED ones.

## Tooltip fields
- `spec`, `supply` (BOM line or bag), `part` and `into` (the joined parts), `anchor`.
- `near` / `far`: where the anchor starts and ends, measured from the seat.
- `stop`: the first solid surface on the screw axis.
- `e`, `e_min`, `len_status`: thread engaged against the rule.
- `clearance`, `recess_check`.
- `sweep.status` and `sweep.worst_text`: HIT, NEAR, CLEAR, CONTACT, or PARTS COLLIDE FIRST.
- `notes`.

## Joined parts as viewer nodes
`part_inst` and `into_inst` index the robot.urdf visuals in link_map order. That is the same order as audit/assembly.json and make_viewer_data.py `inst`. Indices 131 to 138 are the head internals, in the order of fastlib.HEAD_INTERNALS. `into_inst` is null for camera PCB screws (the camera is a placeholder).

## Inserts already in the viewer
make_viewer_data.py draws 58 inserts from audit/sites.json. Those holes come from the URDF meshes, while the inserts here come from the print/ STLs. The 58 positions match, except that the head comes from print/head.stl here. Draw the fasteners.json inserts, or keep the viewer's, but not both.

## Holes left empty
`empty_holes[]` lists every hole stack that has no fastener, with the reason. To show these, draw a ring at `at` along `axis`.
