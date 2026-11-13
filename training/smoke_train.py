# smoke_train.py: a tiny test training run (a few minutes).
# Goal: prove the whole pipeline works, not to get a good model.
import os, json, random
os.environ["HF_HUB_OFFLINE"] = "1"      # use only local files; this computer cannot reach Hugging Face
from unsloth import FastModel           # import unsloth first, so it can speed up the rest
import torch
from datasets import Dataset
from transformers import AutoTokenizer, Trainer, TrainingArguments, DataCollatorForSeq2Seq

MODEL = "/home/tongyang/models/gemma-4-E4B-it"
DATA = "/home/tongyang/hd-anchor/data"
OUT = "/home/tongyang/hd-anchor/outputs/smoke"
MAX_LEN = 6144                          # our longest example is 5,620 tokens
N_TRAIN, N_VALID = 50, 20
MARK = "<|turn>model\n"

# 1. Load the student in 4-bit (saves graphics-card memory), and the same tokenizer we tested
model, _ = FastModel.from_pretrained(model_name=MODEL, max_seq_length=MAX_LEN,
                                     load_in_4bit=True, full_finetuning=False)
tok = AutoTokenizer.from_pretrained(MODEL)

# 2. Add the LoRA "notebook": only these small extra weights are trained
model = FastModel.get_peft_model(
    model, finetune_vision_layers=False, finetune_language_layers=True,
    finetune_attention_modules=True, finetune_mlp_modules=True,
    r=16, lora_alpha=16, lora_dropout=0, bias="none", random_state=3407)

# 3. Turn each example into numbers, and mark the part to learn: only the last patient reply
def encode(msgs):
    text = tok.apply_chat_template(msgs, tokenize=False)
    cut = text.rindex(MARK) + len(MARK)
    prompt_ids = tok(text[:cut], add_special_tokens=False)["input_ids"]
    ids = tok(text, add_special_tokens=False)["input_ids"]
    assert ids[:len(prompt_ids)] == prompt_ids, "token boundary mismatch"
    labels = [-100] * len(prompt_ids) + ids[len(prompt_ids):]   # -100 means "don't learn this part"
    return {"input_ids": ids, "attention_mask": [1] * len(ids), "labels": labels}

def load(name, n):
    rows = [json.loads(l)["messages"] for l in open(f"{DATA}/{name}.jsonl")]
    random.Random(0).shuffle(rows)
    return Dataset.from_list([encode(m) for m in rows[:n]])

train, valid = load("train", N_TRAIN), load("valid", N_VALID)
ex = train[0]
print(f"\nOne example: {len(ex['input_ids'])} tokens; the model learns {sum(x != -100 for x in ex['labels'])} of them")
print("The part it learns:", repr(tok.decode([x for x in ex["labels"] if x != -100])))

# 4. Mock exam, short training, mock exam again
args = TrainingArguments(
    output_dir=OUT, per_device_train_batch_size=1, gradient_accumulation_steps=4,
    max_steps=12, learning_rate=2e-4, warmup_steps=2, lr_scheduler_type="linear",
    logging_steps=1, per_device_eval_batch_size=1, optim="adamw_8bit",
    bf16=True, report_to="none", save_strategy="no", seed=3407)
trainer = Trainer(model=model, args=args, train_dataset=train, eval_dataset=valid,
                  data_collator=DataCollatorForSeq2Seq(tok, padding=True, label_pad_token_id=-100))
before = trainer.evaluate()["eval_loss"]
trainer.train()
after = trainer.evaluate()["eval_loss"]
print(f"\nMock-exam loss before: {before:.3f}   after: {after:.3f}")
print(f"Peak graphics-card memory: {torch.cuda.max_memory_allocated() / 1e9:.1f} GB")

# 5. Ask the student one mock-exam question
FastModel.for_inference(model)
msgs = json.loads(open(f"{DATA}/valid.jsonl").readline())["messages"]
prompt = tok.apply_chat_template(msgs[:-1], tokenize=False, add_generation_prompt=True)
inputs = tok(prompt, return_tensors="pt", add_special_tokens=False).to("cuda")
out = model.generate(**inputs, max_new_tokens=120, do_sample=False)
print("\nClinician:     ", msgs[-2]["content"])
print("Teacher (31B): ", msgs[-1]["content"])
print("Student (E4B): ", tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip())

# 6. Save the LoRA notebook
model.save_pretrained(f"{OUT}/lora")
tok.save_pretrained(f"{OUT}/lora")
print("\nSaved the LoRA notebook to", f"{OUT}/lora")
