#!/usr/bin/env python3
"""Turn the "Buffalo Plumbing PROS media pack" (WebP, 100% quality) into repo-ready assets.

    python3 -I scripts/prepare_media.py <unzipped-webp-pack-dir>

Outputs (all committed):
  src/assets/photos/*.webp   re-encoded sources (q82). Astro's <Picture> builds AVIF/WebP/srcset from these.
  src/assets/brand/*.png     transparent logo variants (navy for light bg, white for dark bg), shield mark,
                             cut-out trust badges.
  public/favicon*.png, apple-touch-icon.png, icon-*.png, favicon.ico, og-default.jpg

Not used on purpose: "Conversion Graphics/Overlay 2" (a mock "5-star verified customer review" card).
"""
from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

PACK = Path(sys.argv[1])
ROOT = Path(__file__).resolve().parent.parent
PHOTOS = ROOT / "src/assets/photos"
BRAND = ROOT / "src/assets/brand"
PUBLIC = ROOT / "public"
for d in (PHOTOS, BRAND, PUBLIC):
    d.mkdir(parents=True, exist_ok=True)

PHOTO_MAP = {
    "Authority Assets/Business Exterior": "business-exterior",
    "Authority Assets/Owner Portrait": "owner-portrait",
    "Authority Assets/Team Composite": "team-composite",
    "Authority Assets/Workspace Interior": "workspace-interior",
    "Backgrounds/Header Background": "bg-header",
    "Backgrounds/Footer Background": "bg-footer",
    "Before & After/Before & After 1": "before-after-1",
    "Before & After/Before & After 2": "before-after-2",
    "Before & After/Before & After 3": "before-after-3",
    "Before & After/Before & After 4": "before-after-4",
    "Conversion Graphics/Overlay 1": "technician-greeting",
    "Field Presence/Branded Van 1": "van-1",
    "Field Presence/Branded Van 2": "van-2",
    "Field Presence/Technician Unloading": "technician-unloading",
    "Service Headers/Residential 1": "residential-1",
    "Service Headers/Residential 2": "residential-2",
    "Service Headers/Residential 3": "residential-3",
    "Service Headers/Residential 4": "residential-4",
    "Service Headers/Commercial 1": "commercial-1",
    "Service Headers/Commercial 2": "commercial-2",
    "Service Headers/Commercial 3": "commercial-3",
    "Service Headers/Commercial 4": "commercial-4",
}


def open_rgb(rel: str) -> Image.Image:
    return Image.open(PACK / f"{rel}.webp").convert("RGB")


# ----------------------------------------------------------------------------- phone-number retouching (optional step)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import phone_retouch as pr  # noqa: E402

stale: list[str] = []


def retouched(name: str, im: Image.Image, recipes: dict) -> Image.Image:
    fn = recipes.get(name)
    if fn is None:
        return im
    try:
        out = fn(im)
        print("  retouched phone number on", name)
        return out
    except (ImportError, FileNotFoundError) as e:
        stale.append(name)
        print(f"  !! could not retouch {name}: {e}")
        return im


# ----------------------------------------------------------------------------- photos
photos: dict[str, Image.Image] = {}
for rel, name in PHOTO_MAP.items():
    im = retouched(name, open_rgb(rel), pr.PHOTO_RECIPES)
    photos[name] = im
    im.save(PHOTOS / f"{name}.webp", "WEBP", quality=82, method=6)
    print("photo", name, im.size)


