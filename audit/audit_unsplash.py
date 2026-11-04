"""Download large copies of the Unsplash hits found by the image hunt (images.unsplash.com is not
rate-limited like the API) and, when quota allows, add the API metadata (EXIF, tags, location)."""
import json
import os
import subprocess
import sys
from pathlib import Path

import requests
from PIL import Image
from PIL.ExifTags import TAGS

API = "https://api.unsplash.com/photos/"
S = requests.Session()
S.headers["User-Agent"] = "moto-image-hunt-audit/1.0"


def load_items(branch):
    subprocess.run(["git", "fetch", "--depth", "1", "origin", branch], check=True)
    raw = subprocess.run(["git", "show", "FETCH_HEAD:results.json"], check=True, capture_output=True, text=True).stdout
    return [i for i in json.loads(raw)["items"] if i["source"].startswith("unsplash") and i["match"] == "exact"]


def main(branch, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
    report = []
    for n, it in enumerate(load_items(branch), 1):
        pid = it["page_url"].rstrip("/").rsplit("/", 1)[1][-11:]
        entry = {"id": pid, "page": it["page_url"], "title": it["title"], "author": it["creator"],
                 "description": it.get("description"), "license": it["license"]}
        sep = "&" if "?" in it["file_url"] else "?"
        img = S.get(f"{it['file_url']}{sep}w=3000", timeout=180)
        img.raise_for_status()
        fname = f"{n:02d}-{pid}.jpg".replace("/", "_")
        (out / fname).write_bytes(img.content)
        im = Image.open(out / fname)
        exif = {TAGS.get(k, k): str(v)[:80] for k, v in (im.getexif() or {}).items()}
        entry.update(saved_as=fname, bytes=len(img.content), size_px=list(im.size), embedded_exif=exif)
        try:
            r = S.get(API + pid, timeout=60, headers={"Authorization": f"Client-ID {key}", "Accept-Version": "v1"})
            entry["api_status"] = r.status_code
            entry["api_rate_limit_remaining"] = r.headers.get("X-Ratelimit-Remaining")
            if r.ok:
                p = r.json()
                entry.update(created_at=p.get("created_at"), api_description=p.get("description"),
                             alt_description=p.get("alt_description"), tags=[t["title"] for t in p.get("tags", [])],
                             exif=p.get("exif"), location=p.get("location"), author_username=p["user"]["username"])
        except requests.RequestException as exc:
            entry["api_error"] = str(exc)
        report.append(entry)
        print(pid, entry["size_px"], "api", entry.get("api_status"), "remaining", entry.get("api_rate_limit_remaining"))
        (out / "audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
