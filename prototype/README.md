# Conduit prototype

A check of planex's package split before any code moves: can the core be built with its own pybind11 while the OCC
module is built with netgen's?

- `core.cpp` (`_core`): pybind11 from pip, the version the workflow's matrix installs, no netgen.
- `occ.cpp` (`_occ`): netgen's bundled pybind11 and ngcore's flags, linked to netgen and OpenCASCADE from their pip
  wheels, as planex's `_planex_occ`.
- `proto/__init__.py`: the Python layer as planex will have it: the OCC module's method attached to the core's class,
  its new objects taken over by the core.
- `test_conduit.py`: a core object as the OCC module's argument (pybind11's conduit when the two type registries
  differ), netgen's `TopoDS_Shape` back, a new core object from a capsule, and the moved contents outliving the capsule.

The workflow `.github/workflows/conduit-prototype.yml` runs it on Linux, macOS (Apple Silicon) and Windows for the core
built with pybind11 3.1.0 and 3.0.1 (netgen 6.2.2608 bundles 3.1.0a0).

Found on Linux (2026-10-27):

- 3.1.0 (internals 12, as netgen's): one type registry, everything passes.
- 3.0.1 (internals 11): two registries; pybind11 tries the conduit only for a C++ type its own registry knows, so the
  OCC module registers a bare shadow of the core's class (`_Thing`) when the core has not registered it in a shared
  registry; then everything passes.
- 2.13.6: fails; 2.x writes the platform id (`gcc_libstdcpp_cxxabi1019`) in another format than 3.x
  (`system_libstdcpp_gxx_abi_1xxx_use_cxx11_abi_1`), so the conduits never match. The core needs pybind11 3.x.
