# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-or-later

"""The tables of a WebAssembly side module the Pyodide build reads: the names it imports and the names it exports."""
from pathlib import Path


def _leb(data, i):
    result = shift = 0
    while True:
        byte = data[i]
        i += 1
        result |= (byte & 0x7F) << shift
        shift += 7
        if byte < 0x80:
            return result, i


def _name(data, i):
    n, i = _leb(data, i)
    return data[i:i + n].decode("utf-8", "replace"), i + n


def _sections(data):
    i = 8
    while i < len(data):
        kind = data[i]
        size, i = _leb(data, i + 1)
        yield kind, data[i:i + size]
        i += size


def _imports(body):
    n, i = _leb(body, 0)
    names = []
    for _ in range(n):
        module, i = _name(body, i)
        field, i = _name(body, i)
        kind = body[i]
        i += 1
        if kind == 0:
            _, i = _leb(body, i)
        elif kind in (1, 2):
            i += kind == 1
            flags, i = _leb(body, i)
            _, i = _leb(body, i)
            if flags & 1:
                _, i = _leb(body, i)
        elif kind == 3:
            i += 2
        elif kind == 4:
            _, i = _leb(body, i + 1)
        if module in ("env", "GOT.func", "GOT.mem"):
            names.append(field)
    return names


def _exports(body):
    n, i = _leb(body, 0)
    names = []
    for _ in range(n):
        name, i = _name(body, i)
        _, i = _leb(body, i + 1)
        names.append(name)
    return names


def tables(path):
    """(the names a side module imports, the names it exports), as sets"""
    imports, exports = set(), set()
    for kind, body in _sections(Path(path).read_bytes()):
        if kind == 2:
            imports |= set(_imports(body))
        elif kind == 7:
            exports |= set(_exports(body))
    return imports, exports
