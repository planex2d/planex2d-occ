# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-or-later

"""Download planex2d's sdist of one version from a package index without building anything (pip download prepares
the package's metadata, which installs its build requirements from that same index). A copy already in dest with the
index's sha256 is kept (the workflow's jobs check the artifact they were given: a download can arrive cut off), any
other is replaced.

    python tools/sdist.py 0.2.0 https://pypi.org/simple/ core-sdist
"""
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path


def download(planex2d, index, dest):
    """planex2d-<version>.tar.gz from the index's simple API (its JSON form), checked against the index's sha256; a copy
    in dest that matches it is kept"""
    name = f"planex2d-{planex2d}.tar.gz"
    page = f"{index.rstrip('/')}/planex2d/"
    request = urllib.request.Request(page, headers={"Accept": "application/vnd.pypi.simple.v1+json"})
    with urllib.request.urlopen(request) as r:
        files = json.load(r)["files"]
    entry = next((f for f in files if f["filename"] == name), None)
    if entry is None:
        raise SystemExit(f"{name} is not on {index}")
    sha256 = entry["hashes"]["sha256"]
    path = Path(dest) / name
    if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == sha256:
        return path
    with urllib.request.urlopen(urllib.parse.urljoin(page, entry["url"])) as r:
        data = r.read()
    if hashlib.sha256(data).hexdigest() != sha256:
        raise SystemExit(f"{name}: the download does not match the index's sha256")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


if __name__ == "__main__":
    print(download(*sys.argv[1:4]))
