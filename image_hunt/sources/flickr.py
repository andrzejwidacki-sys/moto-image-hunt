"""Flickr search restricted to licences that allow commercial use."""
from __future__ import annotations

from typing import Iterator

from ..http import HttpError
from ..models import Item, judge_license
from .base import Ctx

NAME = "flickr"
ENV = ["FLICKR_API_KEY"]
API = "https://www.flickr.com/services/rest/"

# Flickr licence ids. 0-3 (all rights reserved / NC) are never requested.
LICENSES = {
    "4": ("Attribution License", "https://creativecommons.org/licenses/by/2.0/"),
    "5": ("Attribution-ShareAlike License", "https://creativecommons.org/licenses/by-sa/2.0/"),
    "6": ("Attribution-NoDerivs License", "https://creativecommons.org/licenses/by-nd/2.0/"),
    "7": ("No known copyright restrictions", "https://www.flickr.com/commons/usage/"),
    "8": ("United States Government Work", "http://www.usa.gov/copyright.shtml"),
    "9": ("Public Domain Dedication (CC0)", "https://creativecommons.org/publicdomain/zero/1.0/"),
    "10": ("Public Domain Mark", "https://creativecommons.org/publicdomain/mark/1.0/"),
}
EXTRAS = "license,owner_name,tags,description,url_o,url_l,url_c,url_m,o_dims,media"


def to_item(p: dict, query: str) -> Item:
    lic_name, lic_url = LICENSES.get(str(p.get("license")), ("", ""))
    label, verdict, attribution, note = judge_license(lic_name)
    if str(p.get("license")) in ("4", "5", "6"):
        label = {"4": "CC BY 2.0", "5": "CC BY-SA 2.0", "6": "CC BY-ND 2.0"}[str(p["license"])]
    owner, pid = p.get("owner", ""), p.get("id", "")
    base = f"https://live.staticflickr.com/{p.get('server')}/{pid}_{p.get('secret')}"
    return Item(
        source="flickr", kind="video" if p.get("media") == "video" else "image", id=str(pid),
        title=p.get("title") or "", page_url=f"https://www.flickr.com/photos/{owner}/{pid}",
        file_url=p.get("url_o") or p.get("url_l") or p.get("url_c") or base + "_b.jpg",
        thumb_url=p.get("url_m") or base + "_m.jpg", creator=p.get("ownername") or owner,
        license=label, license_url=lic_url, verdict=verdict, attribution_required=attribution,
        description=(p.get("description") or {}).get("_content", "") if isinstance(p.get("description"), dict) else "",
        tags=(p.get("tags") or "").split(), width=int(p.get("width_o") or 0),
        height=int(p.get("height_o") or 0), note=note, query=query,
    )


def search(ctx: Ctx) -> Iterator[Item]:
    key = ctx.key("FLICKR_API_KEY")
    for q in ctx.queries:
        got, page = 0, 1
        while got < ctx.max_per_query:
            data = ctx.http.get_json(API, params={
                "method": "flickr.photos.search", "api_key": key, "format": "json", "nojsoncallback": 1,
                "text": q, "license": ",".join(LICENSES), "sort": "relevance", "safe_search": 1,
                "media": "all" if ctx.include_video else "photos", "extras": EXTRAS,
                "per_page": 250, "page": page})
            if data.get("stat") != "ok":
                raise HttpError(0, API, f"Flickr error {data.get('code')}: {data.get('message')}")
            photos = data["photos"]
            for p in photos.get("photo", []):
                got += 1
                yield to_item(p, q)
            if page >= int(photos.get("pages", 0)):
                break
            page += 1
