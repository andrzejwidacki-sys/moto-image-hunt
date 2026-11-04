"""Wikimedia Commons via the MediaWiki Action API (no key needed).

Three routes, so files are found even when their *name* says nothing about the model:
  1. discover categories whose name matches the target and walk them recursively;
  2. full-text search of the File: namespace (title + description + categories) per query;
  3. every file's real categories are fetched and used for model matching.
"""
from __future__ import annotations

import re
from collections import deque
from typing import Iterator

from ..http import HttpError
from ..models import CHECK, OK, Item, judge_license, normalise
from .base import Ctx, strip_html

NAME = "commons"
ENV: list[str] = []
API = "https://commons.wikimedia.org/w/api.php"
WIKIDATA = "https://www.wikidata.org/w/api.php"
BASE = {"action": "query", "format": "json", "formatversion": "2"}
IMAGEINFO = {
    "prop": "imageinfo|categories",
    "iiprop": "url|size|mime|extmetadata",
    "iiurlwidth": "960",
    "iiextmetadatafilter": "LicenseShortName|LicenseUrl|UsageTerms|Artist|Credit|ImageDescription"
                           "|AttributionRequired|Copyrighted",
    "cllimit": "max",
    "clshow": "!hidden",
}
MAX_CATEGORIES = 150


def _collect(ctx: Ctx, params: dict, limit: int | None = None) -> list[dict]:
    """Run a query and follow `continue`, merging batches that repeat the same page."""
    pages: dict = {}
    cont: dict = {}
    while True:
        data = ctx.http.get_json(API, params={**BASE, **params, **cont})
        for p in (data.get("query") or {}).get("pages", []):
            if p.get("missing"):
                continue
            merged = pages.setdefault(p.get("pageid", p["title"]),
                                      {"title": p["title"], "imageinfo": None, "categories": []})
            if p.get("imageinfo") and not merged["imageinfo"]:
                merged["imageinfo"] = p["imageinfo"]
            for c in p.get("categories") or []:
                if c["title"] not in merged["categories"]:
                    merged["categories"].append(c["title"])
        cont = data.get("continue")
        if not cont or (limit and len(pages) >= limit):
            break
    return list(pages.values())


def to_item(page: dict, query: str, include_video: bool) -> Item | None:
    infos = page.get("imageinfo") or []
    if not infos:
        return None
    ii = infos[0]
    mime = ii.get("mime", "")
    if mime.startswith("image/"):
        kind = "image"
    elif mime.startswith("video/") or mime == "application/ogg":
        kind = "video"
        if not include_video:
            return None
    else:
        return None
    em = ii.get("extmetadata") or {}

    def ev(key: str) -> str:
        return strip_html((em.get(key) or {}).get("value") or "")

    raw_license = ev("LicenseShortName") or ev("UsageTerms")
    if not raw_license and ev("Copyrighted").lower() == "false":
        raw_license = "Public domain"
    # Commons only hosts free content, so an unreadable licence name is "check", not "no".
    label, verdict, attribution, note = judge_license(raw_license, unknown=CHECK)
    if ev("AttributionRequired").lower() == "true":
        attribution = True
    title = re.sub(r"^File:", "", page["title"])
    page_url = ii.get("descriptionurl") or "https://commons.wikimedia.org/wiki/" + page["title"].replace(" ", "_")
    return Item(
        source="commons", kind=kind, id=page["title"], title=title, page_url=page_url,
        file_url=ii.get("url", ""), thumb_url=ii.get("thumburl") or ii.get("url", ""),
        creator=ev("Artist") or ev("Credit"), license=label, license_url=ev("LicenseUrl"),
        verdict=verdict, attribution_required=attribution, description=ev("ImageDescription"),
        categories=[c.removeprefix("Category:") for c in page["categories"]],
        width=ii.get("width") or 0, height=ii.get("height") or 0, note=note, query=query,
    )


def _wikidata(ctx: Ctx, specs: list[dict]) -> dict[str, dict]:
    """Look up label + Commons category (P373) of the configured Wikidata items.

    An item is only trusted (`ok`) when its English label matches the spec's `label` regex, so a wrong
    Q-number in targets.yml can never silently tag unrelated photos."""
    data = ctx.http.get_json(WIKIDATA, params={
        "action": "wbgetentities", "ids": "|".join(s["id"] for s in specs),
        "props": "labels|claims", "languages": "en", "format": "json"})
    out: dict[str, dict] = {}
    for s in specs:
        ent = (data.get("entities") or {}).get(s["id"]) or {}
        label = ((ent.get("labels") or {}).get("en") or {}).get("value", "")
        cats = [c["mainsnak"]["datavalue"]["value"] for c in (ent.get("claims") or {}).get("P373", [])
                if (c.get("mainsnak") or {}).get("datavalue")]
        ok = bool(re.search(s["label"], label, re.I)) if s.get("label") else bool(label)
        out[s["id"]] = {"label": label, "categories": cats, "ok": ok}
    return out


