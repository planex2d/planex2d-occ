# Third-party notices

planex2d-occ is Copyright (C) 2026 Sebastian Hirnschall.

```
planex2d-occ is free software; you can redistribute it and/or modify it under the terms of the
GNU Lesser General Public License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

planex2d-occ is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Lesser General Public License (the file LICENSE) for more details.
```

Its compiled modules (`planex_occ/ng_*/_planex_occ`) are built from planex2d's source distribution of the pinned
version and contain code from the third-party libraries Eigen, Taskflow and pybind11 (header-only, compiled in). They
are linked to the libraries Netgen and Open CASCADE Technology, which are not part of planex2d-occ and are installed
separately.

- Eigen 3.4.0 (https://gitlab.com/libeigen/eigen), compiled with `EIGEN_MPL2_ONLY`: Mozilla Public License 2.0, one file
  (`BFloat16.h`) under the Apache License 2.0 and one under the BSD 3-clause license. The Source Code Form of every
  Eigen file compiled in is in planex2d's source distribution (`external_dependencies/eigen`). The license texts are
  in the wheel's `licenses` folder (`Eigen-COPYING.*`). The Apache License 2.0 is compatible with version 3 of the GNU
  LGPL but not with version 2.1, so the compiled modules as a whole can be passed on under version 3 or later of the
  LGPL, which the "or any later version" of the license above allows.
- Taskflow 4.1.0 (https://github.com/taskflow/taskflow): MIT, Copyright (c) 2018-2026 Dr. Tsung-Wei Huang; the text
  is `licenses/Taskflow-LICENSE`.
- pybind11 (https://github.com/pybind/pybind11), the copy bundled in the netgen-mesher package each module is built
  against: BSD 3-clause; the text is `licenses/pybind11-LICENSE`.

## Libraries planex2d-occ uses but does not include

The modules are linked dynamically to these libraries and compile material from their header files (inline functions
and templates). They are installed separately, as the netgen-mesher and netgen-occt packages on PyPI.

- Netgen, including ngcore, by Joachim Schöberl and contributors, https://github.com/NGSolve/netgen: Netgen and its
  use are covered by the GNU Lesser General Public License version 2.1, whose text is the file `LICENSE`.
- Open CASCADE Technology (OCCT), https://dev.opencascade.org: planex2d-occ makes use of facilities provided by the
  Open CASCADE Technology software. OCCT is covered by the GNU Lesser General Public License version 2.1 (the text: the
  file `LICENSE`) with the Open CASCADE exception, quoted from the file `OCCT_LGPL_EXCEPTION.txt` of the OCCT source:

```
Open CASCADE exception (version 1.0) to GNU LGPL version 2.1.

The object code (i.e. not a source) form of a "work that uses the Library"
can incorporate material from a header file that is part of the Library.
As a special exception to the GNU Lesser General Public License version 2.1,
you may distribute such object code incorporating material from header files
provided with the Open CASCADE Technology libraries (including code of CDL
generic classes) under terms of your choice, provided that you give
prominent notice in supporting documentation to this code that it makes use
of or is based on facilities provided by the Open CASCADE Technology software.
```
