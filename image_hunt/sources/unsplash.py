"""Unsplash photo search. Demo-tier keys have a low hourly request limit, so the run stops
early (keeping what it already has) when the API starts refusing requests."""
from __future__ import annotations

from typing import Iterator

from ..http import HttpError
from ..models import OK, Item
from .base import Ctx

NAME = "unsplash"
ENV = ["UNSPLASH_ACCESS_KEY"]
API = "https://api.unsplash.com/search/photos"
LICENSE_URL = "https://unsplash.com/license"


def to_item(r: dict, query: str) -> Item:
    urls, user = r.get("urls") or {}, r.get("user") or {}
    desc = " ".join(x for x in (r.get("description"), r.get("alt_description")) if x)
    return Item(
        source="unsplash", kind="image", id=str(r.get("id")), title=r.get("description") or r.get("alt_description") or "",
        page_url=(r.get("links") or {}).get("html", ""), file_url=urls.get("full") or urls.get("regular") or "",
        thumb_url=urls.get("small") or urls.get("thumb") or "", creator=user.get("name", ""),
        license="Unsplash License", license_url=LICENSE_URL, verdict=OK, attribution_required=False,
        description=desc, tags=[t.get("title", "") for t in r.get("tags") or [] if isinstance(t, dict)],
        width=r.get("width") or 0, height=r.get("height") or 0,
        note="Unsplash License: free for commercial use, attribution optional", query=query,
    )


def search(ctx: Ctx) -> Iterator[Item]:
    headers = {"Authorization": f"Client-ID {ctx.key('UNSPLASH_ACCESS_KEY')}", "Accept-Version": "v1"}
    for q in ctx.queries:
        got, page = 0, 1
        while got < ctx.max_per_query:
            try:
                data = ctx.http.get_json(API, headers=headers, params={"query": q, "per_page": 30, "page": page})
            except HttpError as exc:
                if exc.status in (403, 429):
                    ctx.notes.append("Unsplash: limit zapytań wyczerpany - wyniki częściowe.")
                    return
                raise
            rows = data.get("results") or []
            for r in rows:
                got += 1
                yield to_item(r, q)
            if not rows or page >= int(data.get("total_pages", 0)):
                break
            page += 1
