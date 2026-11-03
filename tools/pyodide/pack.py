# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-or-later

"""The Pyodide wheels, in the layout of NGSolve's own Pyodide wheels, with the license texts of what each holds:

    python3 pack.py base <folder> <out>
        <out>/<BASE>/: netgen_mesher (netgen/, pyngcore/, netgen_mesher.libs/ with libnglib, libngcore and libocct,
        OpenCASCADE's one side module), ngsolve (ngsolve/, ngsolve.libs/libopenblas.so) and NOTICES.txt
    python3 pack.py planex <folder> <planex2d version> <planex2d-occ repository> <out>
        <out>/<version>/: planex2d_occ (the loader and planex_occ/ng_<netgen>/_planex_occ) and pyodide-lock.json:
        Pyodide's own lock with its packages on jsDelivr, planex2d from PyPI, the base wheels in ../<BASE>/

Every side module gets the runtime paths to netgen_mesher.libs and ngsolve.libs, as NGSolve's wheels have them, so
that Pyodide finds the libraries it needs. The pins come from pins.sh (in the environment).
"""
import base64
import csv
import hashlib
import io
import json
import os
import sys
import urllib.request
import zipfile
from pathlib import Path

PIN = os.environ
TAG = f"cp{PIN['PYTHON_VERSION'].replace('.', '')[:3]}-cp{PIN['PYTHON_VERSION'].replace('.', '')[:3]}-pyemscripten_{PIN['PYODIDE_ABI']}_wasm32"
CDN = f"https://cdn.jsdelivr.net/pyodide/v{PIN['PYODIDE_VERSION']}/full/"
DATE = (2026, 1, 1, 0, 0, 0)


def leb(n):
    out = bytearray()
    while True:
        byte, n = n & 0x7F, n >> 7
        out.append(byte | (0x80 if n else 0))
        if not n:
            return bytes(out)


def read_leb(data, i):
    result = shift = 0
    while True:
        byte = data[i]
        i += 1
        result |= (byte & 0x7F) << shift
        shift += 7
        if byte < 0x80:
            return result, i


def with_runtime_path(data, paths):
    """the side module with the runtime paths of its dylink.0 section (its first) set to paths"""
    i = 8
    assert data[i] == 0, "a side module starts with its dylink.0 section"
    size, start = read_leb(data, i + 1)
    end = start + size
    length, j = read_leb(data, start)
    assert data[j:j + length] == b"dylink.0"
    j += length
    kept = bytearray(data[start:j])
    while j < end:
        kind = data[j]
        n, k = read_leb(data, j + 1)
        if kind != 5:
            kept += data[j:k + n]
        j = k + n
    body = leb(len(paths)) + b"".join(leb(len(p.encode())) + p.encode() for p in paths)
    kept += bytes([5]) + leb(len(body)) + body
    return data[:8] + bytes([0]) + leb(len(kept)) + bytes(kept) + data[end:]


def relinked(files):
    """every side module with the runtime paths to netgen_mesher.libs and ngsolve.libs, counted from its folder"""
    out = {}
    for path, data in files.items():
        if path.endswith(".so"):
            up = "/".join([".."] * path.count("/"))
            data = with_runtime_path(data, [f"$ORIGIN/{up}/netgen_mesher.libs", f"$ORIGIN/{up}/ngsolve.libs"])
        out[path] = data
    return out


def wheel(out, name, version, files, requires, licenses):
    """a wheel of {path: bytes}, with METADATA, WHEEL, the license texts ({name: bytes}) and RECORD"""
    info = f"{name}-{version}.dist-info"
    files = relinked(files)
    meta = ["Metadata-Version: 2.1", f"Name: {name.replace('_', '-')}", f"Version: {version}"]
    files[f"{info}/METADATA"] = ("\n".join(meta + [f"Requires-Dist: {r}" for r in requires]) + "\n").encode()
    files[f"{info}/WHEEL"] = (f"Wheel-Version: 1.0\nGenerator: planex2d-occ tools/pyodide/pack.py\n"
                              f"Root-Is-Purelib: false\nTag: {TAG}\n").encode()
    for license_name, data in licenses.items():
        files[f"{info}/licenses/{license_name}"] = data
    record = io.StringIO()
    writer = csv.writer(record, lineterminator="\n")
    for path, data in sorted(files.items()):
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        writer.writerow([path, f"sha256={digest}", len(data)])
    writer.writerow([f"{info}/RECORD", "", ""])
    files[f"{info}/RECORD"] = record.getvalue().encode()
    target = out / f"{name}-{version}-{TAG}.whl"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for path, data in sorted(files.items()):
            z.writestr(zipfile.ZipInfo(path, DATE), data, zipfile.ZIP_DEFLATED)
    return target


