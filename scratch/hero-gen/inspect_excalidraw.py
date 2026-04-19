"""Print the non-binary structure of design/hero.excalidraw.

Shows: elements summary (type, id, pos, size, customData) and files index
(fileId, mimeType, byte length) — NOT the base64 payloads.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "design" / "hero.excalidraw"

doc = json.loads(SRC.read_text(encoding="utf-8"))
print(f"top-level keys: {list(doc.keys())}")
print(f"appState keys: {list(doc.get('appState', {}).keys())[:20]}")

elements = doc.get("elements", [])
print(f"\n{len(elements)} elements:")
for e in elements:
    et = e.get("type")
    eid = e.get("id", "?")[:12]
    x = int(e.get("x", 0))
    y = int(e.get("y", 0))
    w = int(e.get("width", 0))
    h = int(e.get("height", 0))
    extra = ""
    if et == "image":
        extra = f" fileId={e.get('fileId','?')[:12]}"
    elif et == "text":
        extra = f" text={(e.get('text') or '')[:40]!r}"
    elif et == "rectangle":
        stroke = e.get("strokeColor", "")
        bg = e.get("backgroundColor", "")
        extra = f" stroke={stroke} bg={bg}"
    cd = e.get("customData")
    if cd:
        extra += f" customData={cd}"
    print(f"  {et:10s} id={eid:12s} ({x:5d},{y:5d}) {w:5d}x{h:5d}{extra}")

files = doc.get("files", {})
print(f"\n{len(files)} files:")
for fid, fdata in files.items():
    mt = fdata.get("mimeType", "?")
    blen = len(fdata.get("dataURL", "")) if "dataURL" in fdata else 0
    # dataURL is base64 with prefix; approximate original bytes:
    approx_bytes = int(blen * 0.75) if blen else 0
    print(f"  {fid[:16]:16s} mime={mt:12s} dataURL_len={blen} (~{approx_bytes} bytes)")
