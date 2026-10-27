# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-or-later

"""Build planex's OCC bindings from planex2d's sdist, one module per netgen version, into a staging folder that
planex2d-occ's wheel packages (CMakeLists.txt, PLANEX_OCC_STAGING).

Every netgen version gets its own virtual environment with that netgen and the OpenCASCADE headers it was built with;
the module is compiled there with netgen's pybind11 against planex2d's sources (PLANEX_CORE=OFF). --reuse takes the
modules of the versions not given to --netgen from an earlier planex2d-occ wheel of the same core, platform and Python.

    python tools/build_modules.py --planex2d 0.2.0 --netgen 6.2.2608 --staging staging
    python tools/build_modules.py --planex2d 0.2.0 --netgen 6.2.2609 --reuse dist-previous/*.whl --staging staging
"""
import argparse
import os
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import sdist


def run(*args, **kwargs):
    print("+", " ".join(str(a) for a in args), flush=True)
    subprocess.run([str(a) for a in args], check=True, **kwargs)


def folder(netgen):
    """the module's folder for a netgen version, as the loader looks for it: ng_6_2_2608, ng_6_2_2602_post1"""
    return "ng_" + netgen.replace(".", "_")


def venv_python(venv):
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def sdist_of(planex2d, index, work, local=None):
    """planex2d's sdist of that version (or the file local), unpacked"""
    archive = Path(local) if local else sdist.download(planex2d, index or "https://pypi.org/simple/", work / "sdist")
    with tarfile.open(archive) as tar:
        tar.extractall(work, filter="data")
    return work / archive.name.removesuffix(".tar.gz")


def build(source, planex2d, netgen, work, staging):
    """the OCC module for one netgen version, installed into staging/planex_occ/<folder>"""
    venv = work / f"venv-{netgen}"
    run(sys.executable, "-m", "venv", venv)
    py = venv_python(venv)
    run(py, "-m", "pip", "install", "-q", f"netgen-mesher=={netgen}", "cmake")
    occt = subprocess.run([py, "-c", "from importlib.metadata import version; print(version('netgen-occt'))"],
                          check=True, capture_output=True, text=True).stdout.strip()
    run(py, "-m", "pip", "install", "-q", f"netgen-occt-devel=={occt}")
    cmake = venv / ("Scripts/cmake.exe" if os.name == "nt" else "bin/cmake")
    out = work / f"build-{netgen}"
    run(cmake, "-S", source, "-B", out, "-DCMAKE_BUILD_TYPE=Release", "-DPLANEX_CORE=OFF", "-DPLANEX_OCC=ON",
        f"-DPLANEX_VERSION={planex2d}", f"-DPLANEX_OCC_DESTINATION=planex_occ/{folder(netgen)}",
        f"-DPython3_EXECUTABLE={py}")
    run(cmake, "--build", out, "--config", "Release", "--parallel")
    run(cmake, "--install", out, "--config", "Release", "--prefix", staging)
    pybind11 = subprocess.run([py, "-c", "import netgen.config, pathlib; print(pathlib.Path(netgen.config.get_cmake_dir()).parents[2])"],
                              check=True, capture_output=True, text=True).stdout.strip()
    licenses(source, Path(pybind11), staging)


def licenses(source, prefix, staging):
    """the license texts of what the modules compile in: Eigen and Taskflow from planex2d's sdist, pybind11 from netgen's
    include folder"""
    out = staging / "licenses"
    out.mkdir(exist_ok=True)
    for name in ("COPYING.MPL2", "COPYING.APACHE", "COPYING.BSD"):
        (out / f"Eigen-{name}").write_bytes((source / "external_dependencies/eigen" / name).read_bytes())
    (out / "Taskflow-LICENSE").write_bytes((source / "external_dependencies/taskflow/LICENSE").read_bytes())
    found = next(prefix.rglob("include/netgen/pybind11/LICENSE"), None)
    if found:
        (out / "pybind11-LICENSE").write_bytes(found.read_bytes())


def reuse(wheels, keep, staging):
    """the module folders of the versions in keep from earlier wheels"""
    for wheel in wheels:
        with zipfile.ZipFile(wheel) as z:
            for name in z.namelist():
                parts = name.split("/")
                if len(parts) > 2 and parts[0] == "planex_occ" and parts[1] in keep:
                    z.extract(name, staging)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--planex2d", required=True, help="the planex2d version to build for (its sdist)")
    ap.add_argument("--index", help="the package index of the sdist (default PyPI), e.g. https://test.pypi.org/simple/")
    ap.add_argument("--sdist", type=Path,
                    help="planex2d's sdist from a file instead of the index (the workflow fetches it once)")
    ap.add_argument("--netgen", nargs="+", required=True, help="the netgen versions to build modules for")
    ap.add_argument("--reuse", nargs="*", default=[], type=Path, help="earlier wheels whose other modules to keep")
    ap.add_argument("--keep", nargs="*", default=[], help="with --reuse: the netgen versions of those modules")
    ap.add_argument("--staging", required=True, type=Path, help="the folder to install into")
    ap.add_argument("--work", default=Path("build-modules"), type=Path, help="scratch folder")
    a = ap.parse_args()
    a.work.mkdir(parents=True, exist_ok=True)
    a.staging.mkdir(parents=True, exist_ok=True)
    source = sdist_of(a.planex2d, a.index, a.work, a.sdist)
    for netgen in a.netgen:
        build(source.resolve(), a.planex2d, netgen, a.work.resolve(), a.staging.resolve())
    reuse(a.reuse, {folder(v) for v in a.keep}, a.staging)
    found = sorted(p.name for p in (a.staging / "planex_occ").iterdir() if p.is_dir())
    print("modules:", ", ".join(found))


if __name__ == "__main__":
    main()
