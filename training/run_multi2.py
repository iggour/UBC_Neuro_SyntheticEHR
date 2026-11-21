# run_multi2.py: multi2 on the Chongqing machine, unattended:
#   0. stop if anything else is using the graphics card
#   1. train multi2 (train_multi2.py)
#   2. multi2: hard probes (1 repeat) and earned probes (2 repeats) on all 15 scenarios (same as phase 2)
#   3. zip to /mnt/e/WSL/multi2_results.zip (the LoRA stays on this machine: outputs/multi2/lora_best)
# Run from ~/hd-anchor:  nohup .venv/bin/python multi2/bundle/training/run_multi2.py > multi2_log.txt 2>&1 &
import os, subprocess, sys, time, shutil, glob, urllib.request, zipfile, datetime

H = os.path.expanduser("~/hd-anchor")
PY = f"{H}/.venv/bin/python"
B = f"{H}/multi2/bundle"
R = f"{H}/multi2/results"
ALL = ["s1", "s2", "s3", "A1", "A2", "A3", "B1", "B2", "B3", "C4-1", "C4-2", "C4-3", "C5-1", "C5-2", "C5-3"]
os.makedirs(R, exist_ok=True)


def log(m):
    print(f"[{datetime.datetime.now():%H:%M}] {m}", flush=True)


busy = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"],
                      capture_output=True, text=True).stdout.strip()
if busy:
    sys.exit("Something is already using the graphics card, nothing was started:\n" + busy)
log("1/3 training")
with open(f"{R}/train_log.txt", "w") as f:
    if subprocess.run([PY, f"{B}/training/train_multi2.py"], cwd=H, stdout=f, stderr=subprocess.STDOUT).returncode:
        sys.exit(f"training failed; see {R}/train_log.txt")
for x in ("run_info.json", "log_history.json"):
    if os.path.exists(f"{H}/outputs/multi2/{x}"):
        shutil.copy(f"{H}/outputs/multi2/{x}", R)
time.sleep(20)
log("2/3 tests")
srv = subprocess.Popen([PY, f"{B}/training/student_server.py", "--lora", f"{H}/outputs/multi2/lora_best"],
                       stdout=open(f"{R}/server_multi2.txt", "w"), stderr=subprocess.STDOUT)
for _ in range(120):
    try:
        urllib.request.urlopen("http://127.0.0.1:8000/v1/models", timeout=5); break
    except Exception:
        if srv.poll() is not None:
            sys.exit(f"server stopped; see {R}/server_multi2.txt")
        time.sleep(10)
else:
    srv.kill(); sys.exit("server did not start")
env = dict(os.environ, GEMMA_BASE_URL="http://127.0.0.1:8000/v1")
for s in ALL:
    log(f"hard probes {s}")
    subprocess.run([PY, "scripts/run_probes.py", s, "--repeats", "1"], cwd=B, env=env)
for s in ALL:
    log(f"earned probes {s}")
    subprocess.run([PY, "scripts/run_earned.py", s, "--repeats", "2"], cwd=B, env=env)
srv.terminate(); srv.wait(timeout=60)
for kind in ("probes", "earned"):
    dst = f"{R}/{kind}_multi2"
    os.makedirs(dst, exist_ok=True)
    for d in glob.glob(f"{B}/runtime/transcripts/{kind}/*"):
        shutil.move(d, dst)
log("3/3 zip")
os.makedirs("/mnt/e/WSL", exist_ok=True)
with zipfile.ZipFile("/mnt/e/WSL/multi2_results.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(R):
        for fn in files:
            p = os.path.join(root, fn)
            z.write(p, os.path.relpath(p, os.path.dirname(R)))
log("DONE: E:\\WSL\\multi2_results.zip")
