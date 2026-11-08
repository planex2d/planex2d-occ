#!/bin/bash
# SPDX-FileCopyrightText: The NGSolve team
# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-only

# netgen and NGSolve for Pyodide against libocct.so (build_occ.sh): NGSolve's build (tests/gitlab-ci/pyodide/
# build_in_docker.sh) with these folders, OpenCASCADE from prefix/occt, and no stub files (they would import the
# WebAssembly modules into the building Python).
#
#     bash build_netgen.sh <folder>
set -euo pipefail

ROOT=${1:?the folder setup.sh filled}
source "$(dirname "$0")"/pins.sh
JOBS=${JOBS:-4}
PREFIX=$ROOT/prefix/netgen
NGSOLVE=$ROOT/src/ngsolve
PYBIND11=$NGSOLVE/external_dependencies/netgen/external_dependencies/pybind11

source "$ROOT"/emsdk/emsdk_env.sh >/dev/null
TARGETINSTALLDIR=$ROOT/xbuildenv/pyodide-root/cpython/installs/python-$PYTHON_VERSION
PYTHON_INCLUDE=$TARGETINSTALLDIR/include/python${PYTHON_VERSION%.*}
SIDE_MODULE_LDFLAGS="-O2 -g0 -sSIDE_MODULE=1 -fwasm-exceptions -sSUPPORT_LONGJMP=0"

if [ ! -f "$PYBIND11"/.pyodide-patched ]; then
    (cd "$PYBIND11" && patch -p1 < "$NGSOLVE"/tests/gitlab-ci/pyodide/pybind11.patch)
    touch "$PYBIND11"/.pyodide-patched
fi

# every CMake run below, the sub-builds NGSolve's superbuild starts included, loads Emscripten's toolchain: on a GitHub
# runner the superbuild configured NGSolve itself without it ("CMAKE_SYSTEM_NAME was not set")
export CMAKE_TOOLCHAIN_FILE=$ROOT/emsdk/upstream/emscripten/cmake/Modules/Platform/Emscripten.cmake
echo "cmake: $(command -v cmake) ($(cmake --version | head -1)); emcmake: $(command -v emcmake)"

export CCACHE_DIR=$ROOT/ccache
mkdir -p "$ROOT"/build/ngsolve
cd "$ROOT"/build/ngsolve
emcmake cmake "$NGSOLVE" \
    -DCMAKE_CROSSCOMPILING=ON \
    -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
    -DCMAKE_C_FLAGS="-g0 -O2 -I$PYTHON_INCLUDE -sSUPPORT_LONGJMP=0 -msimd128" \
    -DCMAKE_CXX_FLAGS="-g0 -O2 -I$PYTHON_INCLUDE -sSUPPORT_LONGJMP=0 -msimd128" \
    -DCMAKE_MODULE_LINKER_FLAGS="$SIDE_MODULE_LDFLAGS" \
    -DCMAKE_SHARED_LINKER_FLAGS="$SIDE_MODULE_LDFLAGS" \
    -DUSE_SUPERBUILD=ON \
    -DUSE_CCACHE="${USE_CCACHE:-OFF}" \
    -DNGLIB_LIBRARY_TYPE=SHARED \
    -DNGCORE_LIBRARY_TYPE=SHARED \
    -DMAX_SYS_DIM=1 \
    -DCMAKE_BUILD_TYPE=Release \
    -DUSE_FASTCOMPILE=1 \
    -DUSE_CSG:UNINITIALIZED=ON \
    -DUSE_CUDA:BOOL=OFF \
    -DUSE_GUI:BOOL=OFF \
    -DUSE_HYPRE:BOOL=OFF \
    -DUSE_INTERFACE:UNINITIALIZED=ON \
    -DUSE_LAPACK:BOOL=ON \
    -DLAPACK_LIBRARIES="$ROOT/dist/libopenblas.so" \
    -DUSE_MKL:BOOL=OFF \
    -DUSE_MPI:BOOL=OFF \
    -DUSE_MUMPS:BOOL=OFF \
    -DUSE_NATIVE_ARCH:UNINITIALIZED=OFF \
    -DUSE_PARDISO:BOOL=OFF \
    -DUSE_PYTHON:BOOL=ON \
    -DPython3_ROOT_DIR="$TARGETINSTALLDIR" \
    -DPython3_INCLUDE_DIR="$PYTHON_INCLUDE" \
    -DPython3_INCLUDE_DIRS="$TARGETINSTALLDIR/include" \
    -DNG_INSTALL_DIR_PYTHON=python \
    -DNG_INSTALL_DIR_LIB=python \
    -DUSE_STLGEOM:UNINITIALIZED=ON \
    -DUSE_UMFPACK:BOOL=OFF \
    -DNetgen_DIR="$PREFIX/lib/cmake/netgen" \
    -DCMAKE_INSTALL_PREFIX="$PREFIX" \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
    -DPYBIND_INCLUDE_DIR="$PYBIND11/include" \
    -Dpybind11_INCLUDE_DIR="$PYBIND11/include" \
    -DCMAKE_CXX_FLAGS_RELEASE="" \
    -DBUILD_FOR_CONDA=ON \
    -DBUILD_STUB_FILES=OFF \
    -DUSE_OCC:BOOL=ON \
    -DOpenCascade_DIR="$ROOT/prefix/occt/lib/cmake/opencascade" \
    -DBUILD_OCC=OFF \
    -DBUILD_ZLIB=ON
emmake make -j"$JOBS" install
for sub in netgen ngsolve; do
    if ! grep -qs 'CMAKE_SYSTEM_NAME "Emscripten"' "$ROOT"/build/ngsolve/$sub/CMakeFiles/*/CMakeSystem.cmake; then
        echo "the $sub sub-build was configured without Emscripten's toolchain" >&2
        exit 1
    fi
done
ls -la "$PREFIX"/python/libnglib.so "$PREFIX"/python/ngsolve/ngslib.so
echo NETGEN-DONE
