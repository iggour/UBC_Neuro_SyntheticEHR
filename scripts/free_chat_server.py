#!/usr/bin/env python3
"""
free_chat_server.py
Local-only free-text chat test for scenario B2. The browser talks to this small proxy on 127.0.0.1 and
the proxy talks to the Gemma server, so the server address and any key never reach the page.
Not part of the website; never deploy it.

Usage:
    cp free_chat_config.example.json free_chat_config.json      (fill in base_url; git-ignored)
    python3 scripts/free_chat_server.py
    then open http://127.0.0.1:8770

Each message goes through free_chat_safety.py: possible real distress stops the role-play before
anything is sent to the model, and every reply is checked before it is shown. Conversations are
written only to runtime/transcripts/free_chat/ (git-ignored).
"""
import datetime, http.server, json, pathlib, re, secrets, socket, sys, time, urllib.error, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import free_chat_safety as fs

ROOT = fs.ROOT
CONFIG = ROOT / "free_chat_config.json"
SCENARIO = "B2_driving_and_independence"
PAGE = pathlib.Path(__file__).with_name("free_chat_page.html")
SITE = ROOT / "web" / "hd_anchor_v2.html"
DEFAULTS = {"model": "", "api_key": "", "temperature": 0.3, "max_tokens": 300, "timeout_s": 30, "port": 8770,
            "user_agent": "hd-anchor-client/0.1", "log_dir": str(ROOT / "runtime" / "transcripts" / "free_chat")}
MAX_CHARS, MAX_TURNS, MAX_BODY = 1500, 40, 16384      # the GPU is shared, so one conversation stays small
FALLBACK = "Ruth: Sorry, where was I? Could you put that another way?"
ERRORS = {"timeout": "The AI server took too long to reply.", "bad_response": "The AI server sent a reply that could not be read."}


class UpstreamError(Exception):
    pass


def load_config():
    if not CONFIG.exists():
        raise SystemExit("free_chat_config.json not found. Copy free_chat_config.example.json and fill in base_url.")
    cfg = {**DEFAULTS, **json.loads(CONFIG.read_text(encoding="utf-8"))}
    if not cfg.get("base_url"):
        raise SystemExit("Set base_url in free_chat_config.json.")
    return cfg


def upstream(cfg, path, payload=None):
    """Call the model server. Errors name only a kind, never the address, because they reach the page and the log."""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(cfg["base_url"].rstrip("/") + path, data=data, method="POST" if data else "GET")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", cfg["user_agent"])     # Cloudflare blocks Python's default User-Agent
    if cfg["api_key"]:
        req.add_header("Authorization", "Bearer " + cfg["api_key"])
    try:
        with urllib.request.urlopen(req, timeout=cfg["timeout_s"]) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise UpstreamError(f"http_{e.code}") from None
    except (socket.timeout, TimeoutError):
        raise UpstreamError("timeout") from None
    except urllib.error.URLError as e:
        raise UpstreamError("timeout" if isinstance(e.reason, (socket.timeout, TimeoutError)) else "network") from None
    except ValueError:
        raise UpstreamError("bad_response") from None


def model_name(cfg):
    if not cfg["model"]:
        try:
            cfg["model"] = upstream(cfg, "/models")["data"][0]["id"]
        except (KeyError, IndexError, TypeError):
            raise UpstreamError("bad_response") from None
    return cfg["model"]


def ask_model(cfg, messages):
    out = upstream(cfg, "/chat/completions", {"model": model_name(cfg), "messages": messages,
                                              "temperature": cfg["temperature"], "max_tokens": cfg["max_tokens"]})
    try:
        choice = out["choices"][0]
        text, finish = (choice["message"]["content"] or "").strip(), choice.get("finish_reason")
    except (KeyError, IndexError, TypeError, AttributeError):
        raise UpstreamError("bad_response") from None
    if finish == "length":      # cut off at max_tokens: keep whole sentences only
        m = re.search(r"^.*[.!?][\"')]?", text, re.S)
        text = m.group(0) if m else text
    return text, finish


