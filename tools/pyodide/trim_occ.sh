#!/bin/bash
# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-or-later

# OpenCASCADE's side module with only what netgen, NGSolve and planex's OCC module import: relinked from the static
# toolkits (build_occ.sh) with those names as its exports, so that the linker leaves out the rest. The full library's
# export list stays next to it for the check of later planex2d versions (occt_exports.py check).
#
#     bash trim_occ.sh <folder> <planex2d version whose OCC module the base takes>
set -euo pipefail

ROOT=${1:?the folder with the full build}
PLANEX=${2:?the planex2d version}
HERE=$(cd "$(dirname "$0")" && pwd)
LIB=$ROOT/prefix/occt/lib
PY=$ROOT/prefix/netgen/python
MODULES=("$PY"/libnglib.so "$PY"/libngcore.so "$PY"/netgen/libngpy.so "$PY"/pyngcore/pyngcore.so "$PY"/ngsolve/ngslib.so
         "$ROOT"/prefix/planex-"$PLANEX"/planex_occ/*/_planex_occ*.so)

source "$ROOT"/emsdk/emsdk_env.sh >/dev/null
python3 "$HERE"/occt_exports.py all "$LIB"/libocct.so "$LIB"/libocct-all-exports.txt
python3 "$HERE"/occt_exports.py list "$LIB"/libocct.so "$ROOT"/build/occt-exports.txt "${MODULES[@]}"
cd "$LIB"
emcc -O2 -g0 -sSIDE_MODULE=2 -fwasm-exceptions -sSUPPORT_LONGJMP=0 -sEXPORTED_FUNCTIONS=@"$ROOT"/build/occt-exports.txt \
    $(cat toolkits.txt) -o libocct-trimmed.so
mv libocct.so "$ROOT"/build/libocct-full.so
mv libocct-trimmed.so libocct.so
rm -f libTK*.a
python3 "$HERE"/occt_exports.py check libocct-all-exports.txt libocct.so "${MODULES[@]}"
echo "libocct.so: $(stat -c %s libocct.so) bytes (full: $(stat -c %s "$ROOT"/build/libocct-full.so))"
echo TRIM-DONE
