"""Replace the old phone number that is baked into six media-pack images with the current one.

The AI-generated media pack printed "(716) 610-1160" on the vans, a sign and both trust badges. These helpers erase the old
digits (adaptive text mask + OpenCV inpainting) and redraw the new number in a matching typeface, following each surface's
perspective. `prepare_media.py` calls them; every image touched is listed in RETOUCHED below.

Needs (one-off, not project dependencies):
    pip install opencv-python-headless fonttools brotli numpy pillow
    npm i --no-save @fontsource/bebas-neue @fontsource/roboto-condensed @fontsource/montserrat   # (or set RETOUCH_FONTS)

These are stop-gaps. The proper fix is regenerating/photographing the vans and badges with the new number and swapping them in
with `npm run photo`.
"""
from __future__ import annotations

import math
import os
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

NEW_PHONE = "(716) 663-0186"
RETOUCHED = ["van-1", "van-2", "technician-unloading", "business-exterior", "badge-emergency", "badge-shield"]

ROOT = Path(__file__).resolve().parent.parent
_font_cache: dict[tuple[str, str], Path] = {}


# ------------------------------------------------------------------------------------------------ fonts
def font_path(family: str, weight: str) -> Path:
    """TTF for an @fontsource family (converted once from its woff2)."""
    key = (family, weight)
    if key in _font_cache:
        return _font_cache[key]
    from fontTools.ttLib import TTFont

    roots = [Path(p) for p in os.environ.get("RETOUCH_FONTS", "").split(os.pathsep) if p] + [ROOT]
    for r in roots:
        src = r / "node_modules/@fontsource" / family / "files" / f"{family}-latin-{weight}-normal.woff2"
        if src.exists():
            out = Path(tempfile.gettempdir()) / f"retouch-{family}-{weight}.ttf"
            f = TTFont(src)
            f.flavor = None
            f.save(out)
            _font_cache[key] = out
            return out
    raise FileNotFoundError(f"font {family} {weight} not found — run: npm i --no-save @fontsource/{family}")


def font(family: str, weight: str, size: float) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(font_path(family, weight)), size=max(1, round(size * 4)))  # drawn at 4× then downsampled


# ------------------------------------------------------------------------------------------------ primitives
def _cv2():
    import cv2  # noqa: PLC0415 — optional dependency, imported lazily

    return cv2


def text_mask(rgb: np.ndarray, box: tuple[int, int, int, int], light_text: bool, thresh: int = 28, grow: int = 2, margin: int = 2) -> np.ndarray:
    """Mask of glyph pixels inside `box` (x0, y0, x1, y1). The local background is estimated with a morphological
    close/open wider than any stroke, so gradients and panel curvature do not matter."""
    cv2 = _cv2()
    x0, y0, x1, y1 = box
    pad = 12
    X0, Y0, X1, Y1 = max(x0 - pad, 0), max(y0 - pad, 0), min(x1 + pad, rgb.shape[1]), min(y1 + pad, rgb.shape[0])
    lum = cv2.cvtColor(rgb[Y0:Y1, X0:X1], cv2.COLOR_RGB2GRAY).astype(np.int16)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
    if light_text:  # light glyphs on a darker surface: background = opening
        bg = cv2.morphologyEx(lum.astype(np.uint8), cv2.MORPH_OPEN, k).astype(np.int16)
        m = (lum - bg) > thresh
    else:
        bg = cv2.morphologyEx(lum.astype(np.uint8), cv2.MORPH_CLOSE, k).astype(np.int16)
        m = (bg - lum) > thresh
    full = np.zeros(rgb.shape[:2], np.uint8)
    sub = np.zeros((Y1 - Y0, X1 - X0), np.uint8)
    sub[m] = 255
    # keep only the requested box (+ a small margin)
    keep = np.zeros_like(sub)
    keep[max(y0 - Y0 - margin, 0) : y1 - Y0 + margin, max(x0 - X0 - margin, 0) : x1 - X0 + margin] = 255
    sub = cv2.bitwise_and(sub, keep)
    if grow:
        sub = cv2.dilate(sub, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * grow + 1, 2 * grow + 1)))
        sub = cv2.bitwise_and(sub, keep) if margin == 0 else sub  # with margin=0 the box is a hard limit (protects neighbours)
    full[Y0:Y1, X0:X1] = sub
    return full


