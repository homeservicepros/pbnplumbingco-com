#!/usr/bin/env python3
"""Prove the Astro build is a faithful migration of the legacy site.

    git archive main | tar -x -C /tmp/legacy
    npm run build
    python3 -I scripts/verify_parity.py /tmp/legacy dist

Checks (exit code 1 if any hard check fails):
  1. URL parity      – every legacy page exists at the same extensionless URL; sitemap lists all 45.
  2. Metadata parity – <title> and meta description identical to legacy on every page.
  3. Copy parity     – every text node of legacy page *content* (chrome excluded) appears in the new page.
  4. Link integrity  – every internal href / src in the new build resolves to a built file.
  5. SEO hygiene     – one <h1>, canonical on the new domain, valid JSON-LD, images have alt.
  6. Domain move     – no trace of the old domain anywhere in dist; every page links all state sub-domains.

Owner-approved differences from the legacy copy (applied to the legacy text before comparing):
  contact@pbmplumbingco.com → info@buffaloplumbingpros.com · pbmplumbingco.com → buffaloplumbingpros.com · ZIP 14086 → 14228
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup, Comment

LEGACY = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/legacy")
DIST = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("dist")
NEW_ORIGIN = "https://buffaloplumbingpros.com"
OLD_DOMAIN = "pbmplumbingco.com"

REPLACEMENTS = [
    ("contact@pbmplumbingco.com", "info@buffaloplumbingpros.com"),
    ("pbmplumbingco.com", "buffaloplumbingpros.com"),
    ("14086", "14228"),
]
STATE_CODES = (
    "al ak az ar ca co ct de dc fl ga hi id il in ia ks ky la me md ma mi mn ms mo mt ne nv nh nj nm ny nc nd oh ok or pa pr ri sc sd tn tx ut vt va wa wv wi wy"
).split()


def migrated(text: str) -> str:
    for a, b in REPLACEMENTS:
        text = text.replace(a, b)
    return text


failures: list[str] = []
notes: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def norm(s: str) -> str:
    s = s.replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip()


def url_of(rel: Path) -> str:
    """legacy/dist file path → public URL path as Cloudflare Pages serves it."""
    p = "/" + rel.as_posix()
    if p.endswith("/index.html"):
        p = p[: -len("index.html")]
    elif p.endswith(".html"):
        p = p[: -len(".html")]
    return p


def load(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf8"), "lxml")


legacy_pages = {url_of(p.relative_to(LEGACY)): p for p in LEGACY.rglob("*.html")}
dist_pages = {url_of(p.relative_to(DIST)): p for p in DIST.rglob("*.html") if p.name != "404.html"}

# ------------------------------------------------------------------ 1. URL parity
missing = sorted(set(legacy_pages) - set(dist_pages))
extra = sorted(set(dist_pages) - set(legacy_pages))
for u in missing:
    fail(f"URL missing in new build: {u}")
for u in extra:
    fail(f"unexpected extra URL in new build: {u}")
print(f"[1] URL parity: {len(legacy_pages)} legacy pages / {len(dist_pages)} new pages  → {'OK' if not missing and not extra else 'MISMATCH'}")

sitemap = (DIST / "sitemap.xml").read_text(encoding="utf8")
sm_urls = set(re.findall(r"<loc>([^<]+)</loc>", sitemap))
expected_sm = {NEW_ORIGIN + u for u in legacy_pages}
if sm_urls != expected_sm:
    for u in sorted(expected_sm - sm_urls):
        fail(f"sitemap.xml missing {u}")
    for u in sorted(sm_urls - expected_sm):
        fail(f"sitemap.xml has unexpected {u}")
print(f"    sitemap.xml lists {len(sm_urls)} URLs (expected {len(expected_sm)}) → {'OK' if sm_urls == expected_sm else 'MISMATCH'}")

# ------------------------------------------------------------------ 2. metadata parity
def meta_desc(soup: BeautifulSoup) -> str | None:
    t = soup.find("meta", attrs={"name": "description"})
    return norm(t["content"]) if t and t.get("content") else None


meta_bad = 0
for u, lp in legacy_pages.items():
    if u not in dist_pages:
        continue
    ls, ns = load(lp), load(dist_pages[u])
    lt, nt = norm(migrated(ls.title.get_text())), norm(ns.title.get_text())
    if lt != nt:
        meta_bad += 1
        fail(f"title differs on {u}\n    old: {lt}\n    new: {nt}")
    ld, nd = (migrated(meta_desc(ls)) if meta_desc(ls) else None), meta_desc(ns)
    if ld != nd:
        meta_bad += 1
        fail(f"meta description differs on {u}\n    old: {ld}\n    new: {nd}")
print(f"[2] Metadata parity (title + description, {len(legacy_pages)} pages) → {'OK' if not meta_bad else f'{meta_bad} differences'}")

# ------------------------------------------------------------------ 3. copy parity
CHROME_SELECTORS = [
    "header", "footer", "nav", "script", "style", "noscript", "iframe", "svg", ".mobile-menu", ".floating-phone", "link", "meta",
]


def content_nodes(soup: BeautifulSoup) -> list[str]:
    body = soup.body
    for c in body.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    for sel in CHROME_SELECTORS:
        for el in body.select(sel):
            el.decompose()
    # legacy top bar (e-mail / location strip) is a bare <div> before <header>; it has no header/nav wrapper
    for div in body.find_all("div", class_=lambda c: c and "bg-gray-900" in c and "text-sm" in c):
        div.decompose()
    out = []
    for s in body.find_all(string=True):
        t = norm(migrated(str(s)))
        if not t or not re.search(r"[A-Za-z0-9]", t):  # decorative glyphs/emoji/arrows
            continue
        t = re.sub(r"^[^\w\"'($]+", "", t)
        t = re.sub(r"[\s\u2190-\u21ff\u27a0-\u27bf]+$", "", t)  # trailing → arrows are icons now
        out.append(t.strip())
    return out


def visible_text(soup: BeautifulSoup) -> str:
    body = soup.body
    for sel in ("script", "style", "noscript"):
        for el in body.select(sel):
            el.decompose()
    return norm(body.get_text(" "))


total_nodes = missing_nodes = 0
per_page_missing: dict[str, list[str]] = {}
for u, lp in sorted(legacy_pages.items()):
    if u not in dist_pages:
        continue
    nodes = content_nodes(load(lp))
    new_text = visible_text(load(dist_pages[u]))
    miss = [n for n in nodes if n not in new_text]
    total_nodes += len(nodes)
    missing_nodes += len(miss)
    if miss:
        per_page_missing[u] = miss
print(f"[3] Copy parity: {total_nodes - missing_nodes}/{total_nodes} legacy content text nodes found verbatim in the new pages")
for u, miss in per_page_missing.items():
    for m in miss[:6]:
        print(f"    MISSING on {u}: {m[:140]!r}")
    if len(miss) > 6:
        print(f"    … and {len(miss) - 6} more on {u}")
    fail(f"{len(miss)} legacy text nodes not found on {u}")

# ------------------------------------------------------------------ 4. link integrity
def resolves(href: str, page_url: str) -> bool:
    href = href.split("#")[0].split("?")[0]
    if not href:
        return True
    if href.startswith("/"):
        path = href
    else:
        base = page_url if page_url.endswith("/") else page_url.rsplit("/", 1)[0] + "/"
        path = urlparse(base + href).path
    path = unquote(path)
    if path in dist_pages or path + "/" in dist_pages:
        return True
    f = DIST / path.lstrip("/")
    return f.is_file() or (f.with_suffix(".html")).is_file()


broken = []
checked = 0
for u, p in dist_pages.items():
    soup = load(p)
    for el in soup.find_all(["a", "img", "link", "source", "script"]):
        for attr in ("href", "src", "srcset"):
            val = el.get(attr)
            if not val:
                continue
            candidates = [v.strip().split(" ")[0] for v in val.split(",")] if attr == "srcset" else [val]
            for href in candidates:
                if re.match(r"^(https?:|mailto:|tel:|data:|javascript:|//)", href):
                    continue
                checked += 1
                if not resolves(href, u):
                    broken.append((u, href))
for u, h in broken[:20]:
    print(f"    BROKEN on {u}: {h}")
    fail(f"broken internal reference on {u}: {h}")
print(f"[4] Link integrity: {checked} internal references checked → {'OK' if not broken else f'{len(broken)} broken'}")

# ------------------------------------------------------------------ 5. SEO hygiene
seo_bad = 0
old_domain_hits: dict[str, int] = {}
for u, p in sorted(dist_pages.items()):
    soup = load(p)
    h1s = soup.find_all("h1")
    if len(h1s) != 1:
        seo_bad += 1
        fail(f"{u}: {len(h1s)} <h1> elements")
    canon = soup.find("link", rel="canonical")
    expected = NEW_ORIGIN + u
    if not canon or canon.get("href") != expected:
        seo_bad += 1
        fail(f"{u}: canonical is {canon.get('href') if canon else None}, expected {expected}")
    blocks = soup.find_all("script", type="application/ld+json")
    if not blocks:
        seo_bad += 1
        fail(f"{u}: no JSON-LD")
    for b in blocks:
        try:
            json.loads(b.string)
        except Exception as e:  # noqa: BLE001
            seo_bad += 1
            fail(f"{u}: invalid JSON-LD ({e})")
    for img in soup.find_all("img"):
        if img.get("alt") is None:
            seo_bad += 1
            fail(f"{u}: <img> without alt: {str(img)[:100]}")
    if not soup.find("meta", attrs={"property": "og:image"}):
        seo_bad += 1
        fail(f"{u}: missing og:image")
    for s in soup.find_all("script", type="application/ld+json"):
        if OLD_DOMAIN in (s.string or ""):
            seo_bad += 1
            fail(f"{u}: JSON-LD still mentions {OLD_DOMAIN}")
print(f"[5] SEO hygiene on {len(dist_pages)} pages (1×h1, canonical, JSON-LD, alt, og:image) → {'OK' if not seo_bad else f'{seo_bad} issues'}")

# ------------------------------------------------------------------ 6. domain move
leaks = []
for f in DIST.rglob("*"):
    if f.is_file() and f.suffix in {".html", ".xml", ".txt", ".json", ".webmanifest", ".js", ".css"}:
        if OLD_DOMAIN in f.read_text(encoding="utf8", errors="ignore"):
            leaks.append(f.relative_to(DIST).as_posix())
for f in leaks:
    fail(f"old domain {OLD_DOMAIN} still referenced in dist/{f}")
state_pat = re.compile(r"^https://([a-z]{2})\.buffaloplumbingpros\.com/$")
state_bad = 0
for u, p in sorted(dist_pages.items()):
    codes = {m.group(1) for a in load(p).find_all("a", href=True) if (m := state_pat.match(a["href"]))}
    if codes != set(STATE_CODES):
        state_bad += 1
        fail(f"{u}: state links differ — missing {sorted(set(STATE_CODES) - codes)} extra {sorted(codes - set(STATE_CODES))}")
home = load(dist_pages["/"])
tiles = [a for a in home.select("#states ul[aria-label='Map of states we serve'] a")]
if len(tiles) != len(STATE_CODES):
    fail(f"homepage tile map has {len(tiles)} tiles, expected {len(STATE_CODES)}")
print(f"[6] Domain move: old domain mentioned in {len(leaks)} dist files; all {len(STATE_CODES)} state sub-domain links present on "
      f"{len(dist_pages) - state_bad}/{len(dist_pages)} pages; homepage map has {len(tiles)} tiles → "
      f"{'OK' if not leaks and not state_bad and len(tiles) == len(STATE_CODES) else 'PROBLEMS'}")

# ------------------------------------------------------------------ result
print()
if failures:
    print(f"FAILED — {len(failures)} problem(s):")
    for f in failures[:40]:
        print("  •", f)
    sys.exit(1)
print("ALL CHECKS PASSED")
