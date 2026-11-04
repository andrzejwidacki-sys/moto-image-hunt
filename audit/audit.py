"""Collect hard evidence about a few Wikimedia Commons files: page wikitext, categories,
structured data (depicts), EXIF, usage elsewhere, upload history, and the full-size original."""
import hashlib
import json
import sys
from pathlib import Path

import requests

API = "https://commons.wikimedia.org/w/api.php"
S = requests.Session()
S.headers["User-Agent"] = "moto-image-hunt-audit/1.0 (https://github.com/andrzejwidacki-sys/moto-image-hunt)"


def api(**p):
    r = S.get(API, params={"format": "json", "formatversion": "2", **p}, timeout=60)
    r.raise_for_status()
    return r.json()


def main(titles, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    report = []
    for n, title in enumerate(titles, 1):
        t = "File:" + title.removeprefix("File:")
        d = api(action="query", titles=t, prop="imageinfo|categories|revisions|globalusage|info",
                iiprop="url|size|mime|sha1|timestamp|user|comment|extmetadata|metadata", iilimit="max",
                cllimit="max", rvprop="content|user|timestamp|comment", rvslots="main", rvlimit=1,
                gulimit="max", inprop="url")
        page = d["query"]["pages"][0]
        info = page["imageinfo"][0]
        wikitext = page["revisions"][0]["slots"]["main"]["content"]
        sd = {}
        try:
            e = api(action="wbgetentities", ids=f"M{page['pageid']}", props="claims")
            for pid, claims in (e["entities"][f"M{page['pageid']}"].get("statements") or {}).items():
                sd[pid] = [c.get("mainsnak", {}).get("datavalue", {}).get("value") for c in claims]
        except Exception as exc:  # structured data is optional
            sd = {"error": str(exc)}
        ids = [v["id"] for vals in sd.values() if isinstance(vals, list) for v in vals if isinstance(v, dict) and isinstance(v.get("id"), str)]
        labels = {}
        if ids:
            w = S.get("https://www.wikidata.org/w/api.php", timeout=60, params={
                "action": "wbgetentities", "ids": "|".join(sorted(set(ids))[:50]), "props": "labels|descriptions",
                "languages": "en", "format": "json"}).json()
            labels = {k: {"label": (v.get("labels", {}).get("en") or {}).get("value"),
                          "description": (v.get("descriptions", {}).get("en") or {}).get("value")}
                      for k, v in w.get("entities", {}).items()}
        raw = S.get(info["url"], timeout=180)
        raw.raise_for_status()
        sha = hashlib.sha1(raw.content).hexdigest()
        fname = f"{n:02d}-" + "".join(c if c.isalnum() or c in "._-" else "_" for c in title)[:60]
        (out / fname).write_bytes(raw.content)
        meta = {m["name"]: m["value"] for m in info.get("metadata") or [] if isinstance(m.get("value"), (str, int, float))}
        ext = {k: v.get("value") for k, v in (info.get("extmetadata") or {}).items()}
        item = {
            "title": title, "saved_as": fname, "page": page.get("canonicalurl"), "original_url": info["url"],
            "size_px": [info["width"], info["height"]], "bytes_downloaded": len(raw.content),
            "sha1_commons": info["sha1"], "sha1_downloaded": sha, "sha1_match": sha == info["sha1"],
            "uploaded_by": info["user"], "uploaded": info["timestamp"], "upload_comment": info.get("comment"),
            "categories": [c["title"] for c in page.get("categories", [])],
            "used_on": [f'{g["wiki"]}: {g["title"]}' for g in page.get("globalusage", [])],
            "structured_data": sd, "structured_data_labels": labels,
            "exif": {k: meta[k] for k in meta if k in (
                "Make", "Model", "DateTime", "DateTimeOriginal", "Software", "LensModel", "FocalLength",
                "ExposureTime", "FNumber", "ISOSpeedRatings", "GPSLatitude", "GPSLongitude", "Orientation",
                "ImageDescription", "Artist", "Copyright")},
            "extmetadata": {k: ext.get(k) for k in (
                "ImageDescription", "Artist", "Credit", "LicenseShortName", "LicenseUrl", "DateTimeOriginal",
                "GPSLatitude", "GPSLongitude", "ObjectName", "Categories", "Restrictions", "UsageTerms")},
            "wikitext": wikitext[:6000],
            "history": [{"ts": h["timestamp"], "user": h["user"], "comment": h.get("comment"), "size": [h["width"], h["height"]]}
                        for h in page["imageinfo"]],
        }
        report.append(item)
        print(f"{title}: {len(raw.content)} B, sha1 match={item['sha1_match']}, cats={len(item['categories'])}")
    (out / "audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[2:], sys.argv[1])
