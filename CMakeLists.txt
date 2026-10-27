# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-or-later

# planex2d-occ's wheel: the loader and the modules tools/build_modules.py built from planex2d's sdist, one folder per
# netgen version (planex_occ/ng_6_2_2608/_planex_occ...), in PLANEX_OCC_STAGING
cmake_minimum_required(VERSION 3.20)
project(planex2d_occ LANGUAGES NONE)

if(NOT PLANEX_OCC_STAGING OR NOT IS_DIRECTORY "${PLANEX_OCC_STAGING}/planex_occ")
    message(FATAL_ERROR "PLANEX_OCC_STAGING: the folder tools/build_modules.py filled (it holds planex_occ/ng_*)")
endif()
install(DIRECTORY "${PLANEX_OCC_STAGING}/planex_occ/" DESTINATION planex_occ)
install(FILES src/planex_occ/__init__.py DESTINATION planex_occ)
