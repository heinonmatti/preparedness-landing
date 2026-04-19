"""Regenerate 8 actants in dark-blueprint line-art style via Venice nano-banana-2.

Runs all 8 in parallel via threads. Stdlib only. Saves PNGs to assets/actants/.
Also saves raw JSON blobs under scratch/hero-gen/<slug>.json for reuse by the
excalidraw patcher.

Usage: python scratch/hero-gen/generate_v2.py [--slugs s1,s2,...]
Env:   VENICE_API_KEY must be set.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import threading
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
ACTANTS_DIR = ROOT / "assets" / "actants"
OUT_DIR = ROOT / "scratch" / "hero-gen"
ACTANTS_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

API_KEY = os.environ.get("VENICE_API_KEY")
if not API_KEY:
    sys.exit("VENICE_API_KEY not set")

# Shared style prefix — keeps every actant visually coherent with the contour map.
STYLE = (
    "Antique topographic survey map detail sketch. "
    "Thin single-weight warm gold pencil line drawing on a solid deep navy blue background. "
    "ONLY two colors in the whole image: warm gold #d4a149 for the drawing lines, "
    "deep navy #0e1420 for the background. "
    "The drawing uses ONLY delicate outline strokes of uniform thin thickness, "
    "like a cartographer's hand-drawn notation. "
    "NO solid fills, NO shading, NO cross-hatching, NO tonal gradients, NO color variation. "
    "Just airy uniform-weight outline pencil strokes. "
    "Minimal, sparse, elegant composition. "
    "Generous empty dark navy negative space around and within the subject. "
    "The whole image is one small map-vignette landmark floating on the dark navy. "
    "NO frame, NO border, NO photo edge, NO paper texture, NO labels, NO text, NO compass rose. "
    "Hand-drawn feel, slightly imperfect pencil lines. "
    "Subject occupies roughly the central 60% of the frame."
)

PROMPTS: dict[str, str] = {
    "village-house": (
        "A small rural Finnish log cabin, smoke drifting in a thin curl from the stone chimney, "
        "one small figure outside carrying an armful of firewood, a single tall pine tree beside the cabin. "
        "Rural homestead landmark."
    ),
    "community": (
        "A cluster of three small modern apartment blocks with balconies, seen in a gentle three-quarter view, "
        "a few tiny human figures walking along a path in the shared courtyard garden between them. "
        "Urban neighborhood landmark."
    ),
    "radio": (
        "A tall slender lattice radio antenna mast planted in the ground, standing beside a small wooden hut, "
        "thin guy wires running from the top of the mast down to the ground on either side, "
        "one figure visible through the hut's window operating radio equipment at a desk. "
        "The mast is NOT on top of the hut — it rises from the ground next to it. "
        "Communications relay landmark."
    ),
    "neighbors": (
        "Two human figures standing on either side of a low wooden picket fence between two small houses, "
        "leaning slightly forward over the fence in friendly conversation, one with a hand raised in greeting. "
        "Social tie landmark."
    ),
    "supplies": (
        "The rear of a small utility van with its double back doors open, "
        "several stacked cardboard boxes and wooden crates visible inside, "
        "one figure standing beside the van lifting a box. "
        "Supply cache landmark."
    ),
    "emergency": (
        "Two human figures carrying a simple wooden stretcher with a blanket between them, "
        "a small cross symbol on an arm band, walking slightly uphill. "
        "Aid station landmark."
    ),
    "planning": (
        "Four human figures gathered around a small outdoor wooden table with a large unrolled paper map "
        "spread across it, one figure pointing down at the map, the others leaning in. "
        "Meeting point landmark."
    ),
    "assessment": (
        "A single figure standing on a small grassy rise, holding binoculars up to their eyes, "
        "a small notebook tucked under one arm, looking out across the terrain. "
        "Survey viewpoint landmark."
    ),
}


def venice_generate(slug: str, subject: str) -> None:
    prompt = f"{STYLE}\n\nSUBJECT: {subject}"
    body = {
        "model": "nano-banana-2",
        "prompt": prompt,
        "width": 512,
        "height": 512,
        "format": "png",
        "return_binary": False,
        "safe_mode": False,
        "hide_watermark": True,
    }
    req = urllib.request.Request(
        "https://api.venice.ai/api/v1/image/generate",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=180) as resp:
        payload = json.load(resp)
    dt = time.monotonic() - t0

    images = payload.get("images") or []
    if not images:
        raise RuntimeError(f"{slug}: no images in response: {json.dumps(payload)[:400]}")
    b64 = images[0]
    data = base64.b64decode(b64)
    png_path = ACTANTS_DIR / f"{slug}.png"
    png_path.write_bytes(data)

    json_path = OUT_DIR / f"{slug}.json"
    json_path.write_text(json.dumps({
        "slug": slug,
        "prompt": prompt,
        "b64": b64,
        "bytes": len(data),
    }))

    print(f"[{slug}] ok in {dt:.1f}s, {len(data)} bytes -> {png_path.name}", flush=True)


def main() -> None:
    # Parse --slugs filter
    slugs_filter: set[str] | None = None
    for i, arg in enumerate(sys.argv):
        if arg == "--slugs" and i + 1 < len(sys.argv):
            slugs_filter = {s.strip() for s in sys.argv[i + 1].split(",") if s.strip()}

    to_run = {k: v for k, v in PROMPTS.items() if slugs_filter is None or k in slugs_filter}
    if slugs_filter is not None:
        missing = slugs_filter - to_run.keys()
        if missing:
            sys.exit(f"unknown slugs: {sorted(missing)}")

    threads = []
    errors: list[tuple[str, BaseException]] = []

    def run(slug: str, subject: str) -> None:
        try:
            venice_generate(slug, subject)
        except BaseException as e:
            errors.append((slug, e))
            print(f"[{slug}] FAIL: {e}", flush=True)

    for slug, subject in to_run.items():
        t = threading.Thread(target=run, args=(slug, subject), name=slug)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    if errors:
        print(f"\n{len(errors)} failed:")
        for slug, e in errors:
            print(f"  - {slug}: {e}")
        sys.exit(1)
    print(f"\nall {len(to_run)} actants generated.")


if __name__ == "__main__":
    main()