# ----------------------------------------------------------------------------- logo (colour-to-alpha on white)
def color_to_alpha(im: Image.Image, floor: float = 0.06) -> Image.Image:
    a = np.asarray(im.convert("RGB")).astype(np.float64)
    alpha = 1.0 - a.min(axis=2) / 255.0
    alpha = np.clip((alpha - floor) / (1.0 - floor), 0, 1)
    safe = np.where(alpha > 0, alpha, 1.0)[..., None]
    rgb = np.clip((a - (1 - alpha[..., None]) * 255.0) / safe, 0, 255)
    out = np.dstack([rgb, alpha * 255.0]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def trim(im: Image.Image, pad: int = 0) -> Image.Image:
    bbox = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    l, t, r, b = bbox
    return im.crop((max(l - pad, 0), max(t - pad, 0), min(r + pad, im.width), min(b + pad, im.height)))


def whiten(im: Image.Image) -> Image.Image:
    a = im.getchannel("A")
    out = Image.new("RGBA", im.size, (255, 255, 255, 0))
    out.putalpha(a)
    return out


logo_src = open_rgb("Logo Creation/Logo/Logo-(current)")
logo_src = logo_src.crop((8, 8, logo_src.width - 8, logo_src.height - 8))  # 1px grey frame in the source
logo_rgba = color_to_alpha(logo_src)
full = trim(logo_rgba, pad=6)
full.save(BRAND / "logo-full.png", optimize=True)
whiten(full).save(BRAND / "logo-full-white.png", optimize=True)

# The shield mark = rows above the wordmark. Find the first fully-empty row band below the shield.
alpha_rows = np.asarray(logo_rgba.getchannel("A")).max(axis=1) > 20
ys = np.where(alpha_rows)[0]
gaps = [(ys[i], ys[i + 1]) for i in range(len(ys) - 1) if ys[i + 1] - ys[i] > 12]
split = gaps[0][0] + 1
mark = trim(logo_rgba.crop((0, 0, logo_rgba.width, split)), pad=4)
mark.save(BRAND / "logo-mark.png", optimize=True)
whiten(mark).save(BRAND / "logo-mark-white.png", optimize=True)
print("logo", full.size, "mark", mark.size, "split row", split)


# ----------------------------------------------------------------------------- trust badges (cut out of white)
def cut_out(im: Image.Image, thresh: int = 244) -> Image.Image:
    """Flood-fill the white backdrop from the border so interior whites (text/highlights) survive."""
    im = im.convert("RGB").crop((8, 8, im.width - 8, im.height - 8))
    px = np.asarray(im).astype(int)
    h, w, _ = px.shape
    near_white = (px.min(axis=2) >= thresh)
    seen = np.zeros((h, w), bool)
    q: deque[tuple[int, int]] = deque()
    for x in range(w):
        for y in (0, h - 1):
            if near_white[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if near_white[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and near_white[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                q.append((ny, nx))
    alpha = Image.fromarray(np.where(seen, 0, 255).astype(np.uint8), "L")
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.0))  # shave halo, soften edge
    out = im.convert("RGBA")
    out.putalpha(alpha)
    return trim(out, pad=4)


for rel, name in (("Conversion Graphics/Trust Badge 1", "badge-shield"), ("Conversion Graphics/Trust Badge 2", "badge-emergency")):
    b = cut_out(open_rgb(rel))
    b.thumbnail((640, 640), Image.LANCZOS)
    b = retouched(name, b, pr.BADGE_RECIPES)
    b.save(BRAND / f"{name}.png", optimize=True)
    print("badge", name, b.size)


# ----------------------------------------------------------------------------- favicons / app icons
def square_icon(mark_im: Image.Image, size: int, bg=None, pad_ratio: float = 0.14) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), bg or (0, 0, 0, 0))
    inner = int(size * (1 - 2 * pad_ratio))
    m = mark_im.copy()
    m.thumbnail((inner, inner), Image.LANCZOS)
    canvas.alpha_composite(m, ((size - m.width) // 2, (size - m.height) // 2))
    return canvas


square_icon(mark, 512, bg=(255, 255, 255, 255)).save(PUBLIC / "icon-512.png", optimize=True)
square_icon(mark, 192, bg=(255, 255, 255, 255)).save(PUBLIC / "icon-192.png", optimize=True)
square_icon(mark, 180, bg=(255, 255, 255, 255), pad_ratio=0.12).save(PUBLIC / "apple-touch-icon.png", optimize=True)
fav = square_icon(mark, 96, pad_ratio=0.04)
fav.save(PUBLIC / "favicon-96.png", optimize=True)
fav.save(PUBLIC / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])


# ----------------------------------------------------------------------------- OG image (1200x630)
W, H = 1200, 630
og = Image.new("RGB", (W, H), (9, 30, 66))
photo = photos["van-1"].copy()  # the retouched hero van
scale = H / photo.height
photo = photo.resize((int(photo.width * scale), H), Image.LANCZOS)
PHOTO_X = 300
og.paste(photo.crop((photo.width - (W - PHOTO_X), 0, photo.width, H)), (PHOTO_X, 0))
# navy panel on the left that stays solid under the logo, then fades into the photo (no visible seam)
arr = np.zeros((H, W, 4), np.uint8)
for x in range(W):
    t = min(max((x - 440) / 330, 0), 1)  # 0 → solid, 1 → clear
    arr[:, x] = (9, 30, 66, int(255 * (1 - t)))
og = Image.alpha_composite(og.convert("RGBA"), Image.fromarray(arr, "RGBA"))
logo_w = whiten(full).copy()
logo_w.thumbnail((340, 340), Image.LANCZOS)
og.alpha_composite(logo_w, (64, (H - logo_w.height) // 2))
og.convert("RGB").save(PUBLIC / "og-default.jpg", quality=86, optimize=True, progressive=True)
if stale:
    print("\n*** WARNING: these images still show the OLD phone number:", ", ".join(stale), "***")
print("done")
