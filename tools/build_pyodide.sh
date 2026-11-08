#!/bin/bash
# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-or-later

# planex2d-occ for the browser (Pyodide), for planex2d.org's playground; not on PyPI, which has no Pyodide netgen.
# netgen, NGSolve and OpenCASCADE are built once per set of pins (tools/pyodide/pins.sh) and a planex2d version: the
# base, whose OpenCASCADE exports exactly what netgen, NGSolve and that version's OCC module import (the linker leaves
# out the rest). Later planex2d versions build their OCC module on it, as long as it exports what they import.
# Everything goes into one folder; the files to publish into <folder>/out.
#
#     tools/build_pyodide.sh base <folder> <planex2d>      the base, named <BASE_PREFIX>-planex2d-<planex2d>
#     tools/build_pyodide.sh planex <folder> <planex2d>    planex's OCC module on the base in <folder>/out/site, its
#                                                          wheel, the lock, the tests
#
# out/ after both: pyodide-base-<BASE>-build.tar.gz (what a planex run builds on), pyodide-base-<BASE>.zip (the base
# wheels and NOTICES.txt, unpacked by the site into /pyodide/<BASE>/), pyodide-base-<BASE>-sources.tar (the sources),
# pyodide-<planex2d>.zip (planex2d-occ's wheel and pyodide-lock.json, unpacked into /pyodide/<planex2d>/).
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
STEP=${1:?base or planex}
ROOT=$(mkdir -p "${2:?the folder}" && cd "$2" && pwd)
PLANEX=${3:?the planex2d version}
source "$HERE"/pyodide/pins.sh
OUT=$ROOT/out
mkdir -p "$OUT/site"

if [ "$STEP" = base ]; then
    export BASE=$BASE_PREFIX-planex2d-$PLANEX
    bash "$HERE"/pyodide/setup.sh "$ROOT"
    bash "$HERE"/pyodide/build_occ.sh "$ROOT"
    bash "$HERE"/pyodide/build_netgen.sh "$ROOT"
    bash "$HERE"/pyodide/build_planex_occ.sh "$ROOT" "$PLANEX"
    bash "$HERE"/pyodide/trim_occ.sh "$ROOT" "$PLANEX"
    python3 "$HERE"/pyodide/pack.py base "$ROOT" "$OUT/site"
    tar czf "$OUT/pyodide-base-$BASE-build.tar.gz" --exclude='*.a' -C "$ROOT" prefix/occt prefix/netgen dist
    (cd "$OUT/site" && rm -f "$OUT/pyodide-base-$BASE.zip" && python3 -m zipfile -c "$OUT/pyodide-base-$BASE.zip" "$BASE")
    tar cf "$OUT/pyodide-base-$BASE-sources.tar" -C "$ROOT" dl
    tar rf "$OUT/pyodide-base-$BASE-sources.tar" -C "$HERE/.." LICENSE THIRD_PARTY_NOTICES.md tools/build_pyodide.sh tools/pyodide
elif [ "$STEP" = planex ]; then
    BASES=("$OUT"/site/"$BASE_PREFIX"-planex2d-*/)
    if [ ${#BASES[@]} -ne 1 ] || [ ! -d "${BASES[0]}" ]; then
        echo "out/site needs exactly one base of these pins ($BASE_PREFIX-planex2d-*)" >&2
        exit 2
    fi
    export BASE=$(basename "${BASES[0]}")
    bash "$HERE"/pyodide/setup.sh "$ROOT"
    bash "$HERE"/pyodide/build_planex_occ.sh "$ROOT" "$PLANEX"
    LIB=$ROOT/prefix/occt/lib
    python3 "$HERE"/pyodide/occt_exports.py check "$LIB"/libocct-all-exports.txt "$LIB"/libocct.so \
        "$ROOT"/prefix/planex-"$PLANEX"/planex_occ/*/_planex_occ*.so
    python3 "$HERE"/pyodide/pack.py planex "$ROOT" "$PLANEX" "$HERE/.." "$OUT/site"
    # the tests: Pyodide under Node, the base wheels and this version's files in one folder over local HTTP
    TEST=$ROOT/test-$PLANEX
    rm -rf "$TEST" && mkdir -p "$TEST"
    cp "$OUT/site/$BASE"/*.whl "$OUT/site/$PLANEX"/* "$TEST"/
    NODE=$(ls -d "$ROOT"/emsdk/node/*/bin)/node
    PORT=${PORT:-18765}
    python3 "$HERE"/pyodide/serve.py "$TEST" "$PORT" &
    SERVER=$!
    trap 'kill $SERVER' EXIT
    sleep 2
    CORE=$ROOT/core/pyodide
    "$NODE" "$HERE"/pyodide/run_with_lock.mjs "$CORE" "http://127.0.0.1:$PORT" planex2d-occ,ngsolve \
        "$HERE"/pyodide/smoke_occ.py | tee "$ROOT/smoke-$PLANEX.log"
    grep -q "OCC loaded True" "$ROOT/smoke-$PLANEX.log"
    if grep -q FAILED "$ROOT/smoke-$PLANEX.log"; then exit 1; fi
    # the two tests that start a subprocess, which Pyodide cannot: planex2d up to 0.3.1 does not mark them
    "$NODE" "$HERE"/pyodide/run_pytest.mjs "$CORE" "http://127.0.0.1:$PORT" planex2d-occ,ngsolve,matplotlib,scipy,shapely \
        "$ROOT/src/planex/planex2d-$PLANEX" --ignore=fuzz -rfE \
        -k "not test_without_the_occ_module_planex_has_the_same_names and not test_the_occ_bindings_refuse_a_core_of_another_version_or_other_sources" \
        | tee "$ROOT/tests-$PLANEX.log"
    (cd "$OUT/site" && rm -f "$OUT/pyodide-$PLANEX.zip" && python3 -m zipfile -c "$OUT/pyodide-$PLANEX.zip" "$PLANEX")
else
    echo "base or planex" >&2
    exit 2
fi
ls -la "$OUT"
