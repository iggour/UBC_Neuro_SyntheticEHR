# train_small.py (step 16): the multi1 recipe on a smaller base model (default Qwen3-1.7B).
# Same data (data_multi1) and settings as multi1, except the base is loaded in 16-bit, not 4-bit:
# the model is small enough, and step 11 showed that merging a LoRA trained on a 4-bit base loses quality.
# Usage (Chongqing, ~/hd-anchor): .venv/bin/python <run>/bundle/training/train_small.py [BASE] [OUT] [short]
import os, sys, json, datetime, importlib.metadata as md
os.environ["HF_HUB_OFFLINE"] = "1"
from unsloth import FastModel
import torch
from datasets import Dataset
from transformers import (AutoTokenizer, Trainer, TrainingArguments,
                          DataCollatorForSeq2Seq, EarlyStoppingCallback)

MODEL = sys.argv[1] if len(sys.argv) > 1 else "/home/tongyang/models/Qwen3-1.7B"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/home/tongyang/hd-anchor/outputs/small1"
SHORT = len(sys.argv) > 3 and sys.argv[3] == "short"   # step 17: train with the short prompt (no guideline layer)
DATA = "/home/tongyang/hd-anchor/multi1/data_multi1"
MAX_LEN = 8192
SETTINGS = dict(lora_r=16, lora_alpha=16, learning_rate=2e-4, epochs=2, batch_size=1,
                grad_accum=4, eval_and_save_every=50, early_stop_patience=3, load_in_4bit=False)
TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

model, _ = FastModel.from_pretrained(model_name=MODEL, max_seq_length=MAX_LEN,
                                     load_in_4bit=SETTINGS["load_in_4bit"], full_finetuning=False)
tok = AutoTokenizer.from_pretrained(MODEL)
peft = dict(r=SETTINGS["lora_r"], lora_alpha=SETTINGS["lora_alpha"], lora_dropout=0, bias="none", random_state=3407)
try:   # same call as multi1 (attention + MLP layers, language only)
    model = FastModel.get_peft_model(model, finetune_vision_layers=False, finetune_language_layers=True,
                                     finetune_attention_modules=True, finetune_mlp_modules=True, **peft)
except TypeError:   # text-only models: the same layers named directly
    model = FastModel.get_peft_model(model, target_modules=TARGETS, **peft)

# where the reply starts: Gemma 4 "<|turn>model\n", ChatML (Qwen) "<|im_start|>assistant\n", Gemma 3 "<start_of_turn>model\n"
probe = tok.apply_chat_template([{"role": "user", "content": "x"}, {"role": "assistant", "content": "y"}], tokenize=False)
MARK = next(m for m in ("<|turn>model\n", "<|im_start|>assistant\n", "<start_of_turn>model\n") if m in probe)
print("Reply marker:", repr(MARK))


def encode(msgs):
    text = tok.apply_chat_template(msgs, tokenize=False)
    cut = text.rindex(MARK) + len(MARK)
    prompt_ids = tok(text[:cut], add_special_tokens=False)["input_ids"]
    ids = tok(text, add_special_tokens=False)["input_ids"]
    assert ids[:len(prompt_ids)] == prompt_ids, "token boundary mismatch"
    return {"input_ids": ids, "attention_mask": [1] * len(ids),
            "labels": [-100] * len(prompt_ids) + ids[len(prompt_ids):]}


rows = {n: [json.loads(l) for l in open(f"{DATA}/{n}.jsonl")] for n in ["train", "valid"]}
if SHORT:   # context distillation: the teacher's replies (made with the full prompt) are kept; the student sees the short prompt
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
    import free_chat_safety as fs
    for n in rows:
        for r in rows[n]:
            sid = r["meta"]["scenario"]
            assert r["messages"][0]["role"] == "system" and r["messages"][0]["content"] == fs.system_prompt(sid, short=False), sid
            r["messages"][0]["content"] = fs.system_prompt(sid, short=True)
    print("Short prompt: guideline layer removed from every system message")
train = Dataset.from_list([encode(r["messages"]) for r in rows["train"]])
valid = Dataset.from_list([encode(r["messages"]) for r in rows["valid"]])
lens = sorted(len(x) for x in train["input_ids"])
print(f"Train {len(train)} examples, valid {len(valid)}; tokens median {lens[len(lens) // 2]}, max {lens[-1]}")
print("One training example ends with:", repr(tok.apply_chat_template(rows["train"][0]["messages"], tokenize=False)[-300:]))

os.makedirs(OUT, exist_ok=True)
json.dump({"started": datetime.datetime.now().isoformat(timespec="seconds"), "model": MODEL,
           "data": DATA, "short_prompt": SHORT, "reply_marker": MARK, "prompt_id": sorted({r["meta"]["prompt_id"] for r in rows["train"]}),
           "teacher": rows["train"][0]["meta"]["teacher"], "settings": SETTINGS, "max_tokens": lens[-1],
           "versions": {p: md.version(p) for p in ["torch", "transformers", "unsloth", "peft", "trl"]}},
          open(f"{OUT}/run_info.json", "w"), indent=2)

S = SETTINGS["eval_and_save_every"]
args = TrainingArguments(
    output_dir=OUT, num_train_epochs=SETTINGS["epochs"],
    per_device_train_batch_size=SETTINGS["batch_size"], gradient_accumulation_steps=SETTINGS["grad_accum"],
    learning_rate=SETTINGS["learning_rate"], warmup_steps=10, lr_scheduler_type="linear",
    logging_steps=5, per_device_eval_batch_size=1, optim="adamw_8bit", bf16=True, report_to="none",
    eval_strategy="steps", eval_steps=S, save_strategy="steps", save_steps=S, save_total_limit=3,
    load_best_model_at_end=True, metric_for_best_model="eval_loss", greater_is_better=False, seed=3407)
trainer = Trainer(model=model, args=args, train_dataset=train, eval_dataset=valid,
                  data_collator=DataCollatorForSeq2Seq(tok, padding=True, label_pad_token_id=-100),
                  callbacks=[EarlyStoppingCallback(early_stopping_patience=SETTINGS["early_stop_patience"])])

print(f"Mock-exam loss before training: {trainer.evaluate()['eval_loss']:.3f}")
trainer.train()
json.dump(trainer.state.log_history, open(f"{OUT}/log_history.json", "w"), indent=1)
print("\nMock-exam results during training:")
for h in trainer.state.log_history:
    if "eval_loss" in h:
        print(f"  step {h['step']:4d}  epoch {h['epoch']:.2f}  mock-exam loss {h['eval_loss']:.3f}")
print(f"Best checkpoint: {trainer.state.best_model_checkpoint}  (loss {trainer.state.best_metric:.3f})")
print(f"Peak graphics-card memory: {torch.cuda.max_memory_allocated() / 1e9:.1f} GB")
model.save_pretrained(f"{OUT}/lora_best")
tok.save_pretrained(f"{OUT}/lora_best")
print("Saved the best LoRA to", f"{OUT}/lora_best")
