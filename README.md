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

## Versions

- `0.2.0.3` is the third build for planex2d `0.2.0`. A new build comes out when netgen publishes a release (post
  releases included, nightly builds not); it then holds modules for the newest netgen releases.
- Each release lists the planex2d and netgen-mesher versions it is for in its requirements and its release notes.

## How it is built

The modules are compiled from planex2d's source distribution of the pinned version (its OCC bindings), once per netgen
version, against that netgen and the OpenCASCADE it was built with, using netgen's own pybind11. A scheduled workflow
builds and tests a new release when netgen publishes one: `.github/workflows/release.yml`, with the scripts in `tools/`.

## License

LGPL-2.1-or-later, as planex2d; see `LICENSE` and `THIRD_PARTY_NOTICES.md`.
