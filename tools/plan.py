# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-or-later

"""What a release run of planex2d-occ builds, as JSON for the workflow.

The window is the newest real releases of netgen-mesher on PyPI (final releases: post releases count, nightlies such
as 6.2.2608.post63.dev0 do not), ordered by version, not by upload. The latest planex2d-occ on the index says what is
released already: its planex2d and the netgen versions it has modules for. A new planex2d rebuilds the whole window;
else only the netgen versions the latest release lacks are built and the others reused from its wheels; nothing new
means no release.

    python tools/plan.py --window 6 --index https://test.pypi.org/
"""
import argparse
import json
import urllib.error
import urllib.request

from packaging.requirements import Requirement
from packaging.version import Version


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


def window(size, minimum=None):
    """the newest real netgen-mesher releases on PyPI from minimum on (the oldest whose C++ API planex builds
    against), oldest first"""
    versions, _ = releases("https://pypi.org", "netgen-mesher")
    final = sorted(Version(v) for v in versions if not Version(v).is_prerelease)
    if minimum:
        final = [v for v in final if v >= Version(minimum)]
    return [str(v) for v in final[-size:]]


def latest_occ(index):
    """the latest planex2d-occ on the index: (version, its planex2d, its netgen versions), or None"""
    versions, _ = releases(index, "planex2d-occ")
    if not versions:
        return None
    newest = max(versions, key=Version)
    with urllib.request.urlopen(f"{index.rstrip('/')}/pypi/planex2d-occ/{newest}/json") as r:
        requires = json.load(r)["info"].get("requires_dist") or []
    core, netgen = None, []
    for text in requires:
        req = Requirement(text)
        if req.name == "planex2d":
            core = next(iter(req.specifier)).version
        elif req.name == "netgen-mesher":
            netgen = window_of(req)
    return newest, core, netgen


def window_of(req):
    """the netgen versions a release's requirement admits among netgen's real releases"""
    versions, _ = releases("https://pypi.org", "netgen-mesher")
    return sorted((v for v in versions if not Version(v).is_prerelease and req.specifier.contains(v)), key=Version)


def occ_version(core, counter):
    """planex2d-occ's version: the core's release numbers, the counter, then the core's pre-, post- or dev-release part
    (0.2.0 -> 0.2.0.1, 0.2.0.dev1 -> 0.2.0.1.dev1)"""
    v = Version(core)
    return f"{v.base_version}.{counter}{str(v)[len(v.base_version):]}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--window", type=int, default=6, help="how many netgen releases a wheel has modules for")
    ap.add_argument("--min-netgen", help="the oldest netgen release to build for")
    ap.add_argument("--index", default="https://pypi.org", help="where planex2d and planex2d-occ are released")
    ap.add_argument("--planex2d", help="the planex2d version (default: the newest on the index)")
    ap.add_argument("--rebuild", action="store_true", help="build every module of the window anew")
    a = ap.parse_args()
    cores, _ = releases(a.index, "planex2d")
    if not a.planex2d and not cores:
        raise SystemExit(f"no planex2d on {a.index}: release the core first, or give --planex2d")
    core = a.planex2d or str(max(Version(v) for v in cores))
    want = window(a.window, a.min_netgen)
    last = latest_occ(a.index)
    same = last is not None and last[1] == core
    counter = Version(last[0]).release[len(Version(core).release)] + 1 if same else 1
    if same and not a.rebuild:
        build = [v for v in want if v not in last[2]]
        keep = [v for v in want if v in last[2]]
        previous = last[0]
    else:
        build, keep, previous = want, [], None
    version = occ_version(core, counter)
    print(json.dumps({"planex2d": core, "window": want, "build": build, "keep": keep, "previous": previous,
                      "version": version, "release": bool(build)}))


if __name__ == "__main__":
    main()
