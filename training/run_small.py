# run_small.py (steps 16-17): smaller student on the Chongqing machine, unattended, one command:
#   small1 (step 16): Qwen3-1.7B, multi1 data, full prompt.   small2 (step 17): same, short prompt (no guideline layer).
#   0. stop if anything else is using the graphics card
#   1. download the base model (Qwen3-1.7B) if missing: ModelScope first, then huggingface.co / hf-mirror.com
#   2. train small1 = multi1 data and settings on the small base (train_small.py; 16-bit base + LoRA)
#   3. phase-2 tests with the student on the GPU: hard probes (1 repeat) + earned probes (2 repeats), 15 scenarios
#   4. merge the LoRA, convert to GGUF, quantise to Q8_0 and Q4_K_M (llama.cpp, CPU build)
#   5. measure each GGUF on the CPU as a learner would run it: file size, peak RAM, first and second reply speed
#   6. zip results to /mnt/e/WSL/small1_results.zip; copy both GGUF files to /mnt/e/WSL/
# Run from ~/hd-anchor:  nohup .venv/bin/python small1/bundle/training/run_small.py > small1_log.txt 2>&1 &
#                    or:  nohup .venv/bin/python small2/bundle/training/run_small.py small2 short > small2_log.txt 2>&1 &
import os, subprocess, sys, time, shutil, glob, json, urllib.request, zipfile, datetime

NAME = sys.argv[1] if len(sys.argv) > 1 else "small1"
SHORT = len(sys.argv) > 2 and sys.argv[2] == "short"
H = os.path.expanduser("~/hd-anchor")
PY = f"{H}/.venv/bin/python"
B = f"{H}/{NAME}/bundle"
R = f"{H}/{NAME}/results"
REPO = "Qwen/Qwen3-1.7B"
BASE = os.path.expanduser("~/models/Qwen3-1.7B")
OUT = f"{H}/outputs/{NAME}"
MERGED = os.path.expanduser(f"~/models/hd-{NAME}-merged")
G = os.path.expanduser(f"~/models/hd-{NAME}")
sys.path.insert(0, f"{B}/scripts")
import free_chat_safety as fs
ALL = ["s1", "s2", "s3", "A1", "A2", "A3", "B1", "B2", "B3", "C4-1", "C4-2", "C4-3", "C5-1", "C5-2", "C5-3"]
os.makedirs(R, exist_ok=True)


def log(m):
    print(f"[{datetime.datetime.now():%H:%M}] {m}", flush=True)


def wait_for(url, proc, what, tries=120):
    for _ in range(tries):
        try:
            urllib.request.urlopen(url, timeout=5); return
        except Exception:
            if proc.poll() is not None:
                sys.exit(f"{what} stopped; see {R}")
            time.sleep(10)
    proc.kill(); sys.exit(f"{what} did not start")


def find(name):
    hits = subprocess.run(["find", os.path.expanduser("~"), "-name", name, "-not", "-path", "*/.venv/*"],
                          capture_output=True, text=True).stdout.split()
    hits = [h for h in hits if os.path.isfile(h)]
    if not hits:
        sys.exit(f"{name} not found under ~")
    return hits[0]


busy = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"],
                      capture_output=True, text=True).stdout.strip()
if busy:
    sys.exit("Something is already using the graphics card, nothing was started:\n" + busy)

# 1. base model: ModelScope first (E4B came from there), then Hugging Face and its mirror
def have_base():
    return os.path.exists(f"{BASE}/config.json") and glob.glob(f"{BASE}/*.safetensors")


