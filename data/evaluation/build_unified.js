const fs = require('fs');
const path = require('path');

const evalDir = 'C:/Users/siddh/.gemini/antigravity-ide/scratch/AegisPay-AI/data/evaluation';
const outputFile = path.join(evalDir, 'evaluation.jsonl');

const categoryFiles = [
  'safe.jsonl',
  'injection.jsonl',
  'intent_hijacking.jsonl',
  'velocity_abuse.jsonl',
  'recipient_abuse.jsonl',
  'mixed_attacks.jsonl'
];

let allRecords = [];
for (const fname of categoryFiles) {
  const fpath = path.join(evalDir, fname);
  if (fs.existsSync(fpath)) {
    const lines = fs.readFileSync(fpath, 'utf8').split('\n');
    for (const line of lines) {
      if (line.trim()) {
        allRecords.push(line.trim());
      }
    }
  }
}

fs.writeFileSync(outputFile, allRecords.join('\n') + '\n', 'utf8');
console.log(`Successfully compiled ${allRecords.length} records into ${outputFile}`);
