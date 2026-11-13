import json
from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained("/home/tongyang/models/gemma-4-E4B-it")
msgs = json.loads(open("/home/tongyang/hd-anchor/data/train.jsonl").readline())["messages"]

# Shorten the long patient instructions so the screen is readable
short = [dict(m) for m in msgs]
short[0]["content"] = short[0]["content"][:150] + " ...[rest of the patient instructions]..."

try:
    print(tok.apply_chat_template(short, tokenize=False))
    full = tok.apply_chat_template(msgs, tokenize=False)
    print("\nTokens in this whole example:", len(tok(full)["input_ids"]))
except Exception as e:
    print("TEMPLATE ERROR:", type(e).__name__, e)
