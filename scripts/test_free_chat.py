#!/usr/bin/env python3
"""
test_free_chat.py
Tests the free-chat safety layer and proxy against a fake model server on this computer. No request
reaches the real Gemma server, and the config file is not read.

Usage:
    python3 scripts/test_free_chat.py
"""
import http.server, json, pathlib, sys, tempfile, threading, time, urllib.error, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import free_chat_safety as fs
import free_chat_server as srv

FACTS = fs.load_facts(srv.SCENARIO)

# ---------------------------------------------------------------- the person typing
DISTRESS = ["I want to die", "honestly i just want to die", "I don't want to live anymore", "I want to kill myself",
            "I keep thinking about suicide", "I can't go on", "I feel suicidal", "I've been hurting myself",
            "Sometimes I wish I was dead", "there is no reason to live", "I can’t take this anymore",
            "everyone would be better off without me", "I might end my life", "我想死", "我不想活了", "我想自杀"]
NOT_DISTRESS = ["Do you ever feel you want to die?", "Have you had thoughts of ending your life?",
                "I wonder if you want to die sometimes", "How has your mood been, Ruth?",
                "Has Anna noticed you hurting yourself?", "I want to hear about your driving.",
                "I can't tell you what to do about the car.", "I'd like to ask about suicide, as I ask all my patients.",
                "你有没有想过自杀?", "我想问你是不是想死"]

# ---------------------------------------------------------------- the patient reply
GOOD = ["I'm seventy, not ninety. I've been driving for fifty years.",
        "Ruth: I'm 70 and perfectly fine.\nAnna: Mum, please. I'm 43 and I worry.",
        "I take one tablet for blood pressure. That's all.",
        "My husband George can't drive just now. My daughter Anna fusses.",
        "I drive into town every Sunday for church. Margaret offered me a ride in April.",
        "Lily is 13 and Sam is ten.", "I read that in a magazine once. Where was I?",
        "I'd rather not crash into anybody, thank you.", "HTT CAG 17 / 39, the doctor told me. I don't know what it means.",
        "Anna: I found the dent and the paint. I'm so frightened. Ruth: I am here, you know."]
BAD = [("self-harm", "Sometimes I think about taking an overdose."), ("self-harm", "I want to die."),
       ("self-harm", "I took my whole bottle after the suicide talk, 30 tablets."), ("self-harm", "It would be a noose."),
       ("dose", "My tetrabenazine is 12.5 mg twice a day."), ("dose", "I take 25 mg in the morning."),
       ("dose", "I take two tablets every night."), ("age", "I'm 72 and I drive just fine."),
       ("age", "I'm seventy-two, you know."), ("age", "George is 75 this year."), ("age", "My husband is 80."),
       ("age", "A 68-year-old woman like me."), ("age", "Anna: I'm 45."), ("name", "My husband Frank can't drive."),
       ("name", "My son George lives in Calgary."), ("name", "My name is Margaret."), ("name", "I'm Ruth Smith."),
       ("name", "Doctor: Ruth should stop driving."), ("cag", "They said my CAG was 17/41."), ("cag", "I have 42 repeats."),
       ("medication", "My tetrabenazine keeps the movements down."), ("medication", "I take lisinopril."),
       ("medication", "I'm on sertraline."), ("medication", "I take aspirin too."), ("medication", "I take no regular medicines."),
       ("character", "As an AI, I cannot answer that."), ("character", "That is not in my role card."),
       ("medical-fact", "It is autosomal dominant, you see."), ("medical-fact", "My children have a 50% chance."),
       ("medical-fact", "Anything from 36 to 39 repeats is reduced penetrance."), ("language", "我很好,谢谢。"), ("empty", "   ")]


def run_list(title, cases, test):
    fails = [c for c in cases if not test(c)]
    print(f"{title:44}{len(cases) - len(fails)}/{len(cases)}")
    for c in fails:
        print("   MISSED:", c, fs.check_reply(c[1], FACTS) if isinstance(c, tuple) else "")
    return not fails


# ---------------------------------------------------------------- the proxy, with a fake model server
class Fake(http.server.BaseHTTPRequestHandler):
    mode, reply, calls = "ok", "I've been driving for fifty years.", []

    def log_message(self, *args):
        pass

    def answer(self, code, body):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self.answer(200, {"data": [{"id": "fake-model"}]})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Fake.calls.append(body)
        if Fake.mode == "slow":
            time.sleep(2)
        if Fake.mode == "500":
            return self.answer(500, {"error": "boom"})
        if Fake.mode == "garbage":
            return self.answer(200, b"<html>not json</html>")
        try:
            self.answer(200, {"choices": [{"message": {"content": Fake.reply}, "finish_reason": "length" if Fake.mode == "cut" else "stop"}]})
        except OSError:
            pass


