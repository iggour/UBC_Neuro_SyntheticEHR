# run_phase2.py: phase 2 measurements on the Chongqing machine, unattended (no training):
#   0. stop if anything else is using the graphics card
#   for each small model (untrained E4B, pilot3 = s3-only student, multi1 = 6-scenario student):
#     hard probes (1 repeat): base and multi1 on the 6 unseen-family scenarios (the 9 others were done in
#     step 13); pilot3 on all 15. Earned probes (2 repeats) on all 15 for every model.
#   zip to /mnt/e/WSL/phase2_results.zip
# Run from ~/hd-anchor:  nohup .venv/bin/python phase2/bundle/training/run_phase2.py > phase2_log.txt 2>&1 &
import os, subprocess, sys, time, shutil, glob, urllib.request, zipfile, datetime

H = os.path.expanduser("~/hd-anchor")
PY = f"{H}/.venv/bin/python"
B = f"{H}/phase2/bundle"
R = f"{H}/phase2/results"
ALL = ["s1", "s2", "s3", "A1", "A2", "A3", "B1", "B2", "B3", "C4-1", "C4-2", "C4-3", "C5-1", "C5-2", "C5-3"]
NEW = ["B1", "B2", "B3", "C4-1", "C4-2", "C4-3"]
MODELS = [("base", ["--base-only"], NEW),
          ("pilot3", ["--lora", f"{H}/outputs/pilot3/lora_best"], ALL),
          ("multi1", ["--lora", f"{H}/outputs/multi1/lora_best"], NEW)]
os.makedirs(R, exist_ok=True)


def log(m):
    print(f"[{datetime.datetime.now():%H:%M}] {m}", flush=True)


busy = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"],
                      capture_output=True, text=True).stdout.strip()
if busy:
    sys.exit("Something is already using the graphics card, nothing was started:\n" + busy)
env = dict(os.environ, GEMMA_BASE_URL="http://127.0.0.1:8000/v1")
for label, args, hard in MODELS:
    log(f"{label}: starting server")
    srv = subprocess.Popen([PY, f"{B}/training/student_server.py", *args],
                           stdout=open(f"{R}/server_{label}.txt", "w"), stderr=subprocess.STDOUT)
    for _ in range(120):
        try:
            urllib.request.urlopen("http://127.0.0.1:8000/v1/models", timeout=5); break
        except Exception:
            if srv.poll() is not None:
                sys.exit(f"server for {label} stopped; see {R}/server_{label}.txt")
            time.sleep(10)
    else:
        srv.kill(); sys.exit(f"server for {label} did not start")
    for s in hard:
        log(f"{label}: hard probes {s}")
        subprocess.run([PY, "scripts/run_probes.py", s, "--repeats", "1"], cwd=B, env=env)
    for s in ALL:
        log(f"{label}: earned probes {s}")
        subprocess.run([PY, "scripts/run_earned.py", s, "--repeats", "2"], cwd=B, env=env)
    srv.terminate(); srv.wait(timeout=60)
    for kind in ("probes", "earned"):
        dst = f"{R}/{kind}_{label}"
        os.makedirs(dst, exist_ok=True)
        for d in glob.glob(f"{B}/runtime/transcripts/{kind}/*"):
            shutil.move(d, dst)
    time.sleep(20)
log("zip")
os.makedirs("/mnt/e/WSL", exist_ok=True)
with zipfile.ZipFile("/mnt/e/WSL/phase2_results.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(R):
        for fn in files:
            p = os.path.join(root, fn)
            z.write(p, os.path.relpath(p, os.path.dirname(R)))
log("DONE: E:\\WSL\\phase2_results.zip")
