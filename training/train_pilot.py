# train_pilot.py: first real training run on all s3 examples.
import os, json, random, datetime, importlib.metadata as md
os.environ["HF_HUB_OFFLINE"] = "1"
from unsloth import FastModel
import torch
from datasets import Dataset
from transformers import (AutoTokenizer, Trainer, TrainingArguments,
                          DataCollatorForSeq2Seq, EarlyStoppingCallback)

MODEL = "/home/tongyang/models/gemma-4-E4B-it"
DATA = "/home/tongyang/hd-anchor/data"
OUT = "/home/tongyang/hd-anchor/outputs/pilot1"
MAX_LEN = 6144
MARK = "<|turn>model\n"
SETTINGS = dict(lora_r=16, lora_alpha=16, learning_rate=2e-4, epochs=3, batch_size=1,
                grad_accum=4, eval_and_save_every=50, early_stop_patience=3, load_in_4bit=True)

model, _ = FastModel.from_pretrained(model_name=MODEL, max_seq_length=MAX_LEN,
                                     load_in_4bit=SETTINGS["load_in_4bit"], full_finetuning=False)
tok = AutoTokenizer.from_pretrained(MODEL)
model = FastModel.get_peft_model(
    model, finetune_vision_layers=False, finetune_language_layers=True,
    finetune_attention_modules=True, finetune_mlp_modules=True,
    r=SETTINGS["lora_r"], lora_alpha=SETTINGS["lora_alpha"], lora_dropout=0, bias="none", random_state=3407)

def encode(msgs):
    text = tok.apply_chat_template(msgs, tokenize=False)
    cut = text.rindex(MARK) + len(MARK)
    prompt_ids = tok(text[:cut], add_special_tokens=False)["input_ids"]
    ids = tok(text, add_special_tokens=False)["input_ids"]
    assert ids[:len(prompt_ids)] == prompt_ids, "token boundary mismatch"
    return {"input_ids": ids, "attention_mask": [1] * len(ids),
            "labels": [-100] * len(prompt_ids) + ids[len(prompt_ids):]}

rows = {n: [json.loads(l) for l in open(f"{DATA}/{n}.jsonl")] for n in ["train", "valid"]}
train = Dataset.from_list([encode(r["messages"]) for r in rows["train"]])
valid = Dataset.from_list([encode(r["messages"]) for r in rows["valid"]])
print(f"Train {len(train)} examples, valid {len(valid)} examples")

# Write down everything about this run (for the methods section later)
os.makedirs(OUT, exist_ok=True)
json.dump({"started": datetime.datetime.now().isoformat(timespec="seconds"), "model": MODEL,
           "data": DATA, "prompt_id": rows["train"][0]["meta"]["prompt_id"],
           "teacher": rows["train"][0]["meta"]["teacher"], "settings": SETTINGS,
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
print("Saved the best LoRA notebook to", f"{OUT}/lora_best")

# Ask the best student five mock-exam questions, one from each kind of trainee
FastModel.for_inference(model)
picked, seen = [], set()
for r in rows["valid"]:
    if r["meta"]["trainee"] not in seen:
        seen.add(r["meta"]["trainee"]); picked.append(r)
picked += [r for r in rows["valid"] if r not in picked][:5 - len(picked)]
for r in picked:
    msgs = r["messages"]
    prompt = tok.apply_chat_template(msgs[:-1], tokenize=False, add_generation_prompt=True)
    inputs = tok(prompt, return_tensors="pt", add_special_tokens=False).to("cuda")
    out = model.generate(**inputs, max_new_tokens=150, do_sample=False)
    print(f"\n[{r['meta']['trainee']} trainee, turn {r['meta']['turn']}]")
    print("Clinician:     ", msgs[-2]["content"])
    print("Teacher (31B): ", msgs[-1]["content"])
    print("Student (E4B): ", tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip())
