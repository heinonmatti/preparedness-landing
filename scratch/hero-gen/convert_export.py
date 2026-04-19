"""Convert an Excalidraw PNG export into the site's hero.webp.

Reads a PNG (default: scratch/hero-gen/hero-export.png), resizes to
2400x1350 if needed (Lanczos), encodes WebP q=78, writes assets/hero.webp.

Usage:
  python scratch/hero-gen/convert_export.py                  # default paths
  python scratch/hero-gen/convert_export.py path/to/in.png   # custom source
"""
from __future__ import annotations
import shutil
import sys
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_IN = ROOT / "scratch" / "hero-gen" / "hero-export.png"
OUT_WEBP = ROOT / "assets" / "hero.webp"
BAK_DIR = ROOT / "scratch" / "hero-gen"

TARGET_W, TARGET_H = 2400, 1350
QUALITY = 78


def main() -> None:
    in_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_IN
    if not in_path.exists():
        sys.exit(f"source not found: {in_path}")

    im = Image.open(in_path).convert("RGB")
    print(f"source: {in_path.name}  {im.size[0]}x{im.size[1]}")

    if im.size != (TARGET_W, TARGET_H):
        im = im.resize((TARGET_W, TARGET_H), Image.LANCZOS)
        print(f"resized -> {TARGET_W}x{TARGET_H}")

    # Backup previous hero.webp
    if OUT_WEBP.exists():
        ts = time.strftime("%Y%m%d-%H%M%S")
        bak = BAK_DIR / f"hero.webp.bak-{ts}"
        shutil.copy2(OUT_WEBP, bak)
        print(f"backup: {bak.name}")

    im.save(OUT_WEBP, format="WEBP", quality=QUALITY, method=6)
    print(f"wrote: {OUT_WEBP}  ({OUT_WEBP.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
