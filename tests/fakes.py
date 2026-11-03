"""Canned API responses shaped like the real services (offline stand-in for Http)."""
from __future__ import annotations

from image_hunt.http import HttpError


class FakeHttp:
    def __init__(self, routes):
        self.routes = routes  # list of (predicate(url, params, headers), response | callable | Exception)
        self.calls: list[tuple[str, dict]] = []

    def get_json(self, url, params=None, headers=None, interval=None, timeout=40):
        params = params or {}
        self.calls.append((url, params))
        for pred, resp in self.routes:
            if pred(url, params, headers or {}):
                if isinstance(resp, Exception):
                    raise resp
                return resp(url, params) if callable(resp) else resp
        raise HttpError(404, url, "no fake route")

    def post_form(self, url, data, timeout=40):
        self.calls.append((url, data))
        return {"access_token": "tok"}


def commons_page(pageid, title, lic="CC BY-SA 4.0", mime="image/jpeg", cats=(), artist="<a href='x'>Jan Kowalski</a>",
                 desc="", copyrighted="True"):
    return {
        "pageid": pageid, "ns": 6, "title": title,
        "imageinfo": [{
            "url": f"https://upload.wikimedia.org/x/{pageid}.jpg", "thumburl": f"https://upload.wikimedia.org/t/{pageid}.jpg",
            "descriptionurl": "https://commons.wikimedia.org/wiki/" + title.replace(" ", "_"),
            "width": 4000, "height": 3000, "mime": mime,
            "extmetadata": {
                "LicenseShortName": {"value": lic}, "LicenseUrl": {"value": "https://creativecommons.org/licenses/by-sa/4.0"},
                "Artist": {"value": artist}, "ImageDescription": {"value": desc},
                "AttributionRequired": {"value": "true"}, "Copyrighted": {"value": copyrighted}},
        }],
        "categories": [{"ns": 14, "title": "Category:" + c} for c in cats],
    }
