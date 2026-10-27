// SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
// SPDX-License-Identifier: LGPL-2.1-or-later

// the OCC module: built with netgen's pybind11 and ngcore's flags, linked to netgen and OCC. It shares netgen's type
// registry (TopoDS_Shape), takes the core's Thing through the conduit and hands new ones back in a capsule
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <BRepBndLib.hxx>
#include <BRepGProp.hxx>
#include <BRepPrimAPI_MakeBox.hxx>
#include <Bnd_Box.hxx>
#include <GProp_GProps.hxx>
#include <TopoDS_Shape.hxx>

#include "shared/thing.hpp"

namespace py = pybind11;
using prototype::Thing;

PYBIND11_MODULE(_occ, m) {
    py::module_::import("netgen.occ");
    // pybind11 tries the conduit only for a C++ type its own registry knows: a bare shadow of the core's class, unless
    // the core shares this registry (built with a pybind11 of the same internals) and registered it already
    if (!py::detail::get_type_info(typeid(Thing)))
        py::class_<Thing>(m, "_Thing");
    m.def("Sum", [](const Thing &t) { return t.Sum(); });
    m.def("ToBox", [](const Thing &t) -> TopoDS_Shape { return BRepPrimAPI_MakeBox(t.scale, t.Sum(), 1.0).Shape(); });
    m.def("Volume", [](const TopoDS_Shape &s) {
        GProp_GProps props;
        BRepGProp::VolumeProperties(s, props);
        return props.Mass();
    });
    m.def("FromShape", [](const TopoDS_Shape &s) {
        Bnd_Box box;
        // exact for planar faces: no tolerance gap, no triangulation
        BRepBndLib::AddOptimal(s, box, false, false);
        double x0, y0, z0, x1, y1, z1;
        box.Get(x0, y0, z0, x1, y1, z1);
        return py::capsule(new Thing{{x1 - x0, y1 - y0, z1 - z0}, 1.0}, [](void *p) { delete static_cast<Thing *>(p); });
    });
    m.attr("pybind11_version") = PYBIND11_VERSION_HEX;
    m.attr("internals_id") = PYBIND11_INTERNALS_ID;
}