if not have_base():
    env = {k: v for k, v in os.environ.items() if k != "HF_HUB_OFFLINE"}
    ms_py = f"from modelscope import snapshot_download as d; d('{REPO}', local_dir='{BASE}')"
    tries = [("ModelScope (python)", [PY, "-c", ms_py], env)]
    ms_cli = shutil.which("modelscope") or (f"{H}/.venv/bin/modelscope" if os.path.exists(f"{H}/.venv/bin/modelscope") else None)
    if ms_cli:
        tries.append(("ModelScope (command)", [ms_cli, "download", "--model", REPO, "--local_dir", BASE], env))
    tries.append(("pip install modelscope, then ModelScope", ["bash", "-c", f"{PY} -m pip install -q modelscope && {PY} -c \"{ms_py}\""], env))
    hf_py = f"from huggingface_hub import snapshot_download as d; d('{REPO}', local_dir='{BASE}')"
    for ep in ("https://huggingface.co", "https://hf-mirror.com"):
        tries.append((ep, [PY, "-c", hf_py], dict(env, HF_ENDPOINT=ep)))
    for name, cmd, e in tries:
        log(f"1/6 downloading {REPO}: {name}")
        subprocess.run(cmd, env=e)
        if have_base():
            break
    else:
        sys.exit(f"Could not download {REPO}. Download it on the Mac and copy the folder to {BASE}")
log("base model ready: " + BASE)

# 2. training
log("2/6 training")
with open(f"{R}/train_log.txt", "w") as f:
    if subprocess.run([PY, f"{B}/training/train_small.py", BASE, OUT] + (["short"] if SHORT else []), cwd=H, stdout=f, stderr=subprocess.STDOUT).returncode:
        sys.exit(f"training failed; see {R}/train_log.txt")
for x in ("run_info.json", "log_history.json"):
    if os.path.exists(f"{OUT}/{x}"):
        shutil.copy(f"{OUT}/{x}", R)
time.sleep(20)

# 3. tests (GPU, same scripts and repeats as multi1 / multi2)
log("3/6 tests")
srv = subprocess.Popen([PY, f"{B}/training/student_server.py", "--base", BASE, "--lora", f"{OUT}/lora_best",
                        "--bits16", "--no-think"], stdout=open(f"{R}/server_{NAME}.txt", "w"), stderr=subprocess.STDOUT)
wait_for("http://127.0.0.1:8000/v1/models", srv, "student server")
env = dict(os.environ, GEMMA_BASE_URL="http://127.0.0.1:8000/v1", HD_SHORT_PROMPT="1" if SHORT else "0")
for s in ALL:
    log(f"hard probes {s}")
    subprocess.run([PY, "scripts/run_probes.py", s, "--repeats", "1"], cwd=B, env=env)
for s in ALL:
    log(f"earned probes {s}")
    subprocess.run([PY, "scripts/run_earned.py", s, "--repeats", "2"], cwd=B, env=env)
srv.terminate(); srv.wait(timeout=60)
for kind in ("probes", "earned"):
    dst = f"{R}/{kind}_{NAME}"
    os.makedirs(dst, exist_ok=True)
    for d in glob.glob(f"{B}/runtime/transcripts/{kind}/*"):
        shutil.move(d, dst)
time.sleep(20)

# 4. merge, GGUF, quantise
log("4/6 merge + GGUF")
server = find("llama-server")                       # the CPU build used in step 11; take its own tools
bindir = os.path.dirname(server)
quant = os.path.join(bindir, "llama-quantize") if os.path.isfile(os.path.join(bindir, "llama-quantize")) else find("llama-quantize")
conv = next((c for c in (os.path.join(bindir, "..", "..", "convert_hf_to_gguf.py"),) if os.path.isfile(c)), None) or find("convert_hf_to_gguf.py")
with open(f"{R}/quant_log.txt", "w") as f:
    steps = [[PY, f"{B}/training/merge_lora.py", f"{OUT}/lora_best", MERGED, BASE],
             [PY, conv, MERGED, "--outtype", "bf16", "--outfile", f"{G}-bf16.gguf"],
             [quant, f"{G}-bf16.gguf", f"{G}-Q8_0.gguf", "Q8_0"],
             [quant, f"{G}-bf16.gguf", f"{G}-Q4_K_M.gguf", "Q4_K_M"]]
    for c in steps:
        f.write("\n$ " + " ".join(c) + "\n"); f.flush()
        if subprocess.run(c, stdout=f, stderr=subprocess.STDOUT).returncode:
            sys.exit(f"failed: {' '.join(c)}; see {R}/quant_log.txt")

