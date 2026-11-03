// SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
// SPDX-License-Identifier: LGPL-2.1-or-later

// planex's tests in Pyodide under Node: the packages from a lock file served over HTTP (serve.py), pytest and
// hypothesis from PyPI, the sdist (or source) folder mounted at /src, pytest run in its tests folder.
//     node run_pytest.mjs <pyodide core folder> <lock address> <load,load> <sdist folder> [pytest args ...]
import path from "node:path";
import { pathToFileURL } from "node:url";

const [core, address, load, tests, ...pytestArgs] = process.argv.slice(2);
const base = address.replace(/\/?$/, "/");
const parsed = JSON.parse(await (await fetch(base + "pyodide-lock.json")).text());
for (const p of Object.values(parsed.packages)) p.file_name = p.file_name.split("/").pop();
const { loadPyodide } = await import(pathToFileURL(path.join(core, "pyodide.mjs")).href);
const py = await loadPyodide({ indexURL: core + "/", packageBaseUrl: base, lockFileContents: JSON.stringify(parsed) });
await py.loadPackage([...load.split(","), "micropip"]);
await py.runPythonAsync("import micropip\nawait micropip.install(['pytest', 'hypothesis'])");
py.FS.mkdirTree("/src");
py.FS.mount(py.FS.filesystems.NODEFS, { root: path.resolve(tests) }, "/src");
py.globals.set("ARGS", pytestArgs);
const status = await py.runPythonAsync(`
import os, sys
os.chdir("/src/tests")
sys.path.insert(0, "/src/tests")
import pytest
int(pytest.main(["-q", "-p", "no:cacheprovider", "-W", "ignore::DeprecationWarning", *ARGS]))
`);
console.log("pytest exit", status);
process.exit(status);
