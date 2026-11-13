import json
from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained("/home/tongyang/models/gemma-4-E4B-it")
for name in ["train", "valid"]:
    lengths = []
    for line in open(f"/home/tongyang/hd-anchor/data/{name}.jsonl"):
        msgs = json.loads(line)["messages"]
        text = tok.apply_chat_template(msgs, tokenize=False)
        lengths.append(len(tok(text)["input_ids"]))
    lengths.sort()
    print(f"{name}: {len(lengths)} examples | shortest {lengths[0]} | middle {lengths[len(lengths)//2]} | longest {lengths[-1]} tokens")
