# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-or-later

"""Write a release's version and dependencies into pyproject.toml: planex2d exactly, netgen-mesher within the versions
the wheel has modules for, with != for a release in that range it has none for.

    python tools/metadata.py --version 0.2.0.3 --planex2d 0.2.0 --netgen 6.2.2603 6.2.2604 6.2.2605
"""
import argparse
import re
from pathlib import Path

from packaging.version import Version


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--version", required=True)
    ap.add_argument("--planex2d", required=True)
    ap.add_argument("--netgen", nargs="+", required=True, help="the netgen versions the wheel has modules for")
    ap.add_argument("--exclude", nargs="*", default=[], help="releases in that range without a module")
    ap.add_argument("--pyproject", default=Path("pyproject.toml"), type=Path)
    a = ap.parse_args()
    netgen = sorted(a.netgen, key=Version)
    spec = ",".join([f">={netgen[0]}", f"<={netgen[-1]}"] + [f"!={v}" for v in a.exclude])
    text = a.pyproject.read_text()
    text = re.sub(r'^version = "[^"]*"', f'version = "{a.version}"', text, count=1, flags=re.M)
    text = re.sub(r'^dependencies = \[[^\]]*\]', f'dependencies = ["planex2d=={a.planex2d}", "netgen-mesher{spec}"]', text,
                  count=1, flags=re.M)
    a.pyproject.write_text(text)
    print(f"planex2d-occ {a.version}: planex2d=={a.planex2d}, netgen-mesher{spec}")


if __name__ == "__main__":
    main()
