# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-or-later

# Every pin of the Pyodide build: the browser's files come from these versions and nothing else. netgen and NGSolve
# are frozen at the commits of NGSolve's own Pyodide build of 2026-10-29 (6.2.2608.post82 and .post173), with
# OpenCASCADE 8.0.1 as one shared side module with only what they use.
export PYODIDE_VERSION=314.0.6
export PYODIDE_ABI=2026_0
export PYTHON_VERSION=3.14.2
export EMSDK_VERSION=5.0.3
export OCC_VERSION=8_0_1
export NETGEN_COMMIT=98232f962908dd16402f2cab343b62ea981a7c64
export NETGEN_DESCRIBE=v6.2.2608-82-g98232f96
export NETGEN_VERSION=6.2.2608.post82.dev0
export NGSOLVE_COMMIT=fb1c068b7a353d893bdc6b7f6c538b4338f39038
export NGSOLVE_DESCRIBE=v6.2.2608-173-gfb1c068b7a
export NGSOLVE_VERSION=6.2.2608.post173.dev0
export PYBIND11_COMMIT=98e50b702d9ab784ec918399aaa20adcfd1af9a9
export ZLIB_VERSION=1.3.1
export OPENBLAS_VERSION=0.3.31
# the base builds these pins give: OpenCASCADE, netgen and NGSolve, shared by the planex2d versions built on it;
# each is named after the planex2d version whose OCC module chose OpenCASCADE's exports: <BASE_PREFIX>-planex2d-<version>
export BASE_PREFIX=netgen-$NETGEN_VERSION-occt-${OCC_VERSION//_/.}-pyodide-$PYODIDE_VERSION
