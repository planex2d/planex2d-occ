# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-or-later

"""planex2d-occ: planex's OCC bindings, one module per netgen version this release is built for. Importing it loads the
module for the installed netgen into planex; planex imports it by itself (pip install planex2d[occ])."""
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def _folder(netgen):
    """the subpackage of a netgen version: ng_6_2_2608, ng_6_2_2602_post1"""
    return "ng_" + netgen.replace(".", "_")


def built_for():
    """the netgen versions this release has a module for, oldest first"""
    here = Path(__file__).parent
    names = sorted(p.name for p in here.iterdir() if p.is_dir() and p.name.startswith("ng_"))
    return [n[3:].replace("_", ".") for n in names]


def _load():
    try:
        installed = version("netgen-mesher")
    except PackageNotFoundError:
        raise ImportError("planex2d-occ needs netgen: pip install planex2d[occ] installs it") from None
    if installed not in built_for():
        raise ImportError(f"planex2d-occ {version('planex2d-occ')} has no module for netgen {installed}; it is built for "
                          f"netgen {', '.join(built_for())}: pip install --upgrade planex2d[occ] finds the planex2d-occ "
                          f"for your netgen, or pip install netgen-mesher=={built_for()[-1]}")
    # netgen first: it registers its types and, on Windows, the folders of its and OpenCASCADE's DLLs
    import_module("netgen.occ")
    return import_module(f"planex_occ.{_folder(installed)}._planex_occ")


bindings = _load()
