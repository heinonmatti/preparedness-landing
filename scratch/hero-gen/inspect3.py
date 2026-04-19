import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
doc = json.loads((ROOT / "design" / "hero.excalidraw").read_text(encoding="utf-8"))

# print keys of first file entry + first image element (no blob data)
first_fid = next(iter(doc["files"]))
f0 = doc["files"][first_fid]
print("file entry keys:", list(f0.keys()))
for k, v in f0.items():
    if k == "dataURL":
        print(f"  {k}: (len={len(v)}) starts {v[:50]!r}")
    else:
        print(f"  {k}: {v!r}")

print()
for e in doc["elements"]:
    if e["type"] == "image":
        print("image element keys:", list(e.keys()))
        for k, v in e.items():
            print(f"  {k}: {v!r}")
        break
