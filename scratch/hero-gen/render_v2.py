"""Render design/hero.excalidraw to assets/hero.webp.

Approach: skip headless-browser Excalidraw rendering. Directly composite in
Pillow from the elements we know: bg_landscape as the base, then each actant
blended with ImageChops.lighter so gold lines from both layers survive and
navy backgrounds merge invisibly.

Output: 2400x1350 PNG and WebP (q=78).
"""
from __future__ import annotations
import base64
import io
import json
import shutil
import time
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent.parent
EXCALI = ROOT / "design" / "hero.excalidraw"
OUT_WEBP = ROOT / "assets" / "hero.webp"
OUT_PNG = ROOT / "scratch" / "hero-gen" / "hero.png"
BAK_DIR = ROOT / "scratch" / "hero-gen"

NATIVE_W, NATIVE_H = 1600, 900
TARGET_W, TARGET_H = 2400, 1350
SX = TARGET_W / NATIVE_W
SY = TARGET_H / NATIVE_H
BG_HEX = "#0e1420"
BG_RGB = (0x0e, 0x14, 0x20)


def decode_embedded(data_url: str, keep_alpha: bool = False) -> Image.Image:
    _, b64 = data_url.split(",", 1)
    raw = base64.b64decode(b64)
    im = Image.open(io.BytesIO(raw))
    if keep_alpha and im.mode in ("RGBA", "LA"):
        return im.convert("RGBA")
    return im.convert("RGB")


def composite_rgba_onto_navy(actant: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Resize RGBA actant and composite onto solid navy, yielding RGB.
    Navy pixels match canvas bg, so subsequent ImageChops.lighter leaves contour
    lines visible where the actant is transparent.
    """
    if actant.mode != "RGBA":
        actant = actant.convert("RGBA")
    actant = actant.resize(size, Image.LANCZOS)
    base = Image.new("RGB", size, BG_RGB)
    base.paste(actant, (0, 0), mask=actant)
    return base


def main() -> None:
    doc = json.loads(EXCALI.read_text(encoding="utf-8"))
    elements = doc["elements"]
    files = doc["files"]

    # Backup previous hero.webp
    if OUT_WEBP.exists():
        ts = time.strftime("%Y%m%d-%H%M%S")
        bak = BAK_DIR / f"hero.webp.bak-{ts}"
        shutil.copy2(OUT_WEBP, bak)
        print(f"backup: {bak.name}")

    # Base canvas in exact navy
    canvas = Image.new("RGB", (TARGET_W, TARGET_H), BG_RGB)

    # Paste the bg_landscape first (full-frame)
    bg_el = next(e for e in elements if e.get("id") == "bg_landscape")
    bg_img = decode_embedded(files[bg_el["fileId"]]["dataURL"])
    bg_img = bg_img.resize((TARGET_W, TARGET_H), Image.LANCZOS)
    canvas = ImageChops.lighter(canvas, bg_img)
    print(f"bg_landscape composited: {bg_img.size}")

    # Composite each actant using "lighter" — gold wins over navy in both layers
    for el in elements:
        if el.get("id") == "bg_landscape":
            continue
        if el.get("type") != "image":
            continue
        fid = el["fileId"]
        img = decode_embedded(files[fid]["dataURL"], keep_alpha=True)

        tw = int(round(el["width"] * SX))
        th = int(round(el["height"] * SY))
        tx = int(round(el["x"] * SX))
        ty = int(round(el["y"] * SY))

        # RGBA -> RGB-on-navy so lighter-blend plays well
        img_rgb = composite_rgba_onto_navy(img, (tw, th))

        # Extract region from canvas, blend, paste back
        region = canvas.crop((tx, ty, tx + tw, ty + th))
        blended = ImageChops.lighter(region, img_rgb)
        canvas.paste(blended, (tx, ty))
        print(f"  {el['id']:24s} at ({tx},{ty}) size {tw}x{th}")

    # Save PNG (for inspection) and WebP
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT_PNG, format="PNG", optimize=True)
    print(f"png: {OUT_PNG} ({OUT_PNG.stat().st_size} bytes)")

    canvas.save(OUT_WEBP, format="WEBP", quality=78, method=6)
    print(f"webp: {OUT_WEBP} ({OUT_WEBP.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
