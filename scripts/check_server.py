#!/usr/bin/env python3
"""check_server.py: is the lab server (teacher / judge) answering? Prints a status only, never the address.
Usage: python3 scripts/check_server.py"""
import pathlib, sys, urllib.error, urllib.request
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gemma_client as g

req = urllib.request.Request(g.BASE + "/models", headers={"User-Agent": g.UA, "Accept": "application/json",
                             **({"Authorization": "Bearer " + g.KEY} if g.KEY else {})})
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        print("OK: server answers, HTTP", r.status)
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", "replace")
    hint = ("Cloudflare 1033: the server's tunnel is down (ask the labmate)" if "1033" in body else
            "403: blocked; try GEMMA_USER_AGENT=curl/8.7.1 in .env" if e.code == 403 else
            "server or tunnel error (5xx): server down or restarting" if e.code >= 500 else "see code")
    print("NOT OK: HTTP", e.code, "-", hint)
except Exception as e:
    print("NOT OK: no connection -", type(e).__name__, "(network, VPN, or server off)")