# 5. CPU measurement, as a learner would run it (thinking off, 20 threads, 8k context), with the prompt the website
#    would send for this model (s3; full = role card + guideline layer, short = without the guideline layer).
#    small2 also re-measures small1's files with the full prompt (step 16's measurement left the guideline layer out).
log("5/6 CPU measurement")
turns = ["Hello, thanks for coming in today. How have things been since we last met?",
         "That sounds like a lot to carry. What has been the hardest part for you?"]
other = subprocess.run(["pgrep", "-af", "llama-server"], capture_output=True, text=True).stdout.strip()
meas = {"other_llama_server_running_at_start": other or None, "llama_server": server}
runs = [(f"{NAME}-{q}", f"{G}-{q}.gguf", SHORT) for q in ("Q8_0", "Q4_K_M")]
if NAME != "small1":
    runs += [(f"small1-{q}", os.path.expanduser(f"~/models/hd-small1-{q}.gguf"), False) for q in ("Q8_0", "Q4_K_M")]
for label, path, short in runs:
    if not os.path.exists(path):
        log(f"skip {label}: no file"); continue
    system = fs.system_prompt("s3_suicide_risk_assessment", short=short)
    p = subprocess.Popen([server, "-m", path, "--host", "127.0.0.1", "--port", "8081", "-c", "8192", "-t", "20",
                          "--chat-template-kwargs", '{"enable_thinking": false}', "--reasoning-format", "none"],
                         stdout=open(f"{R}/llama_server_{label}.txt", "w"), stderr=subprocess.STDOUT)
    wait_for("http://127.0.0.1:8081/health", p, f"llama-server {label}")
    msgs, rows = [{"role": "system", "content": system}], []
    for t in turns:
        msgs.append({"role": "user", "content": t})
        body = json.dumps({"messages": msgs, "temperature": 0, "max_tokens": 150}).encode()
        t0 = time.time()
        r = json.load(urllib.request.urlopen(urllib.request.Request(
            "http://127.0.0.1:8081/v1/chat/completions", body, {"Content-Type": "application/json"}), timeout=600))
        reply = r["choices"][0]["message"]["content"]
        msgs.append({"role": "assistant", "content": reply})
        tm = r.get("timings", {})
        rows.append({"clinician": t, "reply": reply, "seconds": round(time.time() - t0, 1),
                     "prompt_tokens": r.get("usage", {}).get("prompt_tokens"), "prompt_tokens_cached": tm.get("cache_n"),
                     "prompt_tokens_per_s": tm.get("prompt_per_second"), "reply_tokens": tm.get("predicted_n"),
                     "reply_tokens_per_s": tm.get("predicted_per_second")})
    status = open(f"/proc/{p.pid}/status").read()
    peak = next((int(l.split()[1]) for l in status.splitlines() if l.startswith("VmHWM")), 0)
    meas[label] = {"prompt": "short" if short else "full", "file_GB": round(os.path.getsize(path) / 1e9, 2),
                   "peak_RAM_GB": round(peak / 1e6, 2), "turns": rows}
    p.terminate(); p.wait(timeout=60)
    log(f"{label} ({meas[label]['prompt']} prompt, {rows[0]['prompt_tokens']} tokens): {meas[label]['file_GB']} GB file, "
        f"{meas[label]['peak_RAM_GB']} GB RAM, first reply {rows[0]['seconds']} s, second {rows[1]['seconds']} s")
json.dump(meas, open(f"{R}/cpu_measure.json", "w"), indent=2, ensure_ascii=False)

# 6. hand-over
log("6/6 zip and copy")
os.makedirs("/mnt/e/WSL", exist_ok=True)
with zipfile.ZipFile(f"/mnt/e/WSL/{NAME}_results.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(R):
        for fn in files:
            p_ = os.path.join(root, fn)
            z.write(p_, os.path.relpath(p_, os.path.dirname(R)))
for q in ("Q8_0", "Q4_K_M"):
    shutil.copy(f"{G}-{q}.gguf", "/mnt/e/WSL/")
log(f"DONE: E:\\WSL\\{NAME}_results.zip, hd-{NAME}-Q8_0.gguf, hd-{NAME}-Q4_K_M.gguf")
