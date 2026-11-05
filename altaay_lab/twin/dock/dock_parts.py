#!/usr/bin/env python3
"""Dock printed parts for the Open Duck Mini v2 contact dock (CAD check only): writes the STLs in stl/ next to this
file. Geometry matches the dock sim of the shared lab gym (overlay gym/overlays/duck, dock/dock_course.py; DOCK_TWIN.md
section 2). Dock frame, mm: x toward the mast (the bumper face is x = 0), y left, z up from the floor.
Every part fits a 220 x 220 mm bed (the lab's print rule, START_HERE.md) and a 150 mm print height.
  dock_seat_base     the seat body on the floor: x -110..-15, y +/-20, z 0..96, 3 mm walls, spring posts and a
                     microswitch bay (Omron D2F-01L, 12.8 x 5.8 x 6.5 mm) inside
  dock_seat_top      the sprung top plate: x -110..-15, y +/-20, z 100..112 at rest (4 mm travel), a pocket for the pin
                     holder, two guide pins down into the base
  dock_pin_holder    (not used since the contacts moved to the chest paddle; kept for the belly-pad option): SENSE (x -38.7, y 0), CHG+ (x -30.2,
                     y +/-5), GND (x -47.2, y +/-5); pin bore 1.9 mm (BLOCKER: the 0932 mounting hole from the
                     Mill-Max drawing, not read)
  dock_spine         the link from the seat to the mast base: x -15..30, y +/-20, z 0..90
  dock_base_l, _r    the mast base in two halves: x 30..190, y 0..+/-140, z 0..10, an 8 mm ballast pocket
  dock_column_<n>    the mast face, an 8 mm plate x 75..83, y +/-140, z 10..460 with a 20 x 10 mm rib on the joint line,
                     cut into 2 halves x 3 sections printed lying flat
  dock_paddle        the chest paddle plate: x 0..12 at rest, y +/-55, z 140..220, three pin bores (CHG+ z 201, SENSE z 179,
                     GND z 157, y 0) with wire reliefs, two pivot knuckles (top and bottom, axis z at x 18, y 0) so the
                     plate swivels +/- 10 deg and lies flat on a yawed chest; PTFE tape on the x = 0 face
  dock_paddle_carrier  the yoke that holds the plate's pivot (two M3 x 20 screws, coaxial) and the two 4 mm guide rods
                     (y +/-40, z 180, pressed into the crossbar x 24..32); it slides 40 mm with the plate
  dock_spring_cup    two, bolted behind the mast face: x 83..141 at y +/-40, z 180; the rods run through 4.4 mm bores in
                     the face plate (column section 2) and the cup front wall; a shaft collar on each rod end rests on
                     the front wall and a 37.5 N/m compression spring in the cup pushes it home (75 N/m for the pair)
"""
import json, os
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "stl")


def box(x0, x1, y0, y1, z0, z1):
    b = trimesh.creation.box(extents=(x1 - x0, y1 - y0, z1 - z0))
    b.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    return b


def cyl(x, y, z0, z1, d, sections=32):
    c = trimesh.creation.cylinder(radius=d / 2, height=z1 - z0, sections=sections)
    c.apply_translation((x, y, (z0 + z1) / 2))
    return c


def hole_y(x, y0, y1, z, d):
    c = trimesh.creation.cylinder(radius=d / 2, height=abs(y1 - y0), sections=24)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0)))
    c.apply_translation((x, (y0 + y1) / 2, z))
    return c


def cyl_x(x0, x1, y, z, d):
    c = trimesh.creation.cylinder(radius=d / 2, height=abs(x1 - x0), sections=24)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0)))
    c.apply_translation(((x0 + x1) / 2, y, z))
    return c


def hole_x(x0, x1, y, z, d):
    c = trimesh.creation.cylinder(radius=d / 2, height=abs(x1 - x0), sections=24)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0)))
    c.apply_translation(((x0 + x1) / 2, y, z))
    return c


M3 = 3.4          # clearance for M3 screws (the build's metric kit, BOM 17 lines)
PINS = {"SENSE": [(-38.7, 0.0)], "CHG+": [(-30.2, 5.0), (-30.2, -5.0)], "GND": [(-47.2, 5.0), (-47.2, -5.0)]}


