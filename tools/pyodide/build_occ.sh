#!/bin/bash
# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-or-later

# OpenCASCADE for Pyodide as ONE shared side module, libocct.so, with its symbols visible: NGSolve's build
# (tests/gitlab-ci/pyodide/build_opencascade.sh) without -fvisibility=hidden, its static toolkits linked whole into
# libocct.so, and OpenCASCADE's CMake targets pointed at that file, so that netgen and planex link it as they would
# the toolkits. netgen and planex's OCC module then share one OpenCASCADE. trim_occ.sh relinks it afterwards with only
# what they import, from the static toolkits kept here.
#
#     bash build_occ.sh <folder>
set -euo pipefail

ROOT=${1:?the folder setup.sh filled}
source "$(dirname "$0")"/pins.sh
JOBS=${JOBS:-4}
PREFIX=$ROOT/prefix/occt

source "$ROOT"/emsdk/emsdk_env.sh >/dev/null
PYTHON_INCLUDE=$ROOT/xbuildenv/pyodide-root/cpython/installs/python-$PYTHON_VERSION/include/python${PYTHON_VERSION%.*}
FLAGS="-I$PYTHON_INCLUDE -g0 -sSUPPORT_LONGJMP=0 -fwasm-exceptions -O2"

SRC=$ROOT/src/OCCT-$OCC_VERSION
if [ ! -f "$SRC"/.pyodide-patched ]; then
    (cd "$SRC" && patch -p1 < "$ROOT"/src/ngsolve/tests/gitlab-ci/pyodide/occ.patch)
    sed -i 's/-fexceptions/-fwasm-exceptions/g' "$SRC"/adm/cmake/occt_defs_flags.cmake
    touch "$SRC"/.pyodide-patched
fi

mkdir -p "$ROOT"/build/occt
cd "$ROOT"/build/occt
emcmake cmake "$SRC" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CROSSCOMPILING=ON \
    -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
    -DCMAKE_C_FLAGS="$FLAGS" \
    -DCMAKE_CXX_FLAGS="$FLAGS" \
    -DCMAKE_CXX_FLAGS_RELEASE="" \
    -DCMAKE_INSTALL_PREFIX="$PREFIX" \
    -DBUILD_LIBRARY_TYPE:STRING=Static \
    -DBUILD_MODULE_FoundationClasses:BOOL=ON \
    -DBUILD_MODULE_ModelingData:BOOL=ON \
    -DBUILD_MODULE_ModelingAlgorithms:BOOL=ON \
    -DBUILD_MODULE_DataExchange:BOOL=ON \
    -DBUILD_MODULE_Visualization:BOOL=OFF \
    -DBUILD_MODULE_ApplicationFramework:BOOL=OFF \
    -DBUILD_MODULE_Draw:BOOL=OFF \
    -DBUILD_MODULE_DETools:BOOL=OFF \
    -DUSE_FREETYPE:BOOL=OFF \
    -DUSE_OPENGL:BOOL=OFF \
    -DUSE_XLIB:BOOL=OFF \
    -DBUILD_DOC_Overview:BOOL=OFF
emmake make -j"$JOBS" install

cd "$PREFIX"/lib
ls libTK*.a > toolkits.txt
emcc -O2 -g0 -sSIDE_MODULE=1 -fwasm-exceptions -sSUPPORT_LONGJMP=0 \
    -Wl,--whole-archive $(cat toolkits.txt) -Wl,--no-whole-archive -o libocct.so
for f in "$PREFIX"/lib/cmake/opencascade/OpenCASCADE*Targets-release.cmake; do
    sed -i -E 's#\$\{_IMPORT_PREFIX\}/lib/libTK[A-Za-z0-9]+\.a#${_IMPORT_PREFIX}/lib/libocct.so#g' "$f"
done
echo "libocct.so: $(stat -c %s libocct.so) bytes, $(wc -l < toolkits.txt) toolkits"
echo OCC-DONE
