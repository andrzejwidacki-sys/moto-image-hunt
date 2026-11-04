"""Fetch Unsplash API metadata (description, tags, EXIF, location, author) and a large copy of each photo."""
import json
import os
import sys
from pathlib import Path

import requests

API = "https://api.unsplash.com/photos/"
S = requests.Session()
S.headers.update({"Authorization": f"Client-ID {os.environ['UNSPLASH_ACCESS_KEY']}", "Accept-Version": "v1",
                  "User-Agent": "moto-image-hunt-audit/1.0"})


def main(ids, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    report = []
    for n, pid in enumerate(ids, 1):
        r = S.get(API + pid, timeout=60)
        remaining = r.headers.get("X-Ratelimit-Remaining")
        r.raise_for_status()
        p = r.json()
        raw = p["urls"]["raw"]
        sep = "&" if "?" in raw else "?"
        img = S.get(f"{raw}{sep}w=3000&q=90&fm=jpg", timeout=180, headers={"Authorization": None})
        img.raise_for_status()
        fname = f"{n:02d}-{pid}.jpg".replace("/", "_")
        (out / fname).write_bytes(img.content)
        report.append({
            "id": pid, "saved_as": fname, "bytes": len(img.content), "page": p["links"]["html"],
            "created_at": p.get("created_at"), "width": p.get("width"), "height": p.get("height"),
            "description": p.get("description"), "alt_description": p.get("alt_description"),
            "author": p["user"]["name"], "author_username": p["user"]["username"],
            "tags": [t["title"] for t in p.get("tags", [])],
            "exif": p.get("exif"), "location": p.get("location"),
            "promoted_at": p.get("promoted_at"), "topic_submissions": list((p.get("topic_submissions") or {}).keys()),
            "rate_limit_remaining": remaining,
        })
        print(pid, len(img.content), "remaining", remaining)
    (out / "audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[2:], sys.argv[1])
