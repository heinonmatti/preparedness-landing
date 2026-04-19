"""Post-process each actant PNG:
 1. Convert RGB → RGBA with alpha proportional to RGB distance from the navy
    background (#0e1420). Navy pixels → transparent; gold-line pixels → opaque;
    anti-aliased edges get smooth partial alpha.
 2. Tight-crop to bbox of pixels where alpha > 5, plus a small padding margin.
 3. Write back to assets/actants/<slug>.png as RGBA PNG.

Raw originals (solid navy bg, full 512x512) are preserved via the <slug>.json
blobs saved by generate_v2.py.
"""
from __future__ import annotations
import numpy as np
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
ACTANTS = ROOT / "assets" / "actants"

BG = np.array([0x0e, 0x14, 0x20], dtype=np.float32)  # navy
ALPHA_LOW = 20.0   # distance <= LOW => alpha 0
ALPHA_HIGH = 80.0  # distance >= HIGH => alpha 255
CROP_PAD = 12      # pixels of padding around content bbox after crop
MIN_ALPHA_FOR_BBOX = 6  # alpha threshold for inclusion in crop bbox


def process(path: Path) -> None:
    img = Image.open(path).convert("RGB")
    arr = np.asarray(img, dtype=np.float32)  # H, W, 3

    # Per-pixel distance from navy
    diff = arr - BG
    dist = np.sqrt((diff * diff).sum(axis=-1))  # H, W

    # Smooth alpha ramp
    alpha = np.clip((dist - ALPHA_LOW) / (ALPHA_HIGH - ALPHA_LOW), 0.0, 1.0)
    alpha_u8 = (alpha * 255.0).astype(np.uint8)

    # Build RGBA
    rgba = np.concatenate([arr.astype(np.uint8), alpha_u8[..., None]], axis=-1)

    # Find bbox of pixels where alpha exceeds threshold
    mask = alpha_u8 > MIN_ALPHA_FOR_BBOX
    ys, xs = np.where(mask)
    if len(xs) == 0:
        print(f"  [{path.stem}] empty (all transparent) — skipping")
        return
    x0, x1 = xs.min(), xs.max()
    y0, y1 = ys.min(), ys.max()

    # Pad, but clamp to image bounds
    h, w = alpha_u8.shape
    x0 = max(0, int(x0) - CROP_PAD)
    y0 = max(0, int(y0) - CROP_PAD)
    x1 = min(w - 1, int(x1) + CROP_PAD)
    y1 = min(h - 1, int(y1) + CROP_PAD)

    cropped = rgba[y0:y1 + 1, x0:x1 + 1]

    out = Image.fromarray(cropped, mode="RGBA")
    out.save(path, format="PNG", optimize=True)
    print(f"  [{path.stem:14s}] {w}x{h} -> {out.size[0]}x{out.size[1]}  alpha-keyed, cropped")


def main() -> None:
    pngs = sorted(ACTANTS.glob("*.png"))
    if not pngs:
        raise SystemExit(f"no PNGs in {ACTANTS}")
    print(f"processing {len(pngs)} actants in {ACTANTS}:")
    for p in pngs:
        process(p)


if __name__ == "__main__":
    main()
