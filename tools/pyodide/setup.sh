#!/bin/bash
# SPDX-FileCopyrightText: The NGSolve team
# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-only

# The toolchain and the pinned sources of the Pyodide build in one folder, without git and without root: Emscripten
# (it brings Node), Pyodide's cross-build environment and the Pyodide runtime, OpenCASCADE, NGSolve with netgen and
# its pybind11, zlib, and Pyodide's OpenBLAS. Every archive's sha256 goes to dl/SHA256SUMS. Done steps are skipped.
#
#     bash setup.sh <folder>
set -euo pipefail

ROOT=$(mkdir -p "${1:?the folder to set up}" && cd "$1" && pwd)
source "$(dirname "$0")"/pins.sh
mkdir -p "$ROOT"/dl "$ROOT"/src "$ROOT"/dist
cd "$ROOT"

fetch() {
    [ -s "dl/$2" ] || curl -sSfL --retry 3 -o "dl/$2" "$1"
}

PYODIDE_RELEASES=https://github.com/pyodide/pyodide/releases/download/$PYODIDE_VERSION
fetch https://github.com/emscripten-core/emsdk/archive/refs/tags/$EMSDK_VERSION.tar.gz emsdk-$EMSDK_VERSION.tar.gz
fetch $PYODIDE_RELEASES/xbuildenv-$PYODIDE_VERSION.tar.bz2 xbuildenv-$PYODIDE_VERSION.tar.bz2
fetch $PYODIDE_RELEASES/pyodide-core-$PYODIDE_VERSION.tar.bz2 pyodide-core-$PYODIDE_VERSION.tar.bz2
fetch https://github.com/Open-Cascade-SAS/OCCT/archive/refs/tags/V$OCC_VERSION.zip OCCT-$OCC_VERSION.zip
fetch https://github.com/NGSolve/ngsolve/archive/$NGSOLVE_COMMIT.tar.gz ngsolve-$NGSOLVE_COMMIT.tar.gz
fetch https://github.com/NGSolve/netgen/archive/$NETGEN_COMMIT.tar.gz netgen-$NETGEN_COMMIT.tar.gz
fetch https://github.com/ngsolve/pybind11/archive/$PYBIND11_COMMIT.tar.gz pybind11-$PYBIND11_COMMIT.tar.gz
fetch https://github.com/madler/zlib/archive/refs/tags/v$ZLIB_VERSION.zip zlib-v$ZLIB_VERSION.zip
fetch https://raw.githubusercontent.com/OpenMathLib/OpenBLAS/v$OPENBLAS_VERSION/LICENSE OpenBLAS-LICENSE
fetch https://cdn.jsdelivr.net/pyodide/v$PYODIDE_VERSION/full/pyodide-lock.json pyodide-lock.json
OPENBLAS=$(python3 -c "import json; print(json.load(open('dl/pyodide-lock.json'))['packages']['libopenblas']['file_name'])")
fetch https://cdn.jsdelivr.net/pyodide/v$PYODIDE_VERSION/full/$OPENBLAS "$OPENBLAS"
(cd dl && sha256sum -- * | grep -v SHA256SUMS > SHA256SUMS)

if [ ! -d emsdk ]; then
    tar xzf dl/emsdk-$EMSDK_VERSION.tar.gz && mv emsdk-$EMSDK_VERSION emsdk
fi
[ -d emsdk/upstream/emscripten ] || (cd emsdk && ./emsdk install $EMSDK_VERSION && ./emsdk activate $EMSDK_VERSION)
# shared libraries (Pyodide's side modules) from CMake; pybind11 strips every Python module after linking and plain
# emstrip drops the dylink.0 section, so its stand-in keeps that
TOOLCHAIN=$ROOT/emsdk/upstream/emscripten/cmake/Modules/Platform/Emscripten.cmake
printf '#!/bin/bash\nexec "%s" --keep-section=dylink.0 "$@"\n' "$ROOT/emsdk/upstream/emscripten/emstrip" > emstrip_side_module
chmod +x emstrip_side_module
if ! grep -q emstrip_side_module "$TOOLCHAIN"; then
    sed -i 's/TARGET_SUPPORTS_SHARED_LIBS FALSE/TARGET_SUPPORTS_SHARED_LIBS TRUE/' "$TOOLCHAIN"
    echo "set(CMAKE_STRIP \"$ROOT/emstrip_side_module\" CACHE FILEPATH \"Emscripten strip\")" >> "$TOOLCHAIN"
fi
[ -d xbuildenv ] || tar xjf dl/xbuildenv-$PYODIDE_VERSION.tar.bz2
[ -d core ] || (mkdir core && tar xjf dl/pyodide-core-$PYODIDE_VERSION.tar.bz2 -C core)
[ -d src/OCCT-$OCC_VERSION ] || (cd src && unzip -q ../dl/OCCT-$OCC_VERSION.zip)

if [ ! -d src/ngsolve ]; then
    mkdir -p src/ngsolve
    tar xzf dl/ngsolve-$NGSOLVE_COMMIT.tar.gz -C src/ngsolve --strip-components=1
    echo "$NGSOLVE_DESCRIBE" > src/ngsolve/version.txt
    NETGEN=src/ngsolve/external_dependencies/netgen
    rm -rf $NETGEN && mkdir -p $NETGEN
    tar xzf dl/netgen-$NETGEN_COMMIT.tar.gz -C $NETGEN --strip-components=1
    echo "$NETGEN_DESCRIBE" > $NETGEN/version.txt
    rm -rf $NETGEN/external_dependencies/pybind11 && mkdir -p $NETGEN/external_dependencies/pybind11
    tar xzf dl/pybind11-$PYBIND11_COMMIT.tar.gz -C $NETGEN/external_dependencies/pybind11 --strip-components=1
    # netgen's superbuild downloads zlib to this place unless it is there (it checks the archive's MD5)
    cp dl/zlib-v$ZLIB_VERSION.zip $NETGEN/external_dependencies/v$ZLIB_VERSION.zip
fi

[ -s dist/libopenblas.so ] || (cd dist && unzip -q -o ../dl/"$OPENBLAS")
cp dl/pyodide-lock.json dist/
echo SETUP-DONE
