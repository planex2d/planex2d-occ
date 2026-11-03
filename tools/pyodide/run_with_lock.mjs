// SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
// SPDX-License-Identifier: LGPL-2.1-or-later

// Runs a Python script in Pyodide under Node with a lock file of our own: the packages named are loaded from it
// (its stock entries on jsDelivr, ours as files next to it), then micropip installs the rest from PyPI.
//     node run_with_lock.mjs <pyodide core folder> <lock folder or its http address> <load,load> <script.py> [file ...] [-- package ...]
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const args = process.argv.slice(2);
const cut = args.indexOf("--");
const [core, lockFolder, load, ...files] = cut < 0 ? args : args.slice(0, cut);
const packages = cut < 0 ? [] : args.slice(cut + 1);
const { loadPyodide } = await import(pathToFileURL(path.join(core, "pyodide.mjs")).href);
const t0 = performance.now();
const base = lockFolder.startsWith("http") ? lockFolder.replace(/\/?$/, "/") : path.resolve(lockFolder) + "/";
// under Node Pyodide puts the base before absolute addresses too: the test's copy names every file by its name, and
// serve.py redirects those it does not hold to their address in the lock
const text = base.startsWith("http") ? await (await fetch(base + "pyodide-lock.json")).text()
                                     : fs.readFileSync(base + "pyodide-lock.json", "utf8");
const parsed = JSON.parse(text);
for (const p of Object.values(parsed.packages)) p.file_name = p.file_name.split("/").pop();
const lock = { lockFileContents: JSON.stringify(parsed) };
const py = await loadPyodide({ indexURL: core + "/", packageBaseUrl: base, ...lock });
const t1 = performance.now();
await py.loadPackage(load.split(","));
const t2 = performance.now();
console.log(`pyodide ${Math.round(t1 - t0)} ms, packages ${Math.round(t2 - t1)} ms`);
if (packages.length) {
  await py.loadPackage("micropip");
  py.globals.set("PACKAGES", packages);
  await py.runPythonAsync("import micropip\nawait micropip.install(list(PACKAGES))");
}
py.FS.mkdirTree("/work");
const argv = files.map(f => {
  py.FS.writeFile("/work/" + path.basename(f), fs.readFileSync(f));
  return "/work/" + path.basename(f);
});
py.globals.set("ARGV", argv);
await py.runPythonAsync("import sys, runpy\nsys.argv = list(ARGV)\nrunpy.run_path(sys.argv[0], run_name='__main__')");
