#!/usr/bin/env python3
"""Extract page content from the legacy static site into Astro content-collection JSON.

The legacy site (the `main` branch) is hand-rolled HTML + Tailwind CDN. Every page follows one of
five templates (home, service, service-area, blog post, blog index). This script parses each page
with a real HTML parser and writes the *copy* — titles, meta descriptions, headings, prose, FAQs,
steps, benefits — to `src/content/**` so the Astro templates render exactly the same words on
exactly the same URLs. Nothing is retyped by hand.

Usage:
    git archive main | tar -x -C /tmp/legacy
    python3 -I scripts/extract_legacy_content.py /tmp/legacy src/content

Any page that does not match its template fails loudly instead of being silently skipped.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, Comment

SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("legacy")
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("src/content")


# --------------------------------------------------------------------------- helpers
def soup_of(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf8"), "lxml")


def txt(el) -> str:
    """Visible text with whitespace collapsed (emoji/icon-only nodes drop out)."""
    if el is None:
        return ""
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()


def strip_emoji(s: str) -> str:
    """Leading decorative emoji/symbols are replaced by SVG icons in the new design."""
    return re.sub(r"^[^\w\"'(]+", "", s).strip()


def inner_html(el) -> str:
    html = el.decode_contents()
    html = re.sub(r"\s+\n", "\n", html).strip()
    return html


def meta(soup: BeautifulSoup, name: str) -> str | None:
    tag = soup.find("meta", attrs={"name": name}) or soup.find("meta", attrs={"property": name})
    return tag["content"].strip() if tag and tag.get("content") else None


def must(value, what: str, page: Path):
    if not value:
        raise SystemExit(f"[template mismatch] {page}: missing {what}")
    return value


def section_after_header(soup: BeautifulSoup):
    """Top-level <section> elements in the <body> (comments excluded)."""
    return [s for s in soup.body.find_all("section", recursive=False)]


def write_json(rel: str, data: dict) -> None:
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf8")


def remove_comments(root) -> None:
    for c in root.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()


# --------------------------------------------------------------------------- nav (single source of truth)
def extract_nav(home: BeautifulSoup):
    """Service + area lists (names/slugs, in the original menu order) from the homepage header."""
    services, areas = [], []
    for a in home.select("header .group a[href^='/services/']"):
        services.append({"slug": a["href"].split("/")[-1], "name": txt(a)})
    for a in home.select("header .group a[href^='/service-area/']"):
        areas.append({"slug": a["href"].split("/")[-1], "name": txt(a)})
    assert len(services) == 18, len(services)
    assert len(areas) == 15, len(areas)
    return services, areas


# --------------------------------------------------------------------------- service pages
def extract_service(path: Path, name: str, card_text: str) -> dict:
    s = soup_of(path)
    remove_comments(s)
    secs = section_after_header(s)
    assert len(secs) == 4, (path, len(secs))
    hero, details, faq, areas = secs

    h1 = must(txt(hero.h1), "h1", path)
    hero_p = must(txt(hero.find("p")), "hero p", path)

    prose = must(details.select_one("div.prose"), "prose", path)
    main_col = details.select_one("div.lg\\:col-span-2")
    blocks = [d for d in main_col.find_all("div", recursive=False)]
    # blocks[0] = prose, blocks[1] = benefits, blocks[2] = process
    benefits_block, process_block = blocks[1], blocks[2]
    benefits_heading = txt(benefits_block.h2)
    benefits = [txt(h) for h in benefits_block.find_all("h4")]
    process_heading = txt(process_block.h2)
    process = [txt(h) for h in process_block.find_all("h4")]

    side = details.select_one("div.lg\\:col-span-1")
    cta_card = side.select_one("div.bg-gradient-to-br")
    cta_h = txt(cta_card.h3)
    cta_p = txt(cta_card.find("p"))
    cta_btn = strip_emoji(txt(cta_card.find("a")))

    faqs = []
    for card in faq.select("div.border-l-4"):
        faqs.append({"q": txt(card.h4), "a": txt(card.find("p"))})
    faq_heading = txt(faq.h2)
    more_p = txt(faq.select_one("div.text-center p"))
    more_btn = strip_emoji(txt(faq.select_one("div.text-center a")))

    area_h2 = txt(areas.h2)
    area_sub = txt(areas.select_one("div.text-center p"))

    return {
        "name": name,
        "title": must(txt(s.title), "title", path),
        "description": must(meta(s, "description"), "description", path),
        "h1": h1,
        "heroText": hero_p,
        "heroButton": strip_emoji(txt(hero.find("a"))),
        "bodyHtml": inner_html(prose),
        "benefitsHeading": benefits_heading,
        "benefits": benefits,
        "processHeading": process_heading,
        "process": process,
        "sidebarCta": {"heading": cta_h, "text": cta_p, "button": cta_btn},
        "faqHeading": faq_heading,
        "faqs": faqs,
        "faqFooter": {"text": more_p, "button": more_btn},
        "areasHeading": area_h2,
        "areasSubheading": area_sub,
        "cardText": card_text,
    }


# --------------------------------------------------------------------------- area pages
def extract_area(path: Path, name: str) -> dict:
    s = soup_of(path)
    remove_comments(s)
    secs = section_after_header(s)
    assert len(secs) == 3, (path, len(secs))
    hero, details, mapsec = secs

    prose = must(details.select_one("div.prose"), "prose", path)
    main_col = details.select_one("div.lg\\:col-span-2")
    blocks = main_col.find_all("div", recursive=False)
    # prose, why-choose, coverage
    why_block, coverage_block = blocks[1], blocks[2]
    why_heading = txt(why_block.h2)
    why_items = []
    for card in why_block.select("div.border-l-4"):
        why_items.append({"title": txt(card.h4), "text": txt(card.find("p"))})
    coverage = {"heading": txt(coverage_block.h3), "text": txt(coverage_block.find("p"))}

    side = details.select_one("div.lg\\:col-span-1")
    cta_card = side.select_one("div.bg-gradient-to-br")
    info_card = side.select_one("div.bg-white")
    info_rows = []
    for row in info_card.select("div.justify-between"):
        spans = row.find_all("span")
        info_rows.append({"label": txt(spans[0]).rstrip(":"), "value": txt(spans[1])})
    zipcode = next(r["value"] for r in info_rows if r["label"].lower().startswith("zip"))
    services_heading = txt(info_card.select_one("h4"))
    info_heading = txt(info_card.h3)

    # map section: location contact card + hand-picked "Nearby Areas We Serve" list
    map_cards = mapsec.select("div.space-y-6 > div.bg-white")
    contact_card, nearby_card = map_cards[0], map_cards[1]
    cps = [txt(x) for x in contact_card.find_all("p")]
    nearby_links = []
    for a in nearby_card.select("div.space-y-2 a"):
        nearby_links.append({"slug": a["href"].rstrip("/").split("/")[-1], "name": txt(a)})
    view_all = nearby_card.select_one("div.border-t a")

    return {
        "name": name,
        "zip": zipcode,
        "title": must(txt(s.title), "title", path),
        "description": must(meta(s, "description"), "description", path),
        "h1": must(txt(hero.h1), "h1", path),
        "heroText": txt(hero.find("p")),
        "heroButton": strip_emoji(txt(hero.find("a"))),
        "bodyHtml": inner_html(prose),
        "whyHeading": why_heading,
        "whyItems": why_items,
        "coverage": coverage,
        "sidebarCta": {
            "heading": txt(cta_card.h3),
            "text": txt(cta_card.find("p")),
            "button": strip_emoji(txt(cta_card.find("a"))),
        },
        "infoHeading": info_heading,
        "infoRows": info_rows,
        "servicesHeading": services_heading,
        "mapHeading": txt(mapsec.h2),
        "mapSubheading": txt(mapsec.select_one("div.text-center p")),
        "mapContact": {
            "heading": txt(contact_card.h3),
            "businessName": cps[0],
            "serving": cps[1],
            "zipLine": cps[2],
            "hoursLabel": cps[3],
            "hoursValue": cps[4],
        },
        "nearby": {
            "heading": txt(nearby_card.h3),
            "links": nearby_links,
            "viewAll": {"label": txt(view_all), "href": view_all["href"]},
        },
    }


# --------------------------------------------------------------------------- blog
def extract_post(path: Path) -> dict:
    s = soup_of(path)
    remove_comments(s)
    art = must(s.select_one("main article"), "article", path)
    head = art.find("header")
    h1 = must(txt(head.h1), "h1", path)
    byline = head.select_one("div.flex")
    spans = byline.find_all("span")
    author, date_text = txt(spans[0]), txt(spans[1])
    summary = txt(head.select_one("div.italic"))
    prose = must(art.select_one("div.prose"), "prose", path)

    # A few legacy posts repeat the page H1 as the first heading of the body. Same words, same
    # place, one level of heading too many — drop the exact duplicate, keep everything else.
    for dup in prose.find_all("h1"):
        if txt(dup) == h1:
            dup.decompose()
        else:
            dup.name = "h2"

    cta = art.select_one("div.bg-blue-50")
    ld = [json.loads(t.string) for t in s.find_all("script", type="application/ld+json")]
    blog_ld = next(x for x in ld if x.get("@type") == "BlogPosting")
    return {
        "title": txt(s.title),
        "description": must(meta(s, "description"), "description", path),
        "keywords": meta(s, "keywords"),
        "h1": h1,
        "author": author,
        "dateText": date_text,
        "datePublished": blog_ld["datePublished"],
        "dateModified": blog_ld.get("dateModified", blog_ld["datePublished"]),
        "summary": summary,
        "bodyHtml": inner_html(prose),
        "cta": {
            "heading": txt(cta.h3),
            "text": txt(cta.find("p")),
            "button": strip_emoji(txt(cta.find("a"))),
        },
    }


def extract_blog_index(path: Path, posts: dict) -> dict:
    s = soup_of(path)
    remove_comments(s)
    main = s.select_one("main")
    hdr = main.find("header")
    items = []
    for art in main.select("article"):
        a = art.select_one("h2 a")
        slug = a["href"].rstrip("/").split("/")[-1]
        items.append(
            {
                "slug": slug,
                "title": txt(a),
                "byline": txt(art.select_one("div.text-sm")),
                "excerpt": txt(art.select_one("p")),
            }
        )
        assert slug in posts, slug
    cta = main.select_one("div.bg-blue-50")
    return {
        "title": txt(s.title),
        "description": must(meta(s, "description"), "description", path),
        "h1": txt(hdr.h1),
        "intro": txt(hdr.find("p")),
        "items": items,
        "cta": {
            "heading": txt(cta.h3),
            "text": txt(cta.find("p")),
            "button": strip_emoji(txt(cta.find("a"))),
        },
    }


# --------------------------------------------------------------------------- home
def extract_home(path: Path) -> dict:
    s = soup_of(path)
    remove_comments(s)  # drops the commented-out reviews block
    secs = section_after_header(s)
    by_id = {sec.get("id"): sec for sec in secs if sec.get("id")}
    plain = [sec for sec in secs if not sec.get("id")]

    # ---- hero (#home)
    hero = by_id["home"]
    hero_cards = []
    for card in hero.select("div.border-t-4"):
        hero_cards.append({"title": txt(card.h3), "text": txt(card.find("p")), "slug": card.find("a")["href"].split("/")[-1]})
    stats_box = hero.select_one("div.border-l-4")
    hero_stats = [{"value": txt(d.select_one("div.text-3xl")), "label": txt(d.select_one("div.text-gray-600"))} for d in stats_box.select("div.grid > div")]

    # ---- about
    about = by_id["about"]
    about_prose = about.select_one("div.prose")
    about_stats = [{"value": txt(d.select_one("div.text-3xl")), "label": txt(d.select_one("div.font-medium"))} for d in about.select("div.border-l-4")]
    about_img = about.find("img")

    # ---- services (#services)
    services = by_id["services"]
    services_heading = txt(services.h2)
    services_sub = txt(services.select_one("div.text-center p"))
    service_cards = []
    for card in services.select("div.group"):
        service_cards.append({"title": txt(card.h3), "text": txt(card.find("p")), "slug": card.find("a")["href"].split("/")[-1]})

    # ---- plain sections in order: why, find-us, nationwide
    why, find_us, nationwide = plain
    why_items = [{"title": txt(d.h3), "text": txt(d.find("p"))} for d in why.select("div.border-l-4")]

    contact_card = find_us.select_one("div.shadow-lg.p-6")
    emergency_card = find_us.select_one("div.text-white.shadow-lg")

    states = [{"name": txt(a), "url": a["href"]} for a in nationwide.select("a[href^='https://']")]
    nat_items = [{"title": txt(d.h4), "text": txt(d.find("p"))} for d in nationwide.select("div.space-y-4 > div")]

    # ---- contact (#contact)
    contact = by_id["contact"]
    hours = contact.find("h3", string=re.compile("Hours")).find_next("p")
    hours_lines = [t.strip() for t in hours.stripped_strings]

    return {
        "title": txt(s.title),
        "description": meta(s, "description"),
        "keywords": meta(s, "keywords"),
        "hero": {
            "badge": strip_emoji(txt(hero.select_one("div.rounded-full"))),
            "h1": txt(hero.h1),
            "text": txt(hero.select_one("div.text-center > p")),
            "button": strip_emoji(txt(hero.select_one("div.text-center > a"))),
            "cards": hero_cards,
            "stats": hero_stats,
        },
        "about": {
            "heading": txt(about.h2),
            "bodyHtml": inner_html(about_prose),
            "stats": about_stats,
            "imageAlt": about_img["alt"],
            "badge": txt(about.select_one("span.font-semibold")),
            "badgeSub": txt(about.select_one("p.text-sm")),
        },
        "services": {"heading": services_heading, "subheading": services_sub, "cards": service_cards},
        "why": {
            "badge": strip_emoji(txt(why.select_one("div.rounded-full"))),
            "heading": txt(why.h2),
            "text": txt(why.select_one("div.text-center > p")),
            "items": why_items,
        },
        "findUs": {
            "heading": txt(find_us.h2),
            "subheading": txt(find_us.select_one("div.text-center > p")),
            "contactHeading": txt(contact_card.h3),
            "businessName": txt(contact_card.select_one("p.font-semibold")),
            "serving": txt(contact_card.select_one("p.text-gray-600")),
            "hoursLabel": "Business Hours",
            "hoursValue": txt(contact_card.find_all("p", class_="text-gray-600")[-1]),
            "emergencyHeading": txt(emergency_card.h3),
            "emergencyText": txt(emergency_card.find("p")),
            "emergencyButton": strip_emoji(txt(emergency_card.find("a"))),
        },
        "nationwide": {
            "badge": txt(nationwide.select_one("div.rounded-full")),
            "heading": txt(nationwide.h2),
            "text": txt(nationwide.select_one("div.text-center > p")),
            "whyHeading": txt(nationwide.select_one("h3.text-2xl.font-bold.mb-6")),
            "items": nat_items,
            "statesHeading": txt(nationwide.select_one("div.mt-16 h3")),
            "states": states,
        },
        "contact": {
            "heading": txt(contact.h2),
            "text": txt(contact.select_one("p.text-xl")),
            "hours": hours_lines,
            "formHeading": txt(contact.select_one("h3.text-2xl")),
            "formText": txt(contact.select_one("div.text-center p")),
            "formButton": strip_emoji(txt(contact.select_one("div.text-center a"))),
        },
    }


# --------------------------------------------------------------------------- main
def main() -> None:
    home = soup_of(SRC / "index.html")
    services_nav, areas_nav = extract_nav(home)
    home_data = extract_home(SRC / "index.html")
    card_text = {c["slug"]: c["text"] for c in home_data["services"]["cards"]}

    write_json("pages/home.json", home_data)

    for sv in services_nav:
        data = extract_service(SRC / "services" / f"{sv['slug']}.html", sv["name"], card_text[sv["slug"]])
        write_json(f"services/{sv['slug']}.json", data)

    for ar in areas_nav:
        data = extract_area(SRC / "service-area" / f"{ar['slug']}.html", ar["name"])
        write_json(f"areas/{ar['slug']}.json", data)

    posts = {}
    for p in sorted((SRC / "blog").glob("*.html")):
        if p.name == "index.html":
            continue
        data = extract_post(p)
        posts[p.stem] = data
        write_json(f"blog/{p.stem}.json", data)

    write_json("pages/blog-index.json", extract_blog_index(SRC / "blog" / "index.html", posts))

    # Order of menus/cards as they appeared on the legacy site.
    write_json("pages/nav.json", {"services": services_nav, "areas": areas_nav})
    print(f"wrote {len(services_nav)} services, {len(areas_nav)} areas, {len(posts)} posts, home, blog index, nav")


if __name__ == "__main__":
    main()
