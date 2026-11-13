# student_server.py: serve the student model on this computer with the same kind of web address as
# the lab server (an "OpenAI-compatible" API), so the test scripts in scripts/ can talk to it unchanged.
#
#   python student_server.py                       # E4B + outputs/pilot1/lora_best (the student)
#   python student_server.py --base-only           # E4B with no LoRA (the "before training" baseline)
#   python student_server.py --lora /path/to/lora  # another LoRA
#
# Then, in another WSL window:
#   GEMMA_BASE_URL=http://127.0.0.1:8000/v1 python scripts/run_probes.py s3
#
# Listens on 127.0.0.1 only (this computer), no key. One reply at a time.
# Loads the model the same way as training: 4-bit base + LoRA, Gemma chat template.
import os, json, time, argparse, threading
os.environ["HF_HUB_OFFLINE"] = "1"
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

MODEL = "/home/tongyang/models/gemma-4-E4B-it"
LORA = "/home/tongyang/hd-anchor/outputs/pilot1/lora_best"
MAX_LEN = 6144

ap = argparse.ArgumentParser()
ap.add_argument("--lora", default=LORA)
ap.add_argument("--base-only", action="store_true")
ap.add_argument("--port", type=int, default=8000)
a = ap.parse_args()

from unsloth import FastModel
import torch
from transformers import AutoTokenizer

src = MODEL if a.base_only else a.lora
model, _ = FastModel.from_pretrained(model_name=src, max_seq_length=MAX_LEN, load_in_4bit=True)
FastModel.for_inference(model)
tok = AutoTokenizer.from_pretrained(MODEL)
END = tok.convert_tokens_to_ids("<turn|>")
NAME = "gemma-4-E4B-it" + ("" if a.base_only else "+" + "/".join(a.lora.rstrip("/").split("/")[-2:]))
lock = threading.Lock()
print("Serving", NAME, "on http://127.0.0.1:%d/v1" % a.port, flush=True)


def generate(messages, temperature, max_tokens):
    prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tok(prompt, return_tensors="pt", add_special_tokens=False).to("cuda")
    n_in = inputs["input_ids"].shape[1]
    if n_in + max_tokens > MAX_LEN:
        raise ValueError(f"prompt too long: {n_in} tokens")
    kw = dict(do_sample=True, temperature=temperature) if temperature > 0 else dict(do_sample=False)
    t0 = time.time()
    with lock, torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=max_tokens, eos_token_id=[END, tok.eos_token_id], **kw)
    new = out[0][n_in:]
    text = tok.decode(new, skip_special_tokens=True).strip()
    secs = time.time() - t0
    print(f"{n_in} in, {len(new)} out, {secs:.1f} s ({len(new) / secs:.1f} tokens/s)", flush=True)
    return text, n_in, len(new)


class Handler(BaseHTTPRequestHandler):
    def send(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.rstrip("/") == "/v1/models":
            return self.send(200, {"object": "list", "data": [{"id": NAME, "object": "model"}]})
        self.send(404, {"error": "not found"})

    def do_POST(self):
        if self.path.rstrip("/") != "/v1/chat/completions":
            return self.send(404, {"error": "not found"})
        try:
            req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            text, n_in, n_out = generate(req["messages"], float(req.get("temperature", 0.7)),
                                         int(req.get("max_tokens", 300)))
        except Exception as e:
            return self.send(400, {"error": f"{type(e).__name__}: {e}"})
        self.send(200, {"object": "chat.completion", "model": NAME,
                        "choices": [{"index": 0, "message": {"role": "assistant", "content": text},
                                     "finish_reason": "stop"}],
                        "usage": {"prompt_tokens": n_in, "completion_tokens": n_out}})

    def log_message(self, *args):
        pass


ThreadingHTTPServer(("127.0.0.1", a.port), Handler).serve_forever()
