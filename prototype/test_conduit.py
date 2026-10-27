# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-or-later

"""the boundary of planex's package split: a core built with pybind11 from pip, of another version
than netgen's, and an OCC module built with netgen's pybind11 pass objects both ways"""
import gc
import sys

import netgen.occ as occ

import proto
from proto import _core

occ_module = proto.occ_module()
print("python", sys.version.split()[0], sys.platform)
print("core: pybind11 %x, %s" % (_core.pybind11_version, _core.internals_id))
print("occ:  pybind11 %x, %s" % (occ_module.pybind11_version, occ_module.internals_id))
print("one type registry" if _core.internals_id == occ_module.internals_id else "two type registries: the conduit carries the objects")

t = proto.Thing([1.0, 2.0, 3.5], 2.0)
# a core object as the OCC module's argument
assert occ_module.Sum(t) == t.Sum() == 13.0
# a method the OCC module adds, attached in Python, returning netgen's own type
box = t.ToBox()
assert isinstance(box, occ.TopoDS_Shape), type(box)
assert abs(occ_module.Volume(box) - 2.0 * 13.0 * 1.0) < 1e-9
# netgen's own functions take it
assert abs(box.mass - 26.0) < 1e-9
# a new object the OCC module makes, taken over by the core
back = proto.FromShape(occ.Box(occ.Pnt(0, 0, 0), occ.Pnt(1, 2, 3)))
assert isinstance(back, proto.Thing), type(back)
assert [round(x, 9) for x in back.xs] == [1.0, 2.0, 3.0] and back.Sum() == 6.0
# the moved contents live on in the core after the capsule is gone, many times over
for k in range(2000):
    things = [proto.FromShape(box) for _ in range(5)]
    assert all(abs(x.Sum() - 16.0) < 1e-9 for x in things)
    del things
    gc.collect()
print("conduit prototype: all checks passed")