def tree(folder, prefix):
    """{prefix/path: bytes} of a folder, without caches and static archives"""
    return {f"{prefix}/{p.relative_to(folder).as_posix()}": p.read_bytes() for p in sorted(folder.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".a"}


def zipped(archive, member):
    with zipfile.ZipFile(archive) as z:
        return z.read(member)


def entry(name, version, file_name, path, imports, depends):
    return {"name": name, "version": version, "file_name": file_name, "install_dir": "site",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "package_type": "package", "imports": imports,
            "depends": depends, "unvendored_tests": False}


def base(root, out):
    out = out / PIN["BASE"]
    out.mkdir(parents=True, exist_ok=True)
    python = root / "prefix/netgen/python"
    occt = root / f"src/OCCT-{PIN['OCC_VERSION']}"
    netgen_src = root / "src/ngsolve/external_dependencies/netgen"
    zlib = zipped(root / f"dl/zlib-v{PIN['ZLIB_VERSION']}.zip", f"zlib-{PIN['ZLIB_VERSION']}/LICENSE")
    libs = {f"netgen_mesher.libs/{n}": (python / n).read_bytes() for n in ("libnglib.so", "libngcore.so")}
    libs["netgen_mesher.libs/libocct.so"] = (root / "prefix/occt/lib/libocct.so").read_bytes()
    wheels = [
        wheel(out, "netgen_mesher", PIN["NETGEN_VERSION"],
              {**tree(python / "netgen", "netgen"), **tree(python / "pyngcore", "pyngcore"), **libs}, ["numpy"],
              {"netgen-LICENSE": (netgen_src / "LICENSE").read_bytes(),
               "pybind11-LICENSE": (root / "prefix/netgen/include/pybind11/LICENSE").read_bytes(),
               "OCCT-LICENSE_LGPL_21.txt": (occt / "LICENSE_LGPL_21.txt").read_bytes(),
               "OCCT_LGPL_EXCEPTION.txt": (occt / "OCCT_LGPL_EXCEPTION.txt").read_bytes(), "zlib-LICENSE": zlib}),
        wheel(out, "ngsolve", PIN["NGSOLVE_VERSION"],
              {**tree(python / "ngsolve", "ngsolve"), "ngsolve.libs/libopenblas.so": (root / "dist/libopenblas.so").read_bytes()},
              [f"netgen-mesher=={PIN['NETGEN_VERSION']}", "numpy"],
              {"NGSolve-LICENSE": (root / "src/ngsolve/LICENSE").read_bytes(),
               "OpenBLAS-LICENSE": (root / "dl/OpenBLAS-LICENSE").read_bytes()}),
    ]
    occ = PIN["OCC_VERSION"].replace("_", ".")
    (out / "NOTICES.txt").write_text(f"""These files run netgen, NGSolve and Open CASCADE Technology in Pyodide {PIN['PYODIDE_VERSION']}, for planex2d-occ.
They are built from unchanged sources with build settings of planex2d-occ's tools/pyodide/ (github.com/planex2d/planex2d-occ),
which follow NGSolve's own Pyodide build: OpenCASCADE as one shared library that exports what netgen, NGSolve and
planex2d-occ use (the linker leaves out the rest), NGSolve's two build patches (pybind11's exception flag, OpenCASCADE's
signal handling). The complete sources are the release
pyodide-base-{PIN['BASE']} of that repository (pyodide-base-{PIN['BASE']}-sources.tar).

- netgen {PIN['NETGEN_VERSION']} (commit {PIN['NETGEN_COMMIT']}), https://github.com/NGSolve/netgen: GNU LGPL 2.1
- NGSolve {PIN['NGSOLVE_VERSION']} (commit {PIN['NGSOLVE_COMMIT']}), https://github.com/NGSolve/ngsolve: GNU LGPL 2.1
- Open CASCADE Technology {occ}, https://dev.opencascade.org: GNU LGPL 2.1 with the Open CASCADE exception. This software
  makes use of facilities provided by the Open CASCADE Technology software.
- pybind11 (netgen's copy, commit {PIN['PYBIND11_COMMIT']}): BSD 3-clause
- zlib {PIN['ZLIB_VERSION']}, https://zlib.net: zlib license
- OpenBLAS {PIN['OPENBLAS_VERSION']} (Pyodide's build), https://www.openblas.net: BSD 3-clause

The license texts are in each wheel's .dist-info/licenses folder. planex2d-occ is not affiliated with these projects.
""")
    for w in wheels:
        print(w.name, round(w.stat().st_size / 1e6, 1), "MB")


def planex(root, version, repository, out):
    shared = out / PIN["BASE"]
    out = out / version
    out.mkdir(parents=True, exist_ok=True)
    sdist = root / f"src/planex/planex2d-{version}"
    folder = "ng_" + PIN["NETGEN_VERSION"].replace(".", "_")
    module = next((root / f"prefix/planex-{version}").rglob("_planex_occ*.so"))
    licenses = {"LICENSE": (repository / "LICENSE").read_bytes(),
                "THIRD_PARTY_NOTICES.md": (repository / "THIRD_PARTY_NOTICES.md").read_bytes(),
                "Taskflow-LICENSE": (sdist / "external_dependencies/taskflow/LICENSE").read_bytes(),
                "pybind11-LICENSE": (root / "prefix/netgen/include/pybind11/LICENSE").read_bytes()}
    for name in ("COPYING.MPL2", "COPYING.APACHE", "COPYING.BSD"):
        licenses[f"Eigen-{name}"] = (sdist / "external_dependencies/eigen" / name).read_bytes()
    occ = wheel(out, "planex2d_occ", f"{version}.1",
                {"planex_occ/__init__.py": (repository / "src/planex_occ/__init__.py").read_bytes(),
                 f"planex_occ/{folder}/{module.name}": module.read_bytes()},
                [f"planex2d=={version}", f"netgen-mesher=={PIN['NETGEN_VERSION']}"], licenses)

    lock = json.loads((root / "dl/pyodide-lock.json").read_text())
    for p in lock["packages"].values():
        if not p["file_name"].startswith("https://"):
            p["file_name"] = CDN + p["file_name"]
    with urllib.request.urlopen(f"https://pypi.org/pypi/planex2d/{version}/json") as r:
        core = next(u for u in json.load(r)["urls"] if u["filename"].endswith(f"{TAG}.whl"))
    lock["packages"]["planex2d"] = {"name": "planex2d", "version": version, "file_name": core["url"],
                                    "install_dir": "site", "sha256": core["digests"]["sha256"],
                                    "package_type": "package", "imports": ["planex"], "depends": ["numpy"],
                                    "unvendored_tests": False}
    netgen = next(shared.glob("netgen_mesher-*.whl"))
    ngsolve = next(shared.glob("ngsolve-*.whl"))
    lock["packages"]["netgen-mesher"] = entry("netgen-mesher", PIN["NETGEN_VERSION"], f"../{PIN['BASE']}/{netgen.name}",
                                              netgen, ["netgen", "pyngcore"], ["numpy"])
    lock["packages"]["ngsolve"] = entry("ngsolve", PIN["NGSOLVE_VERSION"], f"../{PIN['BASE']}/{ngsolve.name}", ngsolve,
                                        ["ngsolve"], ["netgen-mesher", "numpy"])
    lock["packages"]["planex2d-occ"] = entry("planex2d-occ", f"{version}.1", occ.name, occ, ["planex_occ"],
                                             ["planex2d", "netgen-mesher"])
    (out / "pyodide-lock.json").write_text(json.dumps(lock, indent=1))
    print(occ.name, round(occ.stat().st_size / 1e6, 2), "MB")


if __name__ == "__main__":
    if sys.argv[1] == "base":
        base(Path(sys.argv[2]), Path(sys.argv[3]))
    else:
        planex(Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]), Path(sys.argv[5]))
