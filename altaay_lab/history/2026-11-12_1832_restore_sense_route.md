# 2026-11-12 6:32 PM ET: the sense-to-bead route is back

The 158 lines taken out of cables3d.json were one route, DC3 run r1, from the splice JSN.S to the bead pin RT1.1. The points, the 179.4 mm length, the cut of 220 mm, and the chain checks were not copied anywhere else. Cable NT has no 3D route. The file is restored to match current altaay-lab. The conductor is back in the netlist, and the power sheet draws it again.

Putting that conductor back ties the bead pin to the old sense net and to the new divider at the same time. The netlist check reports that join. This is not merged.
