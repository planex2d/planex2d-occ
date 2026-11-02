# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-or-later

"""What a release run of planex2d-occ builds, as JSON for the workflow: the main release and the pre-release.

The planex2d is the one given (a pre-release too, by hand) or the newest final release on the index from
--min-planex2d on (a scheduled run; none yet: nothing to build).

The main release has modules for the newest real releases of netgen-mesher on PyPI (final releases: post releases
count, nightlies such as 6.2.2608.post63.dev0 do not), ordered by version, not by upload. The latest main release for
that planex2d says what is released already: the netgen versions it has modules for. None yet builds the whole window;
else only the netgen versions it lacks are built and the others reused from its wheels; nothing new means no release.

The pre-release has modules for netgen's nightlies newer than its newest real release, for a final planex2d from
--min-planex2d-pre on. Its version is the next main release's with .devN (0.2.4.1 released: 0.2.4.2.dev1, .dev2, ...),
so that pip takes it only with --pre and the next main release sorts above it; its modules are reused from the latest
pre-release of the same counter.

Both take only the netgen versions with a wheel for every platform and Python of release.yml's build matrix (BUILT):
a nightly without a Windows wheel, say, is left out on every platform.

    python tools/plan.py --window 6 --index https://test.pypi.org/
"""
import argparse
import json
import urllib.error
import urllib.request

from packaging.requirements import Requirement
from packaging.utils import parse_wheel_filename
from packaging.version import Version

# release.yml's build matrix: for each os the start and the ends of a wheel's platform tag that it installs, the Pythons
BUILT = {"linux": ("manylinux", ("x86_64",)), "macos-arm64": ("macosx", ("arm64", "universal2")),
         "macos-x86_64": ("macosx", ("x86_64", "universal2")), "windows": ("win", ("amd64",))}
PYTHONS = ("3.11", "3.12", "3.13", "3.14")


def releases(index, name):
    """name's versions on the index (its JSON API), with their requirements"""
    try:
        with urllib.request.urlopen(f"{index.rstrip('/')}/pypi/{name}/json") as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {}, []
        raise
    versions = {v: files for v, files in data["releases"].items() if files and not all(f.get("yanked") for f in files)}
    return versions, data["info"].get("requires_dist") or []


def complete(files):
    """whether a release's files hold a wheel for every os and Python of the build matrix (BUILT, PYTHONS)"""
    tags = {t for f in files if f["filename"].endswith(".whl") and not f.get("yanked")
            for t in parse_wheel_filename(f["filename"])[3]}
    return all(any(t.interpreter == "cp" + python.replace(".", "") and t.platform.startswith(start)
                   and t.platform.endswith(ends) for t in tags)
               for start, ends in BUILT.values() for python in PYTHONS)


def netgen():
    """netgen-mesher's versions on PyPI with a wheel for every os and Python of the build matrix"""
    versions, _ = releases("https://pypi.org", "netgen-mesher")
    return [v for v, files in versions.items() if complete(files)]


def window(size, minimum=None):
    """the newest real netgen-mesher releases on PyPI from minimum on (the oldest whose C++ API planex builds
    against), oldest first"""
    final = sorted(Version(v) for v in netgen() if not Version(v).is_prerelease)
    if minimum:
        final = [v for v in final if v >= Version(minimum)]
    return [str(v) for v in final[-size:]]


def nightlies():
    """netgen-mesher's pre-releases on PyPI newer than its newest real release, oldest first"""
    versions, _ = releases("https://pypi.org", "netgen-mesher")
    newest = max(Version(v) for v in versions if not Version(v).is_prerelease)
    return [str(v) for v in sorted(Version(v) for v in netgen() if Version(v).is_prerelease and Version(v) > newest)]


