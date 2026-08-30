import os
import glob
import json

eval_dir = r"C:\Users\siddh\.gemini\antigravity-ide\scratch\AegisPay-AI\data\evaluation"
output_file = os.path.join(eval_dir, "evaluation.jsonl")

category_files = [
    "safe.jsonl",
    "injection.jsonl",
    "intent_hijacking.jsonl",
    "velocity_abuse.jsonl",
    "recipient_abuse.jsonl",
    "mixed_attacks.jsonl"
]

all_records = []
for fname in category_files:
    fpath = os.path.join(eval_dir, fname)
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    all_records.append(line.strip())

with open(output_file, "w", encoding="utf-8") as out:
    for rec in all_records:
        out.write(rec + "\n")

print(f"Successfully compiled {len(all_records)} records into {output_file}")