def erase(rgb: np.ndarray, mask: np.ndarray, radius: int = 4) -> np.ndarray:
    cv2 = _cv2()
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    out = cv2.inpaint(bgr, mask, radius, cv2.INPAINT_TELEA)
    return cv2.cvtColor(out, cv2.COLOR_BGR2RGB)


def sample_color(rgb: np.ndarray, mask: np.ndarray) -> tuple[int, int, int]:
    """Core colour of the glyphs (median of the most extreme 40 % inside the mask, so anti-aliased fringes don't count)."""
    px = rgb[mask > 0].astype(np.float32)
    lum = px.mean(axis=1)
    return tuple(int(v) for v in np.median(px[lum <= np.percentile(lum, 40)], axis=0))  # darkest 40 %


def sample_color_light(rgb: np.ndarray, mask: np.ndarray) -> tuple[int, int, int]:
    px = rgb[mask > 0].astype(np.float32)
    lum = px.mean(axis=1)
    return tuple(int(v) for v in np.median(px[lum >= np.percentile(lum, 60)], axis=0))  # lightest 40 %


def render_text(text: str, fnt: ImageFont.FreeTypeFont, fill: tuple[int, int, int], tracking: float = 0.0, embolden: float = 0.0) -> Image.Image:
    """RGBA layer (4× supersampled) with `text` baseline-aligned, tight to the ink."""
    asc, desc = fnt.getmetrics()
    widths = [fnt.getlength(ch) for ch in text]
    w = int(sum(widths) + tracking * 4 * (len(text) - 1)) + 16
    layer = Image.new("RGBA", (w, asc + desc + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x = 8.0
    for ch, cw in zip(text, widths):
        d.text((x, 4), ch, font=fnt, fill=fill + (255,), stroke_width=round(embolden * 4), stroke_fill=fill + (255,))
        x += cw + tracking * 4
    return layer.crop(layer.getbbox())


def paste_quad(rgb: np.ndarray, layer: Image.Image, quad: list[tuple[float, float]], blur: float = 0.55, keep_out: np.ndarray | None = None) -> np.ndarray:
    """Warp the text layer onto the destination quad (TL, TR, BR, BL), soften it a touch, and alpha-composite it.
    `keep_out` is a mask (255 = do not paint) for things standing in front of the lettering."""
    cv2 = _cv2()
    h, w = rgb.shape[:2]
    lw, lh = layer.size
    src = np.float32([[0, 0], [lw, 0], [lw, lh], [0, lh]])
    dst = np.float32(quad)
    M = cv2.getPerspectiveTransform(src, dst)
    arr = np.asarray(layer).astype(np.float32)
    # premultiply for clean edges
    arr[..., :3] *= arr[..., 3:4] / 255.0
    warped = cv2.warpPerspective(arr, M, (w, h), flags=cv2.INTER_AREA if lw > 3 * (dst[1][0] - dst[0][0]) else cv2.INTER_CUBIC)
    a = warped[..., 3:4] / 255.0
    if blur:
        a = cv2.GaussianBlur(a, (0, 0), blur)[..., None] if a.ndim == 2 else cv2.GaussianBlur(a[..., 0], (0, 0), blur)[..., None]
        for c in range(3):
            warped[..., c] = cv2.GaussianBlur(warped[..., c], (0, 0), blur)
    if keep_out is not None:
        a = a * (1 - (keep_out[..., None].astype(np.float32) / 255.0))
        warped[..., :3] *= 1 - (keep_out[..., None].astype(np.float32) / 255.0)
    out = rgb.astype(np.float32) * (1 - a) + warped[..., :3]
    return np.clip(out, 0, 255).astype(np.uint8)


def polygon_mask(shape: tuple[int, int], pts: list[tuple[int, int]]) -> np.ndarray:
    cv2 = _cv2()
    m = np.zeros(shape, np.uint8)
    cv2.fillPoly(m, [np.array(pts, np.int32)], 255)
    return m


def draw_arc_text(rgb: np.ndarray, text: str, fnt: ImageFont.FreeTypeFont, fill: tuple[int, int, int], center: tuple[float, float], radius: float,
                  span_deg: float, mid_deg: float = 0.0, blur: float = 0.5) -> np.ndarray:
    """Smile-shaped text: baseline on a circle of `radius` around `center`, letter tops pointing at the centre.
    The string is spread over `span_deg` degrees centred on `mid_deg` (0° = straight below the centre)."""
    base = Image.fromarray(rgb).convert("RGBA")
    widths = [fnt.getlength(ch) / 4 for ch in text]
    natural = sum(widths)
    arc_len = math.radians(span_deg) * radius
    track = (arc_len - natural) / max(len(text) - 1, 1)
    pos = 0.0
    asc, desc = fnt.getmetrics()
    for ch, cw in zip(text, widths):
        mid = pos + cw / 2
        theta = math.radians(mid_deg) + (mid - arc_len / 2) / radius  # angle from straight-down, +ve to the right
        glyph = Image.new("RGBA", (int(cw * 4) + 24, asc + desc + 24), (0, 0, 0, 0))
        ImageDraw.Draw(glyph).text((12 + (glyph.width - 24 - fnt.getlength(ch)) / 2, 12), ch, font=fnt, fill=fill + (255,))
        # rotate so the glyph's "up" points to the centre: left of centre (θ<0) turns clockwise, right turns counter-clockwise
        rot = glyph.rotate(math.degrees(theta), resample=Image.BICUBIC, expand=True)
        rot = rot.resize((max(1, rot.width // 4), max(1, rot.height // 4)), Image.LANCZOS)
        # glyph baseline sits `desc` above the bottom of its canvas; place that baseline point on the circle
        bx = center[0] + radius * math.sin(theta)
        by = center[1] + radius * math.cos(theta)
        # vector from baseline point towards the glyph's visual centre (towards the circle centre by half the x-height-ish)
        half = (asc - 6) / 4 / 2 * 1.0
        cx = bx - half * math.sin(theta)
        cy = by - half * math.cos(theta)
        base.alpha_composite(rot, (int(round(cx - rot.width / 2)), int(round(cy - rot.height / 2))))
        pos += cw + track
    out = np.asarray(base.convert("RGB"))
    return out


# ------------------------------------------------------------------------------------------------ per-image recipes
def retouch_badge_emergency(rgba: Image.Image) -> Image.Image:
    """Circular badge: white band at the bottom with navy 'PHONE: (716) …' on an arc concentric with the badge."""
    cv2 = _cv2()
    rgb = np.asarray(rgba.convert("RGB")).copy()
    alpha = rgba.getchannel("A")
    h, w = rgb.shape[:2]
    # glyphs = very dark navy pixels inside the text band (radius from the badge centre), away from the rings
    lum = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.hypot(xx - 316.0, yy - 320.0)
    ang = np.degrees(np.arctan2(xx - 316.0, yy - 320.0))  # 0° = straight below the centre
    in_band = (rr > 236) & (rr < 282) & (np.abs(ang) < 38)
    mask = ((lum < 120) & in_band).astype(np.uint8) * 255
    blue_ish = (rgb[..., 2].astype(int) - rgb[..., 0].astype(int)) > 60
    mask[blue_ish] = 0
    mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    mask[~in_band] = 0
    navy = sample_color(rgb, mask)
    rgb[mask > 0] = (255, 255, 255)
    fnt = font("bebas-neue", "400", 37.5)  # cap-height ≈ 0.7 em
    out = draw_arc_text(rgb, f"PHONE: {NEW_PHONE}", fnt, navy, center=(316.0, 320.0), radius=272.5, span_deg=64.5, mid_deg=-0.5)
    res = Image.fromarray(out).convert("RGBA")
    res.putalpha(alpha)
    return res


def retouch_badge_shield(rgba: Image.Image) -> Image.Image:
    """Shield badge: small white 'Phone: (716) …' on a smooth blue field."""
    rgb = np.asarray(rgba.convert("RGB")).copy()
    alpha = rgba.getchannel("A")
    box = (182, 541, 362, 569)
    mask = text_mask(rgb, box, light_text=True, thresh=30, grow=2)
    fg = (250, 252, 255)  # the original glyphs are white; sampling picks up the blue fringe
    rgb = erase(rgb, mask, radius=5)
    fnt = font("roboto-condensed", "700", 21.5)
    layer = render_text(f"Phone: {NEW_PHONE}", fnt, fg, tracking=0.0)
    x0, y0, x1, y1 = 185.5, 545.0, 358.5, 565.0
    # fit the ink to the original text box height/width
    scale = (x1 - x0) / (layer.width / 4)
    lh = layer.height / 4 * scale
    cy = (y0 + y1) / 2 + 0.5
    quad = [(x0, cy - lh / 2), (x1, cy - lh / 2), (x1, cy + lh / 2), (x0, cy + lh / 2)]
    rgb = paste_quad(rgb, layer, quad, blur=0.3)
    res = Image.fromarray(rgb).convert("RGBA")
    res.putalpha(alpha)
    return res


def replace_text(rgb: np.ndarray, box: tuple[int, int, int, int], quad: list[tuple[float, float]], text: str, family: str, weight: str,
                 light_text: bool, size_hint: float = 40, blur: float = 0.7, fill: tuple[int, int, int] | None = None,
                 keep_out: np.ndarray | None = None, thresh: int = 28, grow: int = 2, erase_radius: int = 4, embolden: float = 0.0, margin: int = 2,
                 within: np.ndarray | None = None) -> np.ndarray:
    """Erase the glyphs inside `box` and draw `text` so its ink fills `quad` (TL, TR, BR, BL)."""
    mask = text_mask(rgb, box, light_text, thresh, grow, margin)
    if within is not None:
        mask[within == 0] = 0  # only erase inside this band (e.g. along a tilted text line)
    if keep_out is not None:
        mask[keep_out > 0] = 0  # never erase things standing in front of the lettering
    if fill is None:
        fill = (sample_color_light if light_text else sample_color)(rgb, mask)
    cleaned = erase(rgb, mask, erase_radius)
    layer = render_text(text, font(family, weight, size_hint), fill, embolden=embolden)
    return paste_quad(cleaned, layer, quad, blur, keep_out)


def retouch_van_1(img: Image.Image) -> Image.Image:
    """Hero van: navy 'PHONE: (716) 610-1160' on the white side panel. Only '610-1160' changes; it tilts up ~4° and shrinks ~7 %
    towards the rear. The glyph box is a little wider than before because the new digits contain fewer narrow '1's."""
    rgb = np.asarray(img.convert("RGB")).copy()
    quad = [(949.3, 429.3), (1082.0, 423.2), (1082.0, 459.9), (949.3, 469.0)]
    rgb = replace_text(rgb, (947, 418, 1084, 476), quad, "663-0186", "bebas-neue", "400", light_text=False, size_hint=40, blur=0.35, thresh=16, grow=3, embolden=0.45, margin=0)
    return Image.fromarray(rgb)


def retouch_unloading(img: Image.Image) -> Image.Image:
    """Technician photo: white 'Phone: (716) 610-1160' on the blue van panel; only '610-1160' changes."""
    rgb = np.asarray(img.convert("RGB")).copy()
    quad = [(600.0, 359.5), (743.0, 356.4), (743.0, 397.6), (600.0, 396.5)]
    rgb = replace_text(rgb, (597, 351, 742, 403), quad, "663-0186", "roboto-condensed", "700", light_text=True, size_hint=40, blur=0.45,
                       thresh=34, grow=3, embolden=0.0, margin=0)
    return Image.fromarray(rgb)


def retouch_business(img: Image.Image) -> Image.Image:
    """Shop photo: (1) the tilted sign 'BUFFALO PLUMBING PROS (716) 610-1160' and (2) the van's number, mostly hidden behind a
    worker — only '(716)' and the tail '160' are visible, so '(716)' stays and the tail becomes '186'."""
    rgb = np.asarray(img.convert("RGB")).copy()
    # (1) sign: '610-1160' rises ~6° to the right; Montserrat Bold matches the geometric digits
    quad = [(686.3, 151.0), (772.0, 141.6), (772.0, 160.0), (686.3, 169.2)]
    band = polygon_mask(rgb.shape[:2], [(quad[0][0] - 2, quad[0][1] - 4), (quad[1][0] + 3, quad[1][1] - 4), (quad[2][0] + 3, quad[2][1] + 4), (quad[3][0] - 2, quad[3][1] + 4)])
    rgb = replace_text(rgb, (684, 141, 775, 174), quad, "663-0186", "montserrat", "700", light_text=False, size_hint=40, blur=0.5,
                       thresh=22, grow=2, margin=0, within=band)
    # (2) van: erase/draw only to the right of the worker's silhouette
    worker = polygon_mask(rgb.shape[:2], [(840, 360), (890, 360), (890.5, 386), (894.2, 404), (896.5, 418), (898.5, 428), (840, 428)])
    quad2 = [(891.0, 385.6), (929.6, 385.6), (929.6, 406.8), (891.0, 406.8)]
    rgb = replace_text(rgb, (886, 378, 934, 412), quad2, "186", "montserrat", "700", light_text=False, size_hint=40, blur=0.5,
                       thresh=22, grow=2, margin=0, keep_out=worker)
    return Image.fromarray(rgb)


def retouch_van_2(img: Image.Image) -> Image.Image:
    """Street van: (1) side band, white '(716) 610-1160' on blue — '610-1160' becomes '663-0186';
    (2) rear door, '(716) 610-' leaning with the door's perspective and cut off by the dark gap — '610-' becomes '663-'
    (the sliver of the next digit that peeked out is simply erased)."""
    rgb = np.asarray(img.convert("RGB")).copy()
    quad = [(519.8, 417.6), (587.0, 417.6), (587.0, 436.4), (519.8, 436.4)]
    rgb = replace_text(rgb, (517, 412, 590, 442), quad, "663-0186", "roboto-condensed", "700", light_text=True, size_hint=40, blur=0.75,
                       thresh=34, grow=3, margin=0)
    dark_gap = polygon_mask(rgb.shape[:2], [(1003.0, 385), (1022, 385), (1022, 450), (1000.5, 450)])
    quad2 = [(965.5, 403.0), (1002.0, 403.0), (999.3, 428.7), (962.8, 428.7)]
    rgb = replace_text(rgb, (961, 396, 1006, 436), quad2, "663-", "roboto-condensed", "700", light_text=True, size_hint=40, blur=0.75,
                       thresh=20, grow=3, margin=0, keep_out=dark_gap)
    return Image.fromarray(rgb)


# name of the slot -> recipe. Photos take/return an RGB image, badges an RGBA image.
PHOTO_RECIPES = {
    "van-1": retouch_van_1,
    "van-2": retouch_van_2,
    "technician-unloading": retouch_unloading,
    "business-exterior": retouch_business,
}
BADGE_RECIPES = {
    "badge-emergency": retouch_badge_emergency,
    "badge-shield": retouch_badge_shield,
}
