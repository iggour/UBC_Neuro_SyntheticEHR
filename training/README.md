# training/: scripts that run on the training computer (not on the Mac)

These run inside WSL2 Ubuntu 24.04 on the Chongqing workstation (RTX 5090 D v2, 24 GB), in the
virtual environment ~/hd-anchor/.venv. Paths inside the scripts are for that computer.
The full step-by-step record (what was done, why, and the results) is docs/distillation_log.md.

| Script | Step | What it does |
|---|---|---|
| show_template.py | 5c-2 | Prints one training example as the student sees it (Gemma chat template) |
| check_lengths.py | 5c-3 | Token length of every training and validation example |
| smoke_train.py | 5c-4 | Tiny test run: 50 examples, 12 steps, one answer, saves a LoRA |
| train_pilot.py | 5d | Pilot training on all s3 examples, mock exam every 50 steps, early stop, keeps the best LoRA |

Training data comes from scripts/build_training_data.py (runtime/transcripts/training_data/<sN>_<date>/).
