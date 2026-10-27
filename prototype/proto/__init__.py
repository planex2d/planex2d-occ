# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-or-later

"""the Python layer as planex will have it: the OCC module's methods attached to the core's classes, its new objects
taken over by the core"""
from ._core import Thing, _thing_from_capsule


def occ_module():
    import netgen.occ  # noqa: F401  (registers netgen's types and finds its libraries first)
    from . import _occ as occ
    return occ


def ToBox(self):
    """the Thing as an OCC box (netgen's TopoDS_Shape)"""
    return occ_module().ToBox(self)


def FromShape(shape):
    """a core Thing from an OCC shape's bounding box"""
    return _thing_from_capsule(occ_module().FromShape(shape))


Thing.ToBox = ToBox
