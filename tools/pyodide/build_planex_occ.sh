#!/bin/bash
# SPDX-FileCopyrightText: The NGSolve team
# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-only

# planex's OCC module for Pyodide from planex2d's sdist (PLANEX_CORE=OFF, PLANEX_OCC=ON), against netgen and
# libocct.so (the base build), with netgen's flags and its patched pybind11.
#
#     bash build_planex_occ.sh <folder> <planex2d version>
set -euo pipefail

ROOT=${1:?the folder with the base build}
PLANEX=${2:?the planex2d version}
source "$(dirname "$0")"/pins.sh
JOBS=${JOBS:-4}
FOLDER=ng_${NETGEN_VERSION//./_}

source "$ROOT"/emsdk/emsdk_env.sh >/dev/null
TARGETINSTALLDIR=$ROOT/xbuildenv/pyodide-root/cpython/installs/python-$PYTHON_VERSION
PYTHON_INCLUDE=$TARGETINSTALLDIR/include/python${PYTHON_VERSION%.*}
PYTHON_SOABI=cpython-${PYTHON_VERSION%.*}-wasm32-emscripten
PYTHON_SOABI=${PYTHON_SOABI/./}
SIDE_MODULE_LDFLAGS="-O2 -g0 -sSIDE_MODULE=1 -fwasm-exceptions -sSUPPORT_LONGJMP=0"
FLAGS="-g0 -O2 -sSUPPORT_LONGJMP=0 -fwasm-exceptions -msimd128"

SDIST=$ROOT/dl/planex2d-$PLANEX.tar.gz
[ -s "$SDIST" ] || curl -sSfL --retry 3 -o "$SDIST" "https://files.pythonhosted.org/packages/source/p/planex2d/planex2d-$PLANEX.tar.gz"
SRC=$ROOT/src/planex/planex2d-$PLANEX
mkdir -p "$ROOT"/src/planex
[ -d "$SRC" ] || tar xzf "$SDIST" -C "$ROOT"/src/planex
# a cross build has only the target Python's headers: planex2d up to 0.3.1 asks for an interpreter too
sed -i 's/COMPONENTS Interpreter Development.Module)/COMPONENTS Development.Module)/' "$SRC"/CMakeLists.txt

BUILD=$ROOT/build/planex-$PLANEX
rm -rf "$BUILD" "$ROOT/prefix/planex-$PLANEX"
mkdir -p "$BUILD"
cd "$BUILD"
emcmake cmake "$SRC" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CROSSCOMPILING=ON \
    -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
    -DCMAKE_C_FLAGS="$FLAGS" \
    -DCMAKE_CXX_FLAGS="$FLAGS" \
    -DCMAKE_CXX_FLAGS_RELEASE="" \
    -DCMAKE_MODULE_LINKER_FLAGS="$SIDE_MODULE_LDFLAGS" \
    -DCMAKE_SHARED_LINKER_FLAGS="$SIDE_MODULE_LDFLAGS" \
    -DCMAKE_INSTALL_PREFIX="$ROOT/prefix/planex-$PLANEX" \
    -DPLANEX_CORE=OFF \
    -DPLANEX_OCC=ON \
    -DPLANEX_VERSION="$PLANEX" \
    -DPLANEX_OCC_DESTINATION="planex_occ/$FOLDER" \
    -DNetgen_DIR="$ROOT/prefix/netgen/lib/cmake/netgen" \
    -DOpenCASCADE_DIR="$ROOT/prefix/occt/lib/cmake/opencascade" \
    -DPython3_ROOT_DIR="$TARGETINSTALLDIR" \
    -DPython3_INCLUDE_DIR="$PYTHON_INCLUDE" \
    -DPython3_SOABI="$PYTHON_SOABI"
emmake make -j"$JOBS"
emmake make install
ls -la "$ROOT/prefix/planex-$PLANEX/planex_occ/$FOLDER"
echo PLANEX-DONE