def _discover_categories(ctx: Ctx) -> list[str]:
    pattern = ctx.target.get("commons_category_filter")
    found: list[str] = []
    for phrase in ctx.target.get("commons_category_search", []):
        data = ctx.http.get_json(API, params={**BASE, "list": "search", "srsearch": phrase,
                                              "srnamespace": "14", "srlimit": "50"})
        for hit in (data.get("query") or {}).get("search", []):
            title = hit["title"]
            if title not in found and (not pattern or re.search(pattern, normalise(title))):
                found.append(title)
    return found


def _walk(ctx: Ctx, roots: list[str], depth: int) -> tuple[dict[str, str], list[str]]:
    """Breadth-first walk. Returns ({file title: category it was found in}, categories visited)."""
    seen: list[str] = []
    files: dict[str, str] = {}
    queue = deque((r, 0) for r in roots)
    while queue and len(seen) < MAX_CATEGORIES:
        cat, d = queue.popleft()
        if cat in seen:
            continue
        seen.append(cat)
        cont: dict = {}
        while True:
            data = ctx.http.get_json(API, params={**BASE, "list": "categorymembers", "cmtitle": cat,
                                                  "cmtype": "file|subcat", "cmlimit": "500", **cont})
            for m in (data.get("query") or {}).get("categorymembers", []):
                if m["ns"] == 14 and d < depth:
                    queue.append((m["title"], d + 1))
                elif m["ns"] == 6:
                    files.setdefault(m["title"], cat)
            cont = data.get("continue")
            if not cont:
                break
    return files, seen


def search(ctx: Ctx) -> Iterator[Item]:
    seen_titles: set[str] = set()
    depicts: dict[str, set[str]] = {}  # Wikidata id -> titles of files whose structured data says "depicts <id>"

    def emit(item: Item | None, source_query: str = "") -> Item | None:
        if item is None or item.id in seen_titles:
            return None
        seen_titles.add(item.id)
        item.tags += [f"depicts:{q}" for q, titles in depicts.items() if item.id in titles]
        return item

    # Route 0: structured data ("depicts" statements) - finds files whatever their file name is
    specs = ctx.target.get("commons_depicts", [])
    extra_roots: list[str] = []
    if specs:
        try:
            info = _wikidata(ctx, specs)
        except HttpError as exc:
            info = {}
            ctx.notes.append(f"Commons: nie udało się odpytać Wikidata ({exc.status}) - pominięto wyszukiwanie po 'przedstawia'.")
        for s in specs:
            i = info.get(s["id"])
            if not i or not i["ok"]:
                if i is not None:
                    ctx.notes.append(f"Commons: Wikidata {s['id']} ma etykietę '{i['label']}', nie pasuje do '{s.get('label')}' - pominięto.")
                continue
            ctx.notes.append(f"Commons: Wikidata {s['id']} = '{i['label']}'"
                             + (f" (kategoria: {', '.join(i['categories'])})" if i["categories"] else ""))
            extra_roots += ["Category:" + c for c in i["categories"]]
            pages = _collect(ctx, {**IMAGEINFO, "generator": "search", "gsrsearch": f"haswbstatement:P180={s['id']}",
                                   "gsrnamespace": "6", "gsrlimit": "50"}, limit=ctx.max_per_query * 2)
            depicts[s["id"]] = {p["title"] for p in pages}
            ctx.notes.append(f"Commons: {len(pages)} plików z deklaracją 'przedstawia {s['id']}'")
            for page in pages:
                item = emit(to_item(page, f"depicts:{s['id']}", ctx.include_video))
                if item:
                    yield item

    # Route 1: categories
    discovered = _discover_categories(ctx)
    roots = list(dict.fromkeys(ctx.target.get("commons_categories", []) + extra_roots + discovered))
    files, visited = _walk(ctx, roots, depth=int(ctx.target.get("commons_depth", 3)))
    ctx.notes.append(f"Commons: przejrzano {len(visited)} kategorii ({len(files)} plików): "
                     + ", ".join(c.removeprefix("Category:") for c in visited[:25])
                     + (" ..." if len(visited) > 25 else ""))
    titles = list(files)
    for i in range(0, len(titles), 50):
        batch = titles[i:i + 50]
        for page in _collect(ctx, {**IMAGEINFO, "titles": "|".join(batch)}):
            item = emit(to_item(page, "category:" + files.get(page["title"], ""), ctx.include_video))
            if item:
                yield item

    # Route 2: full-text search
    for q in ctx.queries:
        pages = _collect(ctx, {**IMAGEINFO, "generator": "search", "gsrsearch": q,
                               "gsrnamespace": "6", "gsrlimit": "50"}, limit=ctx.max_per_query)
        for page in pages:
            item = emit(to_item(page, q, ctx.include_video))
            if item:
                yield item
