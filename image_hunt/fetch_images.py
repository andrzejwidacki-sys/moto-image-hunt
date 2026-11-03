"""Download preview images for the best hits so the results can be looked at (and committed).

    python -m image_hunt.fetch_images --results results --max 80 --levels exact,family,brand

Reads results/results.json, writes results/images/*.jpg + images/index.json and regenerates
gallery.html so it uses the local copies. Only items whose licence verdict is OK or CHECK are
downloaded (never NO), only still images, at most --max of them, each shrunk to <= 1280 px.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
from pathlib import Path

from .http import Http, HttpError
from .models import MATCH_RANK, VERDICT_RANK, Item
from .report import local_key, build_gallery

MAX_SIDE = 1280


def pick(items: list[Item], levels: set[str], limit: int) -> list[Item]:
    chosen = [i for i in items if i.match in levels and i.verdict != "NO" and i.kind == "image"]
    chosen.sort(key=lambda i: (MATCH_RANK[i.match], VERDICT_RANK[i.verdict]))
    return chosen[:limit]


def shrink(data: bytes) -> bytes:
    """Re-encode as JPEG no larger than MAX_SIDE. Raises if the bytes are not an image."""
    from PIL import Image  # imported lazily: only needed for downloads

    with Image.open(io.BytesIO(data)) as im:
        im = im.convert("RGB")
        im.thumbnail((MAX_SIDE, MAX_SIDE))
        out = io.BytesIO()
        im.save(out, "JPEG", quality=85, optimize=True)
        return out.getvalue()


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "item"


def fetch(http, item: Item) -> tuple[bytes | None, str]:
    """Try the preview URL first, then the full file. Returns (jpeg bytes | None, error text)."""
    errors = []
    for url in dict.fromkeys(u for u in (item.thumb_url, item.file_url) if u.startswith(("http://", "https://"))):
        try:
            data, ctype = http.get_bytes(url)
            if not ctype.startswith("image/"):
                errors.append(f"{url}: content type {ctype or '?'}")
                continue
            return shrink(data), ""
        except HttpError as exc:
            errors.append(f"HTTP {exc.status} {exc.body[:80]}")
        except Exception as exc:  # undecodable image etc.
            errors.append(f"{type(exc).__name__}: {exc}"[:120])
    return None, "; ".join(errors) or "no usable URL"


def run(results_dir: Path, http, levels: set[str], limit: int) -> tuple[int, int]:
    data = json.loads((results_dir / "results.json").read_text(encoding="utf-8"))
    items = [Item(**d) for d in data["items"]]
    images = results_dir / "images"
    images.mkdir(exist_ok=True)
    index, local = [], {}
    for n, item in enumerate(pick(items, levels, limit), 1):
        jpeg, error = fetch(http, item)
        entry = {"source": item.source, "id": item.id, "title": item.title, "creator": item.creator,
                 "license": item.license, "verdict": item.verdict, "match": item.match,
                 "page_url": item.page_url, "credit": item.credit(), "file": "", "error": error}
        if jpeg:
            name = f"{n:03d}-{item.match}-{slug(item.title or item.id)}.jpg"
            (images / name).write_bytes(jpeg)
            entry["file"] = f"images/{name}"
            local[local_key(item)] = entry["file"]
        index.append(entry)
    (images / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    (results_dir / "gallery.html").write_text(build_gallery(items, data.get("target", ""), local), encoding="utf-8")
    return len(local), len(index) - len(local)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", default="results")
    ap.add_argument("--max", type=int, default=80)
    ap.add_argument("--levels", default="exact,family,brand")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)
    repo = os.environ.get("GITHUB_REPOSITORY")
    agent = f"image-hunt/1.0 (+https://github.com/{repo})" if repo else "image-hunt/1.0 (open-licence image finder)"
    http = Http(agent, min_interval=0.5, verbose=args.verbose)
    ok, failed = run(Path(args.results), http, set(args.levels.split(",")), args.max)
    print(f"previews downloaded: {ok}, failed: {failed} -> {args.results}/images/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
