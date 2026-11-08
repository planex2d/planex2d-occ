# planex2d-occ

planex2d's OpenCASCADE integration for [netgen](https://github.com/NGSolve/netgen): the exports to netgen.occ
(`face.ToOCCFace()`, `px.OCCGeometry(...)`), pads and pockets, sections and projections of OCC shapes.
[planex2d](https://pypi.org/project/planex2d/) itself runs without netgen; install this package to use netgen with it:

```
pip install planex2d[occ]
```

pip then picks the planex2d-occ that fits: every release is built for exactly one planex2d version and for the most
recent netgen-mesher releases, and keeps a netgen you have installed if it is one of them. planex loads the module for
your netgen on import; there is nothing to import yourself.

With a nightly build of netgen or NGSolve (such as 6.2.2608.post78.dev0), install with `--pre`:

```
pip install --pre planex2d[occ]
```

It takes the pre-release of planex2d-occ that has a module for your nightly: it covers netgen's nightlies since its
newest release, up to the newest one its daily build has reached. A nightly published after that build is replaced by
the newest one it covers (pip then warns that your NGSolve no longer fits); the next day's build covers it. A nightly
from before netgen's newest release has no module: name your NGSolve (`pip install --pre planex2d[occ]
ngsolve==<your version>`) so that pip keeps it, and planex runs without its OCC part, with a warning at `import planex`
that names the netgen versions planex2d-occ is built for. Without `--pre`, pip sees only the releases for netgen's real
releases and would install one of those in place of your nightly.

## Versions

- `0.2.0.3` is the third build for planex2d `0.2.0`. A new build comes out when netgen publishes a release (post
  releases included); it then holds modules for the newest netgen releases.
- `0.2.0.4.dev2` is a pre-release after it: modules for netgen's nightly builds since its newest release. A new one comes
  out with each nightly; the next build for a netgen release sorts above it.
- Each release lists the planex2d and netgen-mesher versions it is for in its requirements and its release notes.

## How it is built

The modules are compiled from planex2d's source distribution of the pinned version (its OCC bindings), once per netgen
version, against that netgen and the OpenCASCADE it was built with, using netgen's own pybind11. A scheduled workflow
builds and tests a new release when netgen publishes a release or a nightly build: `.github/workflows/release.yml`, with the scripts in `tools/`.

## In the browser

planex2d.org's playground runs planex2d-occ in Pyodide. PyPI has no Pyodide netgen to depend on, so these files are
not on PyPI. `.github/workflows/pyodide.yml` builds them with `tools/build_pyodide.sh`:
- netgen, NGSolve and OpenCASCADE, at fixed versions (`tools/pyodide/pins.sh`), once per set of pins and the planex2d
  version whose OCC calls OpenCASCADE's exports follow (a later version that needs more gets a new one);
- planex2d-occ for each planex2d version on top, tested in Pyodide under Node.

It attaches the wheels and a Pyodide lock file to this repository's releases `pyodide-base-*` and `pyodide-<planex2d>`.

## License

LGPL-2.1-or-later, as planex2d, except the Pyodide build scripts adapted from NGSolve (LGPL-2.1-only); see `LICENSE`
and `THIRD_PARTY_NOTICES.md`.
