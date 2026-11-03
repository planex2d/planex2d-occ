# SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
# SPDX-License-Identifier: LGPL-2.1-or-later

"""A folder over local HTTP for the Node tests: its files as they are, and a file it does not hold redirected to the
address its lock file names for it (the stock packages on jsDelivr, planex2d on PyPI).
    python3 serve.py <folder> <port>"""
import functools
import http.server
import json
import os
import sys

ADDRESSES = {p["file_name"].split("/")[-1]: p["file_name"] for p in
             json.load(open(os.path.join(sys.argv[1], "pyodide-lock.json")))["packages"].values()
             if p["file_name"].startswith("https://")}


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        name = self.path.lstrip("/").split("?")[0]
        if name in ADDRESSES and not os.path.exists(os.path.join(sys.argv[1], name)):
            target = ADDRESSES[name]
            self.send_response(302)
            self.send_header("Location", target)
            self.end_headers()
            return
        super().do_GET()


http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[2])),
                                functools.partial(Handler, directory=sys.argv[1])).serve_forever()