class Session:
    def __init__(self, cfg):
        self.cfg, self.id, self.facts = cfg, secrets.token_hex(8), fs.load_facts(SCENARIO)
        persona = self.facts["card"]["persona"]
        self.opening = persona["opening_line"]
        self.msgs = [{"role": "system", "content": fs.system_prompt(SCENARIO)}, {"role": "assistant", "content": self.opening}]
        self.turns, self.stopped = 0, False
        logs = pathlib.Path(cfg["log_dir"])
        logs.mkdir(parents=True, exist_ok=True)
        self.log_path = logs / f"B2_{datetime.datetime.now():%Y%m%d_%H%M%S}_{self.id[:6]}.jsonl"
        self.log("start", scenario=SCENARIO, temperature=cfg["temperature"], max_tokens=cfg["max_tokens"], opening=self.opening)

    def log(self, event, **fields):
        row = {"time": datetime.datetime.now().isoformat(timespec="seconds"), "event": event, **fields}
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def say(self, text):
        if self.stopped:
            return {"status": "crisis"}
        if self.turns >= MAX_TURNS:
            return {"status": "ended", "message": "This test conversation has reached its limit. Start a new one."}
        self.log("clinician", text=text)
        if fs.looks_like_distress(text):      # checked first, so these words are never sent to the model
            self.stopped = True
            self.log("crisis_stop")
            return {"status": "crisis"}
        self.msgs.append({"role": "user", "content": text})
        started = time.time()
        try:
            reply, finish = ask_model(self.cfg, self.msgs)
        except UpstreamError as e:
            self.msgs.pop()     # so the same message can be sent again
            self.log("error", kind=str(e), seconds=round(time.time() - started, 2))
            return {"status": "error", "kind": str(e), "message": ERRORS.get(str(e), "The AI server could not be reached.")}
        seconds = round(time.time() - started, 2)
        self.turns += 1
        reasons = fs.check_reply(reply, self.facts)
        if reasons:
            self.log("withheld", text=reply, reasons=reasons, seconds=seconds, finish=finish)
            self.log("fallback", text=FALLBACK)
            self.msgs.append({"role": "assistant", "content": FALLBACK})     # the failed reply stays out of the history
            return {"status": "ok", "lines": self.lines(FALLBACK), "withheld": sorted({r[0] for r in reasons})}
        self.log("patient", text=reply, seconds=seconds, finish=finish)
        self.msgs.append({"role": "assistant", "content": reply})
        return {"status": "ok", "lines": self.lines(reply), "seconds": seconds}

    def lines(self, text):
        return [{"speaker": s, "text": t.replace("*", "")} for s, t in fs.split_speakers(text, self.facts)]


class Handler(http.server.BaseHTTPRequestHandler):
    sessions = {}
    cfg = None

    def log_message(self, *args):       # keep the terminal quiet; the JSONL file is the record
        pass

    def send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def local_request(self):
        """Refuse other websites open in the same browser: they could otherwise post to this port."""
        hosts = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        origin = self.headers.get("Origin")
        return self.headers.get("Host") in hosts and (origin is None or origin.split("//")[-1] in hosts)

    def do_GET(self):
        if not self.local_request():
            return self.send(403, {"status": "forbidden"})
        path = self.path.split("?")[0]
        if path == "/":
            return self.send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        if path == "/site":
            return self.send(200, SITE.read_bytes(), "text/html; charset=utf-8")
        self.send(404, {"status": "not found"})

    def do_POST(self):
        if not self.local_request() or not self.headers.get("Content-Type", "").startswith("application/json"):
            return self.send(403, {"status": "forbidden"})
        size = int(self.headers.get("Content-Length") or 0)
        if size > MAX_BODY:
            return self.send(413, {"status": "too large"})
        try:
            body = json.loads(self.rfile.read(size).decode("utf-8") or "{}")
        except ValueError:
            return self.send(400, {"status": "bad request"})
        if self.path == "/api/start":
            s = Session(self.cfg)
            self.sessions[s.id] = s
            card = s.facts["card"]["scenario"]
            return self.send(200, {"session": s.id, "lines": s.lines(s.opening), "title": card["title"],
                                   "brief": " ".join(card["trainee_brief"].split())})
        if self.path == "/api/chat":
            s = self.sessions.get(body.get("session"))
            text = str(body.get("message", "")).strip()
            if s is None:
                return self.send(404, {"status": "error", "kind": "session", "message": "This conversation has ended. Start a new one."})
            if not text or len(text) > MAX_CHARS:
                return self.send(400, {"status": "error", "kind": "input", "message": f"Messages must be 1 to {MAX_CHARS} characters."})
            return self.send(200, s.say(text))
        self.send(404, {"status": "not found"})


def make_server(cfg, port):
    # HTTPServer handles one request at a time, which also keeps the load on the shared GPU modest.
    handler = type("BoundHandler", (Handler,), {"cfg": cfg, "sessions": {}})
    return http.server.HTTPServer(("127.0.0.1", port), handler)


def main():
    cfg = load_config()
    server = make_server(cfg, cfg["port"])
    print(f"HD Anchor free-chat test: http://127.0.0.1:{cfg['port']}  (Ctrl+C to stop)")
    print("Logs:", pathlib.Path(cfg["log_dir"]))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