def latest_occ(index, core, counter=None):
    """the latest planex2d-occ built for that planex2d on the index (its version names the core's, see occ_version):
    (version, its netgen versions), or None; with counter, the latest pre-release of that counter instead"""
    versions, _ = releases(index, "planex2d-occ")
    c = Version(core)
    if counter is None:
        mine = [Version(v) for v in versions
                if Version(v).release[:-1] == c.release and len(Version(v).release) == len(c.release) + 1
                and (Version(v).pre, Version(v).post, Version(v).dev) == (c.pre, c.post, c.dev)]
    else:
        mine = [Version(v) for v in versions
                if Version(v).release == c.release + (counter,) and Version(v).dev is not None
                and Version(v).pre is None and Version(v).post is None]
    if not mine:
        return None
    newest = str(max(mine))
    with urllib.request.urlopen(f"{index.rstrip('/')}/pypi/planex2d-occ/{newest}/json") as r:
        requires = json.load(r)["info"].get("requires_dist") or []
    netgen = [window_of(req, counter is not None) for req in map(Requirement, requires) if req.name == "netgen-mesher"]
    return newest, netgen[0] if netgen else []


def window_of(req, nightly=False):
    """the netgen versions a release's requirement admits among netgen's real releases, or among its nightlies"""
    return sorted((v for v in netgen() if Version(v).is_prerelease == nightly and req.specifier.contains(v, prereleases=True)),
                  key=Version)


def occ_version(core, counter):
    """planex2d-occ's version: the core's release numbers, the counter, then the core's pre-, post- or dev-release part
    (0.2.0 -> 0.2.0.1, 0.2.0.dev1 -> 0.2.0.1.dev1)"""
    v = Version(core)
    return f"{v.base_version}.{counter}{str(v)[len(v.base_version):]}"


def plan(want, last, rebuild, version):
    """what a release builds: the netgen versions in want that the last release (version, netgen versions) lacks"""
    if last and not rebuild:
        build = [v for v in want if v not in last[1]]
        keep = [v for v in want if v in last[1]]
        previous = last[0]
    else:
        build, keep, previous = want, [], None
    return {"window": want, "build": build, "keep": keep, "previous": previous, "version": version,
            "release": bool(build), "newest": want[-1] if want else ""}


def nothing():
    return {"window": [], "build": [], "keep": [], "previous": None, "version": "", "release": False, "newest": ""}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--window", type=int, default=6, help="how many netgen releases a wheel has modules for")
    ap.add_argument("--min-netgen", help="the oldest netgen release to build for")
    ap.add_argument("--index", default="https://pypi.org", help="where planex2d and planex2d-occ are released")
    ap.add_argument("--planex2d", help="the planex2d version, a pre-release too (default: the newest final release)")
    ap.add_argument("--min-planex2d", help="the oldest planex2d the default may be (the first with planex2d-occ)")
    ap.add_argument("--min-planex2d-pre", help="the oldest planex2d a pre-release is built for (none: no pre-releases)")
    ap.add_argument("--rebuild", action="store_true", help="build every module anew")
    a = ap.parse_args()
    core = a.planex2d
    if not core:
        cores, _ = releases(a.index, "planex2d")
        finals = [Version(v) for v in cores if not Version(v).is_prerelease]
        finals = [v for v in finals if not a.min_planex2d or v >= Version(a.min_planex2d)]
        if not finals:
            print(json.dumps({"planex2d": "", "main": nothing(), "pre": nothing()}))
            return
        core = str(max(finals))
    last = latest_occ(a.index, core)
    counter = Version(last[0]).release[-1] + 1 if last else 1
    main_plan = plan(window(a.window, a.min_netgen), last, a.rebuild, occ_version(core, counter))
    pre_plan = nothing()
    c = Version(core)
    if a.min_planex2d_pre and not c.is_prerelease and not c.is_postrelease and c >= Version(a.min_planex2d_pre):
        counter = counter + 1 if main_plan["release"] else counter
        last_pre = latest_occ(a.index, core, counter)
        dev = Version(last_pre[0]).dev + 1 if last_pre else 1
        pre_plan = plan(nightlies(), last_pre, a.rebuild, f"{occ_version(core, counter)}.dev{dev}")
    print(json.dumps({"planex2d": core, "main": main_plan, "pre": pre_plan}))


if __name__ == "__main__":
    main()
