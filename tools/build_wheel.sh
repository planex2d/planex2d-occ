#!/bin/sh
# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-or-later

# one planex2d-occ wheel for this platform and Python into dist/: the modules of the netgen versions in $4 built from
# planex2d's sdist, those in $5 taken from the previous release's wheel ($6), the release's metadata ($3, $7)
#   sh tools/build_wheel.sh PYTHON PLANEX2D VERSION "BUILD..." "KEEP..." PREVIOUS "WINDOW..."
# INDEX_SIMPLE: the index planex2d and the previous planex2d-occ come from; SDIST: planex2d's sdist from a file (tests)
set -e
py=$1 planex2d=$2 version=$3 build=$4 keep=$5 previous=$6 window=$7
staging=$($py -c 'import os; print(os.path.abspath("staging"))')
reuse=""
if [ -n "$keep" ] && [ -n "$previous" ]; then
    $py -m pip download "planex2d-occ==$previous" --no-deps --only-binary :all: -d previous --index-url "$INDEX_SIMPLE"
    reuse="--reuse $(ls previous/*.whl) --keep $keep"
fi
$py tools/build_modules.py --planex2d "$planex2d" --index "$INDEX_SIMPLE" ${SDIST:+--sdist "$SDIST"} --netgen $build $reuse \
    --staging "$staging"
$py tools/metadata.py --version "$version" --planex2d "$planex2d" --netgen $window
rm -rf licenses && cp -r "$staging/licenses" licenses
$py -m pip wheel . --no-deps --no-build-isolation -w dist -Ccmake.define.PLANEX_OCC_STAGING="$staging"
