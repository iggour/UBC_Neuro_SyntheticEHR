#!/usr/bin/env python3
"""
gemma_client.py
Minimal client for an OpenAI-compatible chat endpoint (vLLM serving Gemma).
Standard library only. Settings are read from .env in the project root (never committed):
    GEMMA_BASE_URL=https://.../v1
    GEMMA_API_KEY=...        (optional)
    GEMMA_MODEL=...          (optional; default: first model the server lists)
"""
import json, os, pathlib, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent

def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

load_env()
BASE = os.environ.get("GEMMA_BASE_URL", "").rstrip("/")
KEY = os.environ.get("GEMMA_API_KEY", "")
# Cloudflare in front of the server blocks Python's default "Python-urllib" User-Agent (HTTP 403),
# so send our own. Override with GEMMA_USER_AGENT in .env if needed.
UA = os.environ.get("GEMMA_USER_AGENT", "hd-anchor-client/0.1")

def _req(path, payload=None, timeout=300):
    if not BASE:
        raise SystemExit("GEMMA_BASE_URL is not set. Add it to .env (see .env.example).")
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, method="POST" if data else "GET")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", UA)
    req.add_header("Accept", "application/json")
    if KEY:
        req.add_header("Authorization", "Bearer " + KEY)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:300]
        raise SystemExit(f"HTTP {e.code} from {BASE + path}\n{body}\n"
                         "If this is 403, try setting GEMMA_USER_AGENT=curl/8.7.1 in .env.")

_model = None
def model():
    global _model
    if _model is None:
        _model = os.environ.get("GEMMA_MODEL") or _req("/models")["data"][0]["id"]
    return _model

def chat(messages, temperature=0.7, max_tokens=300):
    out = _req("/chat/completions", {"model": model(), "messages": messages,
                                     "temperature": temperature, "max_tokens": max_tokens})
    return out["choices"][0]["message"]["content"].strip()

if __name__ == "__main__":
    print("Model:", model())
    print(chat([{"role": "user", "content": "Say hello in one short sentence."}], max_tokens=40))
