# run_multi1.py: the whole multi1 run on the Chongqing machine, unattended, in this order:
#   0. stop if anything else is using the graphics card
#   1. untrained E4B (--base-only): hard probes for all 9 scenarios, 1 repeat   (baseline)
#   2. train the student (train_multi1.py)
#   3. student (outputs/multi1/lora_best): the same probes                      (result)
#   4. zip the results to /mnt/e/WSL/multi1_results.zip (the LoRA stays on this machine)
# Run from ~/hd-anchor:  nohup .venv/bin/python multi1/bundle/training/run_multi1.py > multi1_log.txt 2>&1 &
import os, subprocess, sys, time, shutil, glob, urllib.request, zipfile, datetime

H = os.path.expanduser("~/hd-anchor")
PY = f"{H}/.venv/bin/python"
B = f"{H}/multi1/bundle"
R = f"{H}/multi1/results"
SCEN = ["s1", "s2", "s3", "A1", "A2", "A3", "C5-1", "C5-2", "C5-3"]   # held out: s2, A3, C5-2
LORA = f"{H}/outputs/multi1/lora_best"
os.makedirs(R, exist_ok=True)


def log(m):
    print(f"[{datetime.datetime.now():%H:%M}] {m}", flush=True)


def gpu_busy():
    out = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"],
                         capture_output=True, text=True).stdout.strip()
    return out


def probes(label, server_args):
    srv = subprocess.Popen([PY, f"{B}/training/student_server.py", *server_args],
                           stdout=open(f"{R}/server_{label}.txt", "w"), stderr=subprocess.STDOUT)
    for _ in range(120):                                  # wait up to 20 minutes for the model to load
        try:
            urllib.request.urlopen("http://127.0.0.1:8000/v1/models", timeout=5); break
        except Exception:
            if srv.poll() is not None:
                sys.exit(f"server for {label} stopped; see {R}/server_{label}.txt")
            time.sleep(10)
    else:
        srv.kill(); sys.exit(f"server for {label} did not start")
    env = dict(os.environ, GEMMA_BASE_URL="http://127.0.0.1:8000/v1")
    for s in SCEN:
        log(f"{label}: probes {s}")
        subprocess.run([PY, "scripts/run_probes.py", s, "--repeats", "1"], cwd=B, env=env)
    srv.terminate(); srv.wait(timeout=60)
    dst = f"{R}/probes_{label}"
    os.makedirs(dst, exist_ok=True)
    for d in glob.glob(f"{B}/runtime/transcripts/probes/*"):
        shutil.move(d, dst)
    time.sleep(20)                                        # let the graphics card free its memory


busy = gpu_busy()
if busy:
    sys.exit("Something is already using the graphics card, nothing was started:\n" + busy)
log("1/4 baseline (untrained E4B)")
probes("base", ["--base-only"])
log("2/4 training")
with open(f"{R}/train_log.txt", "w") as f:
    if subprocess.run([PY, f"{B}/training/train_multi1.py"], cwd=H, stdout=f, stderr=subprocess.STDOUT).returncode:
        sys.exit(f"training failed; see {R}/train_log.txt")
for x in ("run_info.json", "log_history.json"):
    if os.path.exists(f"{H}/outputs/multi1/{x}"):
        shutil.copy(f"{H}/outputs/multi1/{x}", R)
log("3/4 student")
probes("student", ["--lora", LORA])
log("4/4 zip")
os.makedirs("/mnt/e/WSL", exist_ok=True)
with zipfile.ZipFile("/mnt/e/WSL/multi1_results.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(R):
        for fn in files:
            p = os.path.join(root, fn)
            z.write(p, os.path.relpath(p, os.path.dirname(R)))
log("DONE: E:\\WSL\\multi1_results.zip")
