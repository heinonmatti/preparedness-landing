"""Thicken the lines in each actant PNG via morphological dilation on the alpha
channel. Also normalizes RGB to pure gold so dilated edges don't pick up the
navy halo from the postprocess ramp.

First run snapshots the pre-thicken state to scratch/hero-gen/actants-pre-thicken/.
Subsequent runs always dilate from that snapshot — so re-running with a
different DILATION doesn't compound.

Usage: python scratch/hero-gen/dilate_lines.py [DILATION]
       DILATION defaults to 2 (adds ~2px to each side of every line).
"""
from __future__ import annotations
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent.parent
ACTANTS = ROOT / "assets" / "actants"
BACKUP = ROOT / "scratch" / "hero-gen" / "actants-pre-thicken"

GOLD = (0xd4, 0xa1, 0x49)
DEFAULT_DILATION = 2  # half-width in pixels; kernel size = 2*DILATION + 1


def thicken(src: Path, dst: Path, dilation: int) -> None:
    img = Image.open(src).convert("RGBA")
    _, _, _, a = img.split()
    k = 2 * dilation + 1
    a_thick = a.filter(ImageFilter.MaxFilter(k))
    solid_r = Image.new("L", img.size, GOLD[0])
    solid_g = Image.new("L", img.size, GOLD[1])
    solid_b = Image.new("L", img.size, GOLD[2])
    out = Image.merge("RGBA", (solid_r, solid_g, solid_b, a_thick))
    out.save(dst, format="PNG", optimize=True)
    print(f"  [{src.stem:14s}] {img.size[0]}x{img.size[1]} dilated {dilation}px")


def main() -> None:
    dilation = DEFAULT_DILATION
    if len(sys.argv) > 1:
        dilation = int(sys.argv[1])

    if not BACKUP.exists():
        BACKUP.mkdir(parents=True, exist_ok=True)
        src_pngs = sorted(ACTANTS.glob("*.png"))
        if not src_pngs:
            raise SystemExit(f"no PNGs in {ACTANTS}")
        for p in src_pngs:
            shutil.copy2(p, BACKUP / p.name)
        print(f"backup created: {BACKUP} ({len(src_pngs)} PNGs)")
    else:
        print(f"backup exists: {BACKUP} (reusing)")

    originals = sorted(BACKUP.glob("*.png"))
    print(f"thickening {len(originals)} actants from backup, DILATION={dilation}px:")
    for src in originals:
        dst = ACTANTS / src.name
        thicken(src, dst, dilation)


if __name__ == "__main__":
    main()
