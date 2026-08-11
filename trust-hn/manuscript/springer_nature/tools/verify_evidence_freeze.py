from __future__ import annotations
import csv, hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
MANIFEST=HERE.parent/'project_management'/'evidence_asset_manifest.csv'
ROOT=HERE.parents[2]
def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def resolve(recorded: str) -> Path:
    p=Path(recorded)
    return p if p.is_absolute() else ROOT/p
bad=[]; total=0
with MANIFEST.open(encoding='utf-8-sig',newline='') as f:
    for row in csv.DictReader(f):
        total+=1; p=resolve(row['path'])
        if not p.exists(): bad.append((row['path'],'MISSING'))
        else:
            actual=sha256(p)
            if actual!=row['sha256']: bad.append((row['path'],actual))
print(f'checked={total} mismatches={len(bad)}')
for path,status in bad: print(f'{status}\t{path}')
raise SystemExit(1 if bad else 0)
