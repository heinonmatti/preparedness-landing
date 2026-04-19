"""Patch design/hero.excalidraw: keep bg_landscape, replace all actant images
with 8 new dark-blueprint PNGs from assets/actants/ scattered as map landmarks.

Layout philosophy: 1600x900 canvas, actants scattered asymmetrically across
the contour map like landmarks on a cartographer's survey sketch. Since both
the contour bg and the new actants share the same navy (#0e1420) + gold
(#d4a149) palette, no framing is needed — edges blend naturally.
"""
from __future__ import annotations
import base64
import hashlib
import json
import shutil
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
EXCALI = ROOT / "design" / "hero.excalidraw"
ACTANTS = ROOT / "assets" / "actants"
BAK_DIR = ROOT / "scratch" / "hero-gen"
BAK_DIR.mkdir(parents=True, exist_ok=True)

# Landmark layout across 1600x900. Each slot specifies a visual CENTER (cx, cy)
# and a max long-side budget. The actant's aspect ratio comes from the cropped
# PNG; the short side scales proportionally. Element is centered on (cx, cy).
LAYOUT: list[dict] = [
    # slug             cx    cy   max_long_side
    {"slug": "village-house", "cx":  260, "cy":  260, "long": 260},  # upper-left rural
    {"slug": "radio",         "cx": 1370, "cy":  200, "long": 280},  # upper-right
    {"slug": "community",     "cx":  860, "cy":  320, "long": 340},  # center-upper urban
    {"slug": "neighbors",     "cx":  340, "cy":  660, "long": 300},  # left-lower
    {"slug": "supplies",      "cx":  670, "cy":  760, "long": 240},  # lower-mid-left
    {"slug": "planning",      "cx":  940, "cy":  680, "long": 250},  # center-lower
    {"slug": "emergency",     "cx": 1240, "cy":  470, "long": 260},  # right-center
    {"slug": "assessment",    "cx": 1410, "cy":  740, "long": 260},  # right-lower
]


def png_to_data_url(path: Path) -> tuple[str, str, bytes]:
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode()
    fid = hashlib.sha1(data).hexdigest()
    data_url = f"data:image/png;base64,{b64}"
    return fid, data_url, data


def main() -> None:
    # Backup first
    ts = time.strftime("%Y%m%d-%H%M%S")
    bak = BAK_DIR / f"hero.excalidraw.bak-{ts}"
    shutil.copy2(EXCALI, bak)
    print(f"backup: {bak.name}")

    doc = json.loads(EXCALI.read_text(encoding="utf-8"))

    # Keep only the bg_landscape element + its file entry.
    bg_el = next(e for e in doc["elements"] if e.get("id") == "bg_landscape")
    bg_file_id = bg_el["fileId"]
    bg_file = doc["files"][bg_file_id]

    new_elements: list[dict] = [bg_el]
    new_files: dict[str, dict] = {bg_file_id: bg_file}

    now_ms = int(time.time() * 1000)

    for i, slot in enumerate(LAYOUT, start=1):
        slug = slot["slug"]
        png_path = ACTANTS / f"{slug}.png"
        if not png_path.exists():
            raise FileNotFoundError(png_path)
        fid, data_url, raw = png_to_data_url(png_path)

        # Read actual cropped PNG aspect ratio
        with Image.open(png_path) as im:
            iw, ih = im.size

        long_side = slot["long"]
        if iw >= ih:
            ew = long_side
            eh = int(round(long_side * ih / iw))
        else:
            eh = long_side
            ew = int(round(long_side * iw / ih))

        # Center on slot center
        ex = slot["cx"] - ew // 2
        ey = slot["cy"] - eh // 2

        # File entry
        new_files[fid] = {
            "mimeType": "image/png",
            "id": fid,
            "dataURL": data_url,
            "created": now_ms,
        }

        # Image element — mimic the shape of the existing bg_landscape element
        seed_base = 200000 + i * 100
        el_id = f"actant_{slug.replace('-', '_')}"
        new_elements.append({
            "type": "image",
            "id": el_id,
            "fileId": fid,
            "status": "saved",
            "x": ex,
            "y": ey,
            "width": ew,
            "height": eh,
            "scale": [1, 1],
            "crop": None,
            "angle": 0,
            "opacity": 100,
            "strokeColor": "transparent",
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 0,
            "strokeStyle": "solid",
            "roughness": 0,
            "seed": seed_base,
            "version": 1,
            "versionNonce": seed_base + 1,
            "isDeleted": False,
            "groupIds": [],
            "boundElements": None,
            "link": None,
            "locked": False,
            "roundness": None,
        })
        print(f"  [{slug:14s}] fileId={fid[:12]}… png={iw}x{ih} el=({ex},{ey}) {ew}x{eh} bytes={len(raw)}")

    doc["elements"] = new_elements
    doc["files"] = new_files

    # Write back with a newline at end
    EXCALI.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\npatched: {EXCALI}")
    print(f"elements: {len(new_elements)}, files: {len(new_files)}")


if __name__ == "__main__":
    main()
