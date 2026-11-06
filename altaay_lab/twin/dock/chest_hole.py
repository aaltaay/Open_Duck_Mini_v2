"""D50: the chest lead feedthrough in print/body_front.stl (CAD check only). One 6.0 mm hole through the 10 mm chest wall at the
pad centre (world y 0, z 38 at the zero pose, the wall x 36 to 46) for the four pad conductors (3 x 20 AWG at 1.9 mm, 1 x 26 AWG at
1.3 mm: a 4.6 mm bundle, 0.7 mm a side to spare). Strain relief printed in the wall: a 45 deg bell mouth 2.0 mm deep on the inside
(10.0 mm across at the inner face), where the leads turn towards their splices, and a 0.8 mm 45 deg chamfer on the pad side, so
the bundle bends over a wide 45 deg mouth, not a sharp edge. A grommet ring standing 2 mm proud of the inner face was tried and
dropped: body_front prints +x up, so the ring would hang under the chest wall's bridged ceiling and the slicer adds 1.8 g of
support inside the shell; the bell mouth and the chamfer are 45 deg overhangs and need none. The hole carries the leads, so D39
(no empty hole) holds; no screw changes (D42).
Run: python3 altaay_lab/twin/dock/chest_hole.py [--write]   (writes print/body_front.stl and stl/chest_hole_section.png)"""
import os, sys
import numpy as np, trimesh
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
STL = os.path.join(REPO, "print", "body_front.stl")
OFF = np.array([-19.0, 0.0, 64.89093881])          # body_front STL frame to the URDF world at the zero pose (twin/complete3d scene)
C = np.array([0.0, 0.0, 38.0]) - OFF               # hole axis point in the STL frame (axis along x)
D_HOLE, CH_OUT, BELL = 6.0, 0.8, 2.0                # hole, pad-side chamfer, inner bell mouth depth (45 deg)
X_IN, X_OUT = 36.0 - OFF[0], 46.0 - OFF[0]


def cyl_x(x0, x1, d, sec=64):
    c = trimesh.creation.cylinder(radius=d / 2, height=x1 - x0, sections=sec)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0)))
    c.apply_translation([(x0 + x1) / 2, C[1], C[2]]); return c


def cone_x(x_tip, x_base, d_base, sec=64):
    c = trimesh.creation.cone(radius=d_base / 2, height=abs(x_tip - x_base), sections=sec)
    R = trimesh.transformations.rotation_matrix(np.pi / 2 if x_tip > x_base else -np.pi / 2, (0, 1, 0))
    c.apply_transform(R); c.apply_translation([x_base, C[1], C[2]]); return c


def make(m):
    m = m.difference(cyl_x(X_IN - 1, X_OUT + 1, D_HOLE))
    w_out, w_in = D_HOLE + 2 * CH_OUT, D_HOLE + 2 * BELL          # 45 deg cones: the hole plus 2 x depth at each mouth
    m = m.difference(cone_x(X_OUT - w_out / 2, X_OUT, w_out)).difference(cone_x(X_IN + w_in / 2, X_IN, w_in))
    return m


if __name__ == "__main__":
    m0 = trimesh.load(STL)
    if abs(m0.volume - 142628.4) > 50:
        raise SystemExit("body_front.stl is not the pre-D50 file (volume %.1f mm3): already applied?" % m0.volume)
    m = make(m0)
    assert m.is_watertight
    print("volume %.1f -> %.1f mm3 (%+.2f cm3)" % (m0.volume, m.volume, (m.volume - m0.volume) / 1000))
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(12, 6))
    for k, (n, o) in enumerate((([0, 1, 0], C), ([0, 0, 1], C))):
        s = m.section(plane_origin=o, plane_normal=n)
        for e in s.discrete:
            e = e + OFF
            ax[k].plot(e[:, 0], e[:, 2] if k == 0 else e[:, 1], "k-", lw=0.8)
        b = 4.6 / 2                                                 # the 4-wire bundle in the hole
        ax[k].add_patch(plt.Rectangle((30, (38 if k == 0 else 0) - b), 20, 2 * b, color="tab:orange", alpha=0.4))
        ax[k].set_xlim(28, 50); ax[k].set_ylim((38 if k == 0 else 0) - 10, (38 if k == 0 else 0) + 10); ax[k].set_aspect("equal")
        ax[k].set_xlabel("x mm (world)"); ax[k].set_ylabel("z mm" if k == 0 else "y mm")
        ax[k].set_title("section %s: 6.0 mm hole, 2 mm bell mouth inside,\n0.8 mm chamfer at the pad; orange: the 4.6 mm 4-wire bundle" % ("y = 0" if k == 0 else "z = 38"), fontsize=9)
    plt.tight_layout(); plt.savefig(os.path.join(HERE, "stl", "chest_hole_section.png"), dpi=130)
    if "--write" in sys.argv:
        m.export(STL); print("wrote", os.path.relpath(STL, REPO))
