# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-or-later

"""What OpenCASCADE's side module exports in the Pyodide build: exactly the names netgen, NGSolve and planex's OCC
module import from it, so that the linker leaves out the rest (it loads several times faster).

    python3 occt_exports.py all <libocct.so> <out.txt>
        every name the full library exports (kept with the base build for the check)
    python3 occt_exports.py list <libocct.so> <out.txt> <module.so> ...
        the names the modules import from the full library, as EXPORTED_FUNCTIONS takes them (a leading underscore)
    python3 occt_exports.py check <all exports.txt> <libocct.so> <module.so> ...
        the OpenCASCADE names a module imports that the library leaves out: listed, and the exit status 1
"""
import sys
from pathlib import Path

from wasm import tables


def main(step, *args):
    if step == "all":
        library, out = args
        Path(out).write_text("".join(f"{name}\n" for name in sorted(tables(library)[1])))
    elif step == "list":
        library, out, *modules = args
        exported = tables(library)[1]
        needed = set().union(*(tables(m)[0] & exported for m in modules))
        Path(out).write_text("".join(f"_{name}\n" for name in sorted(needed)))
        print(f"OpenCASCADE exports {len(needed)} of {len(exported)} names")
    elif step == "check":
        everything, library, *modules = args
        occt = set(Path(everything).read_text().split())
        exported = tables(library)[1]
        missing = sorted(set().union(*(tables(m)[0] for m in modules)) & occt - exported)
        if missing:
            print(f"{len(missing)} OpenCASCADE functions the modules import are left out of {Path(library).name}:")
            print("\n".join(f"  {name}" for name in missing[:40]))
            print("This needs a new base build: run pyodide.yml with new_base.")
            return 1
        print(f"every OpenCASCADE name the modules import is in {Path(library).name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