def parts():
    P = {}
    # seat base: hollow, open top, spring posts, switch bay
    base = box(-110, -15, -20, 20, 0, 96).difference(box(-107, -18, -17, 17, 3, 97))
    for x in (-95.0, -30.0):
        base = base.union(cyl(x, 0, 3, 80, 8)).difference(cyl(x, 0, 60, 81, 4.2))     # spring seats, guide bores
    base = base.union(box(-70, -56, -10, 10, 3, 70))                                   # microswitch tower
    base = base.difference(box(-69.4, -56.6, -3.0, 3.0, 63.5, 71))                      # D2F bay 12.8 x 5.8 (+0.6 fit)
    base = base.difference(hole_x(-16, -14, 0, 45, M3)).difference(hole_x(-16, -14, 0, 20, M3))   # to the spine
    P["dock_seat_base"] = base
    # seat top plate with the pin holder pocket and guide pins
    top = box(-110, -15, -20, 20, 100, 112).difference(box(-52, -25, -19, 19, 104, 113))
    for x in (-95.0, -30.0):
        top = top.union(cyl(x, 0, 80, 100, 4.0))
    P["dock_seat_top"] = top
    holder = box(-51.6, -25.4, -18.6, 18.6, 104.2, 112)
    for pts in PINS.values():
        for x, y in pts:
            holder = holder.difference(cyl(x, y, 103, 113, 1.9, 16)).difference(cyl(x, y, 103, 106, 3.2, 16))  # pin bore, wire relief
    P["dock_pin_holder"] = holder
    # spine
    spine = box(-15, 30, -20, 20, 0, 90)
    for z in (20, 45):
        spine = spine.difference(hole_x(-16, 31, 0, z, M3))
    P["dock_spine"] = spine
    # mast base halves with a ballast pocket (steel plate 100 x 120 x 10, BOM K8)
    for side, s in (("l", 1), ("r", -1)):
        y0, y1 = (0, 140) if s > 0 else (-140, 0)
        b = box(30, 190, y0, y1, 0, 10)
        pocket = box(110, 182, (5 if s > 0 else -125), (125 if s > 0 else -5), 3, 11)
        b = b.difference(pocket)
        for x in (40, 60):
            b = b.difference(cyl(x, 10 * s, -1, 11, M3))                                # spine bolts
        b = b.difference(cyl(79, 70 * s, -1, 11, M3)).difference(cyl(93, 5 * s, -1, 11, M3))   # column bolts
        P[f"dock_base_{side}"] = b
    # column: 2 halves x 3 height sections
    zc = [10, 160, 310, 460]
    for side, (y0, y1) in (("l", (0, 140)), ("r", (-140, 0))):
        for i in range(3):
            c = box(75, 83, y0, y1, zc[i], zc[i + 1])                                    # 8 mm face plate
            ry0, ry1 = (0, 10) if side == "l" else (-10, 0)
            c = c.union(box(83, 103, ry0, ry1, zc[i], zc[i + 1]))                       # rib at the joint line
            for z in (zc[i] + 20, zc[i + 1] - 20):
                c = c.difference(hole_y(93, y0 - 1, y1 + 1, z, M3))                     # bolts through both ribs
            if i == 1:                                                                   # section 2 carries the paddle guide
                yr = 40.0 if side == "l" else -40.0
                c = c.difference(hole_x(74, 84, yr, 180, 4.4))                           # rod bore through the face plate
                for dz in (-11.0, 11.0):
                    c = c.difference(hole_x(74, 84, yr, 180 + dz, M3))                   # spring cup bolts
            P[f"dock_column_{side}{i + 1}"] = c
    # chest paddle: a plate on a vertical pivot (x 18, y 0) in a yoke that slides 40 mm on two 4 mm rods; the springs
    # sit in cups behind the mast face, so the 75 mm between the paddle face and the mast keeps the full travel
    pad = box(0, 12, -55, 55, 140, 220)
    for z in (157.1, 179.1, 201.1):                                                    # CHG+ 201, SENSE 179, GND 157 (pin rows)
        pad = pad.difference(hole_x(-1, 13, 0, z, 1.9)).difference(hole_x(8, 13, 0, z, 3.2))   # pin bore, wire relief
    for z0, z1 in ((140.0, 152.0), (208.0, 220.0)):                                    # knuckles clear of the pin rows
        pad = pad.union(box(11, 18, -5, 5, z0, z1)).union(cyl(18, 0, z0, z1, 10.0))
        pad = pad.difference(cyl(18, 0, z0 - 1, z1 + 1, 2.5))                           # M3 pilot (the screw is the pivot pin)
    P["dock_paddle"] = pad
    car = box(24, 32, -6, 6, 133, 227)                                                 # yoke back bar
    for z0, z1 in ((133.0, 139.5), (220.5, 227.0)):                                    # ears above and below the knuckles
        car = car.union(box(18, 24, -6, 6, z0, z1)).union(cyl(18, 0, z0, z1, 10.0))
        car = car.difference(cyl(18, 0, z0 - 1, z1 + 1, M3))
    car = car.union(box(24, 32, -46, 46, 174, 186))                                    # rod crossbar
    for y in (-40, 40):
        car = car.difference(hole_x(23, 33, y, 180, 3.9))                               # 4 mm rods pressed in
    P["dock_paddle_carrier"] = car
    cup = cyl_x(83, 141, 0, 180, 14.0).union(box(83, 86, -8, 8, 165, 195))             # tube and bolt flange
    cup = cup.difference(hole_x(86, 138, 0, 180, 10.0)).difference(hole_x(82, 87, 0, 180, 4.4))
    for dz in (-11.0, 11.0):
        cup = cup.difference(hole_x(82, 87, 0, 180 + dz, M3))
    P["dock_spring_cup"] = cup
    return P


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    rep = {}
    for name, m in parts().items():
        m.process(validate=True)
        ext = m.extents
        path = os.path.join(OUT, name + ".stl")
        m.export(path)
        rep[name] = dict(watertight=bool(m.is_watertight), volume_cm3=round(m.volume / 1000.0, 1), extents_mm=[round(float(e), 1) for e in ext],
                         fits_220=bool(sorted(ext)[1] <= 220 and sorted(ext)[0] <= 150), bytes=os.path.getsize(path))
    json.dump(rep, open(os.path.join(OUT, "parts.json"), "w"), indent=1)
    print(json.dumps(rep, indent=1))
