#!/bin/bash
# Re-slice before and after with the repo's slice.py (PrusaSlicer 2.7.2, D22 light profile), in a SCRATCH worktree
# (it overwrites print/ there). Env: WT (scratch worktree root, default: this repo), ODM_HOLES_OUT (outputs of
# close_holes.py, default ~/v1_out/holes), RAMCAP (ramcap.py of the shared lab gym (overlay gym/overlays/duck)).
set -e
: "${RAMCAP:?set RAMCAP to ramcap.py of the shared lab gym (overlay gym/overlays/duck)}"
HERE=$(cd "$(dirname "$0")" && pwd)
WT=${WT:-$(cd "$HERE/../../.." && pwd)}; P=$WT/print
OUT=${ODM_HOLES_OUT:-$HOME/v1_out/holes}; O=$OUT/slice; ST=$OUT/stl
TW=$WT/altaay_lab/twin/screws/stl
RAM="python3 $RAMCAP --cap-mb 7000"
export ODM_SLICER_THREADS=2
LIST=battery_pack_lid.stl,body_back.stl,body_front.stl,body_middle_bottom.stl,body_middle_top.stl,bulb.stl,flash_light_module.stl,head.stl,head_bot_sheet.stl,left_eye.stl,leg_spacer.stl,neck_right_sheet.stl,right_eye.stl,speaker_interface.stl,speaker_stand.stl,trunk_top.stl,roll_motor_bottom.stl
TWL=body_front.stl,body_middle_top.stl,body_middle_bottom.stl
mkdir -p $O/orig_print && cp -n $P/*.stl $O/orig_print/
cd $WT/altaay_lab/print
run() { $RAM --peak-json $O/peak_$1.json -- nice -n 10 python3 slice.py parts --out $O/$1 --only $2 --jobs 2 > $O/$1.log 2>&1; }
run before $LIST
cp $TW/body_front_groove.stl $P/body_front.stl; cp $TW/body_middle_top_lip.stl $P/body_middle_top.stl; cp $TW/body_middle_bottom_lip.stl $P/body_middle_bottom.stl
run twin_before $TWL
cp $ST/body_front_groove.stl $P/body_front.stl; cp $ST/body_middle_top_lip.stl $P/body_middle_top.stl; cp $ST/body_middle_bottom_lip.stl $P/body_middle_bottom.stl
run twin_after $TWL
for f in ${LIST//,/ }; do n=${f%.stl}; [ -f $ST/$n.stl ] && cp $ST/$n.stl $P/$f; done
run after $LIST
echo SLICE_DONE
