"""Openverse aggregator (Flickr, Wikimedia, museums, ...). Works anonymously; optional OAuth.

Only `license_type=commercial` is requested: Openverse then drops NC licences itself.
Field names are read defensively because not every one is spelled out in the public docs.
"""
from __future__ import annotations

from typing import Iterator

from ..http import HttpError
from ..models import Item, judge_license
from .base import Ctx

NAME = "openverse"
ENV: list[str] = []  # OPENVERSE_CLIENT_ID / OPENVERSE_CLIENT_SECRET are optional
API = "https://api.openverse.org/v1"


def _token(ctx: Ctx) -> str:
    cid, secret = ctx.key("OPENVERSE_CLIENT_ID"), ctx.key("OPENVERSE_CLIENT_SECRET")
    if not (cid and secret):
        return ""
    form = {"grant_type": "client_credentials", "client_id": cid, "client_secret": secret}
    try:
        return ctx.http.post_form(API + "/auth_tokens/token/", form).get("access_token", "")
    except HttpError as exc:
        if exc.status == 404:
            return ctx.http.post_form(API + "/auth_tokens/token", form).get("access_token", "")
        raise


def license_string(lic: str, version: str) -> str:
    lic = (lic or "").lower()
    if lic == "cc0":
        return "CC0 1.0"
    if lic == "pdm":
        return "Public Domain Mark 1.0"
    return f"CC {lic.upper()} {version or ''}".strip()


def to_item(r: dict, query: str) -> Item:
    label, verdict, attribution, note = judge_license(license_string(r.get("license"), r.get("license_version")))
    provider = r.get("source") or r.get("provider") or "?"
    url = r.get("url") or ""
    return Item(
        source=f"openverse/{provider}", kind="image", id=str(r.get("id")), title=r.get("title") or "",
        page_url=r.get("foreign_landing_url") or url, file_url=url,
        thumb_url=r.get("thumbnail") or url, creator=r.get("creator") or "",
        license=label, license_url=r.get("license_url") or "", verdict=verdict,
        attribution_required=attribution, tags=[t.get("name", "") for t in r.get("tags") or []],
        width=r.get("width") or 0, height=r.get("height") or 0, note=note, query=query,
    )


def search(ctx: Ctx) -> Iterator[Item]:
    token = _token(ctx)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    page_size = 50 if token else 20  # anonymous clients get small pages
    if not token:
        ctx.notes.append("Openverse: tryb anonimowy (małe strony, ograniczona głębokość). "
                         "Ustaw OPENVERSE_CLIENT_ID/SECRET, by pobierać więcej.")
    for q in ctx.queries:
        got, page = 0, 1
        while got < ctx.max_per_query:
            try:
                data = ctx.http.get_json(API + "/images/", headers=headers, params={
                    "q": q, "license_type": "commercial", "page_size": page_size, "page": page})
            except HttpError as exc:
                if page > 1 and 400 <= exc.status < 500:  # ran past the depth limit for this client
                    break
                raise
            results = data.get("results") or []
            if not results:
                break
            for r in results:
                got += 1
                yield to_item(r, q)
            if page >= (data.get("page_count") or page):
                break
            page += 1
