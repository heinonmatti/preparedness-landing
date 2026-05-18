"""Thicken the lines in each actant PNG via morphological dilation on the alpha
channel. Also normalizes RGB to pure gold so dilated edges don't pick up the
navy halo from the postprocess ramp.

First run snapshots the pre-thicken state to scratch/hero-gen/actants-pre-thicken/.
Subsequent runs always dilate from that snapshot — so re-running with a
different DILATION doesn't compound.

DILATION may be fractional (e.g. 0.5). For non-integer values the alpha channel
is supersampled 2x before applying an integer MaxFilter, then downsampled —
effectively giving sub-pixel line growth at native resolution.

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
DEFAULT_DILATION = 0.5  # half-width in pixels; may be fractional

# Per-file dilation overrides for assets whose inner geometry is too dense
# for the global default (e.g. window grids, antenna lattice fuse together).
# Key = filename in assets/actants/, value = half-width in pixels.
OVERRIDES: dict[str, float] = {}


def thicken(src: Path, dst: Path, dilation: float) -> None:
    img = Image.open(src).convert("RGBA")
    _, _, _, a = img.split()
    if dilation == int(dilation):
        k = 2 * int(dilation) + 1
        a_thick = a.filter(ImageFilter.MaxFilter(k))
    else:
        # Supersample 2x, apply integer-equivalent kernel, downsample.
        # 2x scale doubles effective pixel resolution, so dilation*2 px there
        # = dilation px back at native resolution.
        scale = 2
        big = a.resize((a.width * scale, a.height * scale), Image.LANCZOS)
        k_big = 2 * round(scale * dilation) + 1
        big_thick = big.filter(ImageFilter.MaxFilter(k_big))
        a_thick = big_thick.resize(a.size, Image.LANCZOS)
    solid_r = Image.new("L", img.size, GOLD[0])
    solid_g = Image.new("L", img.size, GOLD[1])
    solid_b = Image.new("L", img.size, GOLD[2])
    out = Image.merge("RGBA", (solid_r, solid_g, solid_b, a_thick))
    out.save(dst, format="PNG", optimize=True)
    print(f"  [{src.stem:14s}] {img.size[0]}x{img.size[1]} dilated {dilation:g}px")


def main() -> None:
    dilation = DEFAULT_DILATION
    if len(sys.argv) > 1:
        dilation = float(sys.argv[1])

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
    print(f"thickening {len(originals)} actants from backup, DILATION={dilation:g}px (overrides: {OVERRIDES or 'none'}):")
    for src in originals:
        dst = ACTANTS / src.name
        thicken(src, dst, OVERRIDES.get(src.name, dilation))


if __name__ == "__main__":
    main()
