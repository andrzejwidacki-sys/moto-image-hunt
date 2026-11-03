"""GitHub code search for image/video *files* whose path contains the model name.

A repository licence is not a licence for every picture inside it (people commit scraped
images), so nothing from here is ever rated OK: permissive repo -> CHECK, no licence -> NO.
"""
from __future__ import annotations

from typing import Iterator

from ..http import HttpError
from ..models import CHECK, NO, Item
from .base import Ctx

NAME = "github"
ENV = ["GITHUB_TOKEN"]
API = "https://api.github.com"
IMAGE_EXT = ("jpg", "jpeg", "png", "webp")
VIDEO_EXT = ("mp4", "webm", "mov")
PAGES_PER_QUERY = 3
CODE_SEARCH_INTERVAL = 7.0  # code search allows ~10 requests / minute


def repo_info(ctx: Ctx, cache: dict, full_name: str, headers: dict) -> dict:
    if full_name not in cache:
        try:
            cache[full_name] = ctx.http.get_json(f"{API}/repos/{full_name}", headers=headers)
        except HttpError:
            cache[full_name] = {}
    return cache[full_name]


def to_item(hit: dict, repo: dict, query: str) -> Item:
    full = (hit.get("repository") or {}).get("full_name", "")
    spdx = ((repo.get("license") or {}).get("spdx_id") or "").strip()
    licensed = bool(spdx) and spdx != "NOASSERTION"
    html_url = hit.get("html_url", "")
    raw = html_url.replace("/blob/", "/raw/", 1)
    is_image = hit.get("path", "").lower().rsplit(".", 1)[-1] in IMAGE_EXT
    return Item(
        source="github", kind="image" if is_image else "video", id=f"{full}:{hit.get('path')}",
        title=hit.get("name", ""), page_url=html_url, file_url=raw, thumb_url=raw if is_image else "",
        creator=full.split("/")[0], license=f"repo: {spdx}" if licensed else "repo: no licence",
        license_url="", verdict=CHECK if licensed else NO, attribution_required=licensed,
        description=hit.get("path", ""),
        note=("repo licence may not cover third-party images - verify where the file came from"
              if licensed else "repository has no licence: all rights reserved"),
        query=query,
    )


def search(ctx: Ctx) -> Iterator[Item]:
    headers = {"Authorization": f"Bearer {ctx.key('GITHUB_TOKEN')}", "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28"}
    exts = IMAGE_EXT + (VIDEO_EXT if ctx.include_video else ())
    cache: dict = {}
    seen: set[str] = set()
    for term in ctx.target.get("github_terms", []):
        for ext in exts:
            q = f"{term} in:path extension:{ext}"
            for page in range(1, PAGES_PER_QUERY + 1):
                try:
                    data = ctx.http.get_json(f"{API}/search/code", headers=headers, interval=CODE_SEARCH_INTERVAL,
                                             params={"q": q, "per_page": 100, "page": page})
                except HttpError as exc:
                    # status 0 + "429" = urllib3 gave up retrying a rate-limited response
                    if exc.status in (403, 429) or (exc.status == 0 and "429" in exc.body):
                        ctx.notes.append("GitHub: wyszukiwanie kodu przekroczyło limit zapytań - przerwano po "
                                         f"{len(seen)} trafieniach (to normalne: limit to ok. 10 zapytań/min).")
                        return
                    if exc.status == 422:  # query refused: skip this combination only
                        ctx.notes.append(f"GitHub: zapytanie '{q}' odrzucone (HTTP 422).")
                        break
                    raise
                hits = data.get("items") or []
                for hit in hits:
                    key = f"{hit['repository']['full_name']}:{hit['path']}"
                    if key in seen:
                        continue
                    seen.add(key)
                    yield to_item(hit, repo_info(ctx, cache, hit["repository"]["full_name"], headers), q)
                if len(hits) < 100:
                    break
