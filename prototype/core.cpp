// SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
// SPDX-License-Identifier: LGPL-2.1-or-later

// the core: built with pybind11 from pip, of any version, without netgen
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "shared/thing.hpp"

namespace py = pybind11;
using prototype::Thing;

PYBIND11_MODULE(_core, m) {
    py::class_<Thing>(m, "Thing")
        .def(py::init([](std::vector<double> xs, double scale) { return Thing{std::move(xs), scale}; }), py::arg("xs"),
             py::arg("scale") = 1.0)
        .def("Sum", &Thing::Sum)
        .def_readonly("xs", &Thing::xs)
        .def_readonly("scale", &Thing::scale);
    // a Thing the OCC module made, handed over in a capsule: its contents move into a new core object, the capsule's
    // own destructor (the OCC module's) frees what is left
    m.def("_thing_from_capsule", [](const py::capsule &c) { return std::move(*c.get_pointer<Thing>()); });
    m.attr("pybind11_version") = PYBIND11_VERSION_HEX;
    m.attr("internals_id") = PYBIND11_INTERNALS_ID;
}
