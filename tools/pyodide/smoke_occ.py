# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-or-later

"""planex2d-occ in Pyodide: the versions, the loader, and one call of each kind (a pad, a projection with its
silhouette, the views of a solid, a pocket, a round trip through netgen.occ), with their times."""
import importlib.metadata as metadata
import sys
import time

t = time.perf_counter()
import planex as px
from planex import _occ
print(sys.platform, {n: metadata.version(n) for n in ("planex2d", "planex2d-occ", "netgen-mesher", "ngsolve")})
print("OCC loaded", _occ.loaded, _occ.why, f"{time.perf_counter() - t:.2f} s")


def timed(label, f):
    t = time.perf_counter()
    try:
        value = f()
    except Exception as e:
        print(f"{label}: FAILED {type(e).__name__}: {e}")
        return None
    print(f"{label}: {time.perf_counter() - t:.2f} s")
    return value


import netgen.occ as occ

plate = px.QuickSketch().Rectangle(40, 20).Face()
solid = timed("Pad", lambda: px.Pad(plate, 5))
print("volume", solid and round(solid.mass, 6), "expected", 40 * 20 * 5)
wires = timed("Project silhouette", lambda: px.Project(occ.Cylinder(occ.Pnt(0, 0, 0), occ.X, 3, 10),
                                                         silhouette=True))
print("silhouette wires", wires and len(wires))
front = timed("Drawing front view", lambda: px.Drawing(solid, px.Front, unit=px.mm))
iso = timed("Drawing isometric", lambda: px.Drawing(solid, px.Isometric, unit=px.mm))
hole = px.QuickSketch((20, 10)).Circle(4).Face()
pocketed = timed("Pocket", lambda: px.Pocket(solid, hole, 2, reverse=True))
print("volume after the pocket", pocketed and round(pocketed.mass, 6), "expected", round(4000 - 3.141592653589793 * 16 * 2, 6))
back = timed("FromOCC of ToOCCFace", lambda: px.FromOCC(plate.ToOCCFace()))
print("area back", back and round(back.mass, 9))
print("SMOKE-DONE")
