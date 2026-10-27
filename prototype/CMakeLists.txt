# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-or-later

# two modules as planex's: _core with pybind11 from pip (any version), _occ with netgen's pybind11 and ngcore's flags,
# linked to netgen and OpenCASCADE from their pip wheels
cmake_minimum_required(VERSION 3.20)
project(conduit_prototype LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)

# PIP_PYBIND11_INCLUDE given: the headers of another pybind11 than the installed one
if(NOT PIP_PYBIND11_INCLUDE)
    execute_process(COMMAND ${Python3_EXECUTABLE} -c "import pybind11; print(pybind11.get_include())"
        OUTPUT_VARIABLE PIP_PYBIND11_INCLUDE OUTPUT_STRIP_TRAILING_WHITESPACE COMMAND_ERROR_IS_FATAL ANY)
endif()
Python3_add_library(_core MODULE WITH_SOABI core.cpp)
target_include_directories(_core PRIVATE ${CMAKE_CURRENT_SOURCE_DIR} ${PIP_PYBIND11_INCLUDE})

# netgen and OpenCASCADE from the pip wheels of the Python that builds (netgen says where its CMake files are)
execute_process(COMMAND ${Python3_EXECUTABLE} -c "import netgen.config; print(netgen.config.get_cmake_dir())"
    OUTPUT_VARIABLE Netgen_DIR OUTPUT_STRIP_TRAILING_WHITESPACE COMMAND_ERROR_IS_FATAL ANY)
execute_process(COMMAND ${Python3_EXECUTABLE} -c "import sys; print(sys.prefix)"
    OUTPUT_VARIABLE PYTHON_PREFIX OUTPUT_STRIP_TRAILING_WHITESPACE COMMAND_ERROR_IS_FATAL ANY)
list(PREPEND CMAKE_PREFIX_PATH ${PYTHON_PREFIX})
find_package(Netgen REQUIRED CONFIG)
find_package(OpenCASCADE REQUIRED CONFIG)

Python3_add_library(_occ MODULE WITH_SOABI occ.cpp)
target_include_directories(_occ PRIVATE ${CMAKE_CURRENT_SOURCE_DIR} $<TARGET_PROPERTY:ngcore,INTERFACE_INCLUDE_DIRECTORIES>
                           ${OpenCASCADE_INCLUDE_DIR})
target_compile_definitions(_occ PRIVATE $<TARGET_PROPERTY:ngcore,INTERFACE_COMPILE_DEFINITIONS> OCCGEOMETRY)
target_compile_options(_occ PRIVATE $<TARGET_PROPERTY:ngcore,INTERFACE_COMPILE_OPTIONS>)
target_link_libraries(_occ PRIVATE nglib ngcore ${NETGEN_OCC_LIBRARIES})
set_target_properties(_occ PROPERTIES
    BUILD_RPATH "${NETGEN_LIBRARY_DIR};${OpenCASCADE_LIBRARY_DIR}"
    INSTALL_RPATH "${NETGEN_LIBRARY_DIR};${OpenCASCADE_LIBRARY_DIR}")

install(TARGETS _core _occ LIBRARY DESTINATION proto)
