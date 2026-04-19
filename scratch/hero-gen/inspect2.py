import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
doc = json.loads((ROOT / "design" / "hero.excalidraw").read_text(encoding="utf-8"))
print("viewBackgroundColor:", doc["appState"].get("viewBackgroundColor"))
print("gridSize:", doc["appState"].get("gridSize"))

for e in doc["elements"]:
    if e["type"] == "image":
        print(f"\n{e['id']}:")
        print(f"  pos=({e['x']},{e['y']}) size={e['width']}x{e['height']}")
        print(f"  angle={e.get('angle')} strokeColor={e.get('strokeColor')} backgroundColor={e.get('backgroundColor')}")
        print(f"  locked={e.get('locked')} opacity={e.get('opacity')}")
        print(f"  fileId={e.get('fileId')}")
        print(f"  status={e.get('status')}")
