"""Patch design/hero.excalidraw: refresh the 8 actant PNGs embedded in the
file from assets/actants/, WITHOUT disturbing layout the user set in Excalidraw.

Behavior:
  - bg_landscape element + file: untouched.
  - For each slug, look up its existing element by id (`actant_<slug>`).
    - If present, preserve x/y/width/height/angle/etc — only swap fileId to
      point at the freshly-embedded PNG.
    - If absent (first build, or element was deleted), create a new element
      at the LAYOUT fallback position below.
  - Orphaned file entries (no longer referenced by any element) are pruned
    so the file doesn't bloat on every re-run.

Layout philosophy (fallback only): 1600x900 canvas, actants scattered like
cartographic landmarks. Shared navy (#0e1420) + gold (#d4a149) palette means
no framing — edges blend.
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

# Fallback positions used ONLY when a slug has no existing element in the
# current excalidraw (first build, or user deleted one). Each slot specifies
# a visual CENTER (cx, cy) and a max long-side budget; aspect ratio comes
# from the cropped PNG.
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


def elem_id(slug: str) -> str:
    return f"actant_{slug.replace('-', '_')}"


def png_to_data_url(path: Path) -> tuple[str, str, bytes]:
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode()
    fid = hashlib.sha1(data).hexdigest()
    data_url = f"data:image/png;base64,{b64}"
    return fid, data_url, data


def new_element_from_layout(slot: dict, fid: str, png_path: Path, now_ms: int, seed_base: int) -> dict:
    """Build a fresh image element at the layout slot's (cx, cy), sized from
    the PNG's own aspect ratio bounded by slot['long']."""
    with Image.open(png_path) as im:
        iw, ih = im.size
    long_side = slot["long"]
    if iw >= ih:
        ew = long_side
        eh = int(round(long_side * ih / iw))
    else:
        eh = long_side
        ew = int(round(long_side * iw / ih))
    ex = slot["cx"] - ew // 2
    ey = slot["cy"] - eh // 2
    return {
        "type": "image",
        "id": elem_id(slot["slug"]),
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
    }


def main() -> None:
    ts = time.strftime("%Y%m%d-%H%M%S")
    bak = BAK_DIR / f"hero.excalidraw.bak-{ts}"
    shutil.copy2(EXCALI, bak)
    print(f"backup: {bak.name}")

    doc = json.loads(EXCALI.read_text(encoding="utf-8"))
    existing_by_id: dict[str, dict] = {
        e["id"]: e for e in doc["elements"] if e.get("type") == "image"
    }

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

        new_files[fid] = {
            "mimeType": "image/png",
            "id": fid,
            "dataURL": data_url,
            "created": now_ms,
        }

        existing = existing_by_id.get(elem_id(slug))
        if existing is not None:
            # Preserve every property the user may have tweaked (x/y/w/h/angle/
            # scale/crop/opacity). Only swap fileId, mark as saved, bump version.
            el = dict(existing)
            el["fileId"] = fid
            el["status"] = "saved"
            el["version"] = int(el.get("version", 1)) + 1
            el["versionNonce"] = (int(el.get("versionNonce", 0)) + 1) & 0x7FFFFFFF
            new_elements.append(el)
            print(
                f"  [{slug:14s}] KEEP pos ({el['x']:.0f},{el['y']:.0f}) "
                f"{el['width']:.0f}x{el['height']:.0f}  fid={fid[:10]}… bytes={len(raw)}"
            )
        else:
            seed_base = 200000 + i * 100
            el = new_element_from_layout(slot, fid, png_path, now_ms, seed_base)
            new_elements.append(el)
            print(
                f"  [{slug:14s}] NEW  pos ({el['x']},{el['y']}) "
                f"{el['width']}x{el['height']}  fid={fid[:10]}… bytes={len(raw)}  (fallback LAYOUT)"
            )

    # Preserve any non-image elements (arrows, text notes, etc.) the user added
    for e in doc["elements"]:
        if e.get("type") == "image":
            continue
        new_elements.append(e)

    doc["elements"] = new_elements
    doc["files"] = new_files

    EXCALI.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\npatched: {EXCALI}")
    print(f"elements: {len(new_elements)}, files: {len(new_files)}")


if __name__ == "__main__":
    main()