def serve(server):
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server.server_port


def call(port, path, body=None, headers=None):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def proxy_tests(log_dir):
    fake = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Fake)
    fake_port = serve(fake)
    cfg = {**srv.DEFAULTS, "base_url": f"http://127.0.0.1:{fake_port}/v1", "timeout_s": 1, "log_dir": str(log_dir), "model": "fake-model"}
    port = serve(srv.make_server(cfg, 0))
    start = lambda: json.loads(call(port, "/api/start", {})[1])
    chat = lambda s, m: json.loads(call(port, "/api/chat", {"session": s, "message": m})[1])
    results = []

    def check(label, ok):
        results.append(ok)
        print(f"  {label:66}{'OK' if ok else 'FAILED'}")

    s = start()
    check("opening line is the role card's", s["lines"][0]["text"] == FACTS["card"]["persona"]["opening_line"])
    page = call(port, "/")[1].decode()
    check("banner on the page", "Test mode – AI responses may be wrong. Fictional patient. Not medical advice." in page)
    check("page has no server address", "://" not in page and "base_url" not in page)
    d = chat(s["session"], "How is the driving going?")
    sent = Fake.calls[-1]
    check("normal reply shown", d["status"] == "ok" and d["lines"][0]["text"].startswith("I've been"))
    check("settings: low temperature, 300 tokens", sent["temperature"] == 0.3 and sent["max_tokens"] == 300)
    check("prompt has role card and guidelines", "Ruth Fraser" in sent["messages"][0]["content"] and "hd-tx-001" in sent["messages"][0]["content"])

    Fake.reply = "I take 25 mg of tetrabenazine."
    d = chat(s["session"], "What do you take?")
    check("bad reply withheld, fallback shown", d["withheld"] == ["dose", "medication"] and d["lines"][0]["text"].startswith("Sorry"))
    Fake.reply = "Fine."
    chat(s["session"], "Anything else?")
    check("withheld reply is not in the history", not any("25 mg" in m["content"] for m in Fake.calls[-1]["messages"]))

    Fake.mode, Fake.reply = "cut", "I've been fine. Really. And then I was going to the"
    d = chat(s["session"], "Tell me more.")
    check("reply cut at max_tokens keeps whole sentences", d["lines"][0]["text"] == "I've been fine. Really.")

    Fake.reply = "Fine."
    for mode, kind in (("slow", "timeout"), ("500", "http_500"), ("garbage", "bad_response")):
        Fake.mode = mode
        d = chat(s["session"], "Are you there?")
        check(f"{mode}: error shown, kind {kind}", d["status"] == "error" and d["kind"] == kind and "127.0.0.1" not in json.dumps(d))
    Fake.mode = "ok"
    n = len(Fake.calls[-1]["messages"])     # the last failed call already carried this message once
    chat(s["session"], "Are you there?")
    check("failed message is not left in the history", len(Fake.calls[-1]["messages"]) == n)

    before = len(Fake.calls)
    d = chat(s["session"], "Sorry, this is not the role-play. I want to die.")
    check("distress stops the role-play", d["status"] == "crisis")
    check("distress message never reached the model", len(Fake.calls) == before)
    check("conversation stays stopped", chat(s["session"], "Hello?")["status"] == "crisis" and len(Fake.calls) == before)
    log = "\n".join(p.read_text(encoding="utf-8") for p in pathlib.Path(log_dir).glob("*.jsonl"))
    check("log records the stop and the withheld reply", "crisis_stop" in log and '"withheld"' in log and "25 mg" in log)
    check("log has no model server address", f"127.0.0.1:{fake_port}" not in log)

    check("other sites refused", call(port, "/api/start", {}, {"Origin": "https://evil.example"})[0] == 403)
    check("non-JSON post refused", call(port, "/api/start", {}, {"Content-Type": "text/plain"})[0] == 403)
    check("over-long message refused", call(port, "/api/chat", {"session": s["session"], "message": "x" * 1501})[0] == 400)
    fake.shutdown()
    return all(results)


def main():
    ok = run_list("Distress: must stop", DISTRESS, fs.looks_like_distress)
    ok = run_list("Distress: must not stop (role-play)", NOT_DISTRESS, lambda t: not fs.looks_like_distress(t)) and ok
    ok = run_list("Replies: must pass", [("pass", t) for t in GOOD], lambda c: fs.check_reply(c[1], FACTS) == []) and ok
    ok = run_list("Replies: must be withheld, right category", BAD, lambda c: c[0] in {r[0] for r in fs.check_reply(c[1], FACTS)}) and ok
    print("Proxy, with a fake model server")
    with tempfile.TemporaryDirectory() as tmp:
        ok = proxy_tests(tmp) and ok
    print("ALL PASSED" if ok else "SOME TESTS FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
