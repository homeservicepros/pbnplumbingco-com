#!/usr/bin/env python3
"""Swap a placeholder photo for a real one without touching any code.

    python3 -I scripts/swap_photo.py --list
    python3 -I scripts/swap_photo.py van-1 ~/Downloads/real-van.jpg
    npm run photo -- team-composite ~/Downloads/crew.heic

The new image replaces src/assets/photos/<name>.webp (resized to at most 1600 px wide, WebP q82). Every page that
uses the slot picks it up on the next build; Astro regenerates the AVIF/WebP/srcset variants. Any aspect ratio works
(images are cropped with object-fit: cover), 16:9 landscape is ideal; "technician-greeting" is square.

After swapping, update the description of the photo in src/lib/media.ts (PHOTO_ALT) so the alt text matches the new image.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
PHOTOS = ROOT / "src/assets/photos"


def usage_of(name: str) -> list[str]:
    hits = []
    for f in sorted((ROOT / "src").rglob("*")):
        if f.suffix in {".astro", ".ts"} and f.is_file():
            text = f.read_text(encoding="utf8")
            if re.search(rf"['\"]{re.escape(name)}['\"]", text):
                hits.append(f.relative_to(ROOT).as_posix())
    return hits


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", nargs="?", help="photo slot, e.g. van-1 (see --list)")
    ap.add_argument("source", nargs="?", help="path to the new image (jpg/png/webp/…)")
    ap.add_argument("--list", action="store_true", help="show every photo slot with size and where it is used")
    ap.add_argument("--max-width", type=int, default=1600)
    ap.add_argument("--quality", type=int, default=82)
    a = ap.parse_args()

    if a.list or not a.name:
        for f in sorted(PHOTOS.glob("*.webp")):
            w, h = Image.open(f).size
            print(f"{f.stem:22s} {w}x{h:<5d} used in: {', '.join(usage_of(f.stem)) or '—'}")
        return

    target = PHOTOS / f"{a.name}.webp"
    if not target.exists():
        sys.exit(f"Unknown photo slot '{a.name}'. Run with --list to see the available names.")
    if not a.source or not Path(a.source).expanduser().is_file():
        sys.exit("Give the path to the new image as the second argument.")

    im = ImageOps.exif_transpose(Image.open(Path(a.source).expanduser())).convert("RGB")
    if im.width > a.max_width:
        im = im.resize((a.max_width, round(im.height * a.max_width / im.width)), Image.LANCZOS)
    old = Image.open(target).size
    im.save(target, "WEBP", quality=a.quality, method=6)
    print(f"{a.name}: {old[0]}x{old[1]} → {im.width}x{im.height} ({target.stat().st_size // 1024} kB)")
    print("Used in:", ", ".join(usage_of(a.name)) or "—")
    print("Next: update its alt text in src/lib/media.ts (PHOTO_ALT), then `npm run build`.")


if __name__ == "__main__":
    main()
