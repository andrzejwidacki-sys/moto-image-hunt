"""Pexels photo and video search (endpoints as in the official API documentation)."""
from __future__ import annotations

from typing import Iterator

from ..models import OK, Item
from .base import Ctx, slug_title

NAME = "pexels"
ENV = ["PEXELS_API_KEY"]
PHOTOS = "https://api.pexels.com/v1/search"
VIDEOS = "https://api.pexels.com/v1/videos/search"
LICENSE_URL = "https://www.pexels.com/license/"
NOTE = "Pexels License: free for commercial use, attribution optional"


def photo_item(p: dict, query: str) -> Item:
    src = p.get("src") or {}
    return Item(
        source="pexels", kind="image", id=str(p.get("id")), title=p.get("alt") or slug_title(p.get("url", "")),
        page_url=p.get("url", ""), file_url=src.get("original") or src.get("large2x") or "",
        thumb_url=src.get("medium") or src.get("small") or "", creator=p.get("photographer", ""),
        license="Pexels License", license_url=LICENSE_URL, verdict=OK, attribution_required=False,
        description=p.get("alt") or "", width=p.get("width") or 0, height=p.get("height") or 0,
        note=NOTE, query=query,
    )


def video_item(v: dict, query: str) -> Item:
    files = sorted(v.get("video_files") or [], key=lambda f: f.get("width") or 0, reverse=True)
    return Item(
        source="pexels", kind="video", id=str(v.get("id")), title=slug_title(v.get("url", "")),
        page_url=v.get("url", ""), file_url=(files[0].get("link") if files else "") or "",
        thumb_url=v.get("image", ""), creator=(v.get("user") or {}).get("name", ""),
        license="Pexels License", license_url=LICENSE_URL, verdict=OK, attribution_required=False,
        width=v.get("width") or 0, height=v.get("height") or 0, note=NOTE, query=query,
    )


def _run(ctx: Ctx, url: str, field: str, make) -> Iterator[Item]:
    headers = {"Authorization": ctx.key("PEXELS_API_KEY")}
    for q in ctx.queries:
        got, page = 0, 1
        while got < ctx.max_per_query:
            data = ctx.http.get_json(url, headers=headers, params={"query": q, "per_page": 80, "page": page})
            rows = data.get(field) or []
            for row in rows:
                got += 1
                yield make(row, q)
            if not rows or not data.get("next_page"):
                break
            page += 1


def search(ctx: Ctx) -> Iterator[Item]:
    yield from _run(ctx, PHOTOS, "photos", photo_item)
    if ctx.include_video:
        yield from _run(ctx, VIDEOS, "videos", video_item)
