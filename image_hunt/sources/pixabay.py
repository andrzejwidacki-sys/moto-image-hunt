"""Pixabay photo and video search.

Documented limits: q <= 100 chars, per_page <= 200, at most 500 hits per query,
100 requests / 60 s per key. The gallery only hot-links previews temporarily;
download the files you actually use.
"""
from __future__ import annotations

from typing import Iterator

from ..models import OK, Item
from .base import Ctx

NAME = "pixabay"
ENV = ["PIXABAY_API_KEY"]
IMAGES = "https://pixabay.com/api/"
VIDEOS = "https://pixabay.com/api/videos/"
LICENSE_URL = "https://pixabay.com/service/license-summary/"
NOTE = "Pixabay Content License: free for commercial use, attribution optional"


def image_item(h: dict, query: str) -> Item:
    tags = [t.strip() for t in (h.get("tags") or "").split(",") if t.strip()]
    return Item(
        source="pixabay", kind="image", id=str(h.get("id")), title=", ".join(tags[:6]),
        page_url=h.get("pageURL", ""), file_url=h.get("largeImageURL") or h.get("webformatURL") or "",
        thumb_url=h.get("previewURL") or h.get("webformatURL") or "", creator=h.get("user", ""),
        license="Pixabay Content License", license_url=LICENSE_URL, verdict=OK,
        attribution_required=False, tags=tags, width=h.get("imageWidth") or 0,
        height=h.get("imageHeight") or 0, note=NOTE, query=query,
    )


def video_item(h: dict, query: str) -> Item:
    tags = [t.strip() for t in (h.get("tags") or "").split(",") if t.strip()]
    vids = h.get("videos") or {}
    best = next((vids[k] for k in ("large", "medium", "small", "tiny") if (vids.get(k) or {}).get("url")), {})
    return Item(
        source="pixabay", kind="video", id=str(h.get("id")), title=", ".join(tags[:6]),
        page_url=h.get("pageURL", ""), file_url=best.get("url", ""),
        thumb_url=(vids.get("tiny") or {}).get("thumbnail", ""), creator=h.get("user", ""),
        license="Pixabay Content License", license_url=LICENSE_URL, verdict=OK,
        attribution_required=False, tags=tags, width=best.get("width") or 0,
        height=best.get("height") or 0, note=NOTE, query=query,
    )


def _run(ctx: Ctx, url: str, extra: dict, make) -> Iterator[Item]:
    key = ctx.key("PIXABAY_API_KEY")
    for q in ctx.queries:
        got, page = 0, 1
        while got < min(ctx.max_per_query, 500):
            data = ctx.http.get_json(url, interval=0.7, params={
                "key": key, "q": q[:100], "per_page": 200, "page": page, "safesearch": "false", **extra})
            hits = data.get("hits") or []
            for h in hits:
                got += 1
                yield make(h, q)
            if not hits or page * 200 >= int(data.get("totalHits", 0)):
                break
            page += 1


def search(ctx: Ctx) -> Iterator[Item]:
    yield from _run(ctx, IMAGES, {"image_type": "photo"}, image_item)
    if ctx.include_video:
        yield from _run(ctx, VIDEOS, {"video_type": "all"}, video_item)
