# Step 11a: merge a LoRA adapter into the 16-bit E4B base, loaded the same way as training (unsloth FastModel)
# Usage (Chongqing, ~/hd-anchor, .venv): nohup python merge_lora.py [LORA_DIR] [OUT_DIR] [BASE_DIR] > merge_log.txt 2>&1 &
import os, sys, shutil, time
os.environ["HF_HUB_OFFLINE"] = "1"
from unsloth import FastModel
from transformers import AutoTokenizer
MODEL = sys.argv[3] if len(sys.argv) > 3 else "/home/tongyang/models/gemma-4-E4B-it"   # base (tokenizer, template files)
LORA = sys.argv[1] if len(sys.argv) > 1 else "/home/tongyang/hd-anchor/outputs/pilot3/lora_best"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/home/tongyang/models/hd-s3-pilot3-merged"
t0 = time.time()
model, _ = FastModel.from_pretrained(model_name=LORA, max_seq_length=6144, load_in_4bit=False)
tok = AutoTokenizer.from_pretrained(MODEL)
model.save_pretrained_merged(OUT, tok, save_method="merged_16bit")
for f in ("chat_template.jinja", "processor_config.json", "generation_config.json", "tokenizer_config.json", "tokenizer.json"):
    if os.path.exists(f"{MODEL}/{f}") and not os.path.exists(f"{OUT}/{f}"):
        shutil.copy(f"{MODEL}/{f}", OUT)
print(f"saved {OUT} in {time.time() - t0:.0f} s")
