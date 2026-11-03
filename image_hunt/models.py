"""Item model, licence judgement and target matching (pure functions, no network)."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from urllib.parse import unquote

OK, CHECK, NO = "OK", "CHECK", "NO"
VERDICT_RANK = {OK: 0, CHECK: 1, NO: 2}
MATCH_LEVELS = ("exact", "family", "brand")
MATCH_RANK = {"exact": 0, "family": 1, "brand": 2, "other": 3}

_VERSION = re.compile(r"\b(\d\.\d)\b")


def judge_license(raw: str, unknown: str = NO) -> tuple[str, str, bool, str]:
    """Return (label, verdict, attribution_required, note) for a licence string.

    Verdicts are about use in a (possibly monetised) YouTube / social-media video:
      OK    - commercial use + editing allowed
      CHECK - allowed only under conditions that need a human look (ND, GFDL, ...)
      NO    - not allowed (NC, all rights reserved) or unknown
    The licence string is whatever the uploader / platform claims; it is not verified.
    """
    text = (raw or "").strip()
    low = text.lower()
    toks = re.findall(r"[a-z0-9]+", low)
    tokset = set(toks)
    if not toks:
        return "unknown", unknown, False, "no licence information"

    if "rights" in tokset and "reserved" in tokset:
        return "All rights reserved", NO, False, "no licence granted"
    if "nc" in tokset or "noncommercial" in tokset or ("non" in tokset and "commercial" in tokset):
        return text, NO, True, "non-commercial licence"
    if tokset & {"pexels", "pixabay", "unsplash"}:
        return text, OK, False, "platform licence: free for commercial use, attribution optional"
    if "known" in tokset and "restrictions" in tokset:
        return text, CHECK, False, "statement by an institution, not a licence"
    if "government" in tokset:
        return "US Government work", OK, False, "public domain in the US; check other countries"
    if "cc0" in tokset or "zero" in tokset or ("cc" in tokset and "0" in tokset and "by" not in tokset):
        return "CC0 1.0", OK, False, ""
    if tokset & {"pdm", "pd"} or "public domain" in low or "publicdomain" in tokset:
        return "Public domain", OK, False, ""
    if "copyrighted" in tokset and "free" in tokset:
        return text, CHECK, False, "'copyrighted free use' - read the file page"
    if tokset & {"gfdl", "gpl", "fal"} or "free art" in low:
        return text, CHECK, True, "non-CC free licence; terms are awkward for video"

    by = "by" in tokset and ("cc" in tokset or toks[0] == "by") or "attribution" in tokset
    if by:
        nd = bool(tokset & {"nd", "noderivs", "noderivatives"})
        sa = bool(tokset & {"sa", "sharealike"})
        version = _VERSION.search(low)
        label = "CC BY" + ("-ND" if nd else "") + ("-SA" if sa else "")
        if version:
            label += " " + version.group(1)
        if nd:
            return label, CHECK, True, "no-derivatives: cutting/cropping into a video may count as an adaptation"
        if sa:
            return label, OK, True, "share-alike: adaptations must carry the same licence"
        return label, OK, True, ""
    return text, unknown, False, "unrecognised licence"


@dataclass
class Item:
    source: str
    kind: str  # "image" | "video"
    id: str
    title: str
    page_url: str
    file_url: str
    thumb_url: str
    creator: str
    license: str
    license_url: str
    verdict: str
    attribution_required: bool
    description: str = ""
    tags: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    width: int = 0
    height: int = 0
    note: str = ""
    match: str = "other"
    query: str = ""

    def as_dict(self) -> dict:
        return asdict(self)

    def credit(self) -> str:
        who = self.creator or "unknown author"
        lic = self.license + (f" ({self.license_url})" if self.license_url else "")
        return f'"{self.title or self.id}" by {who} via {self.source}, {lic} - {self.page_url}'


def normalise(text: str) -> str:
    t = unquote(text or "").lower()
    t = re.sub(r"[_\-./+,:;()\[\]{}\"'|&=?]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _any(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text) for p in patterns)


def haystack(item: Item) -> str:
    parts = [item.title, item.description, " ".join(item.tags), " ".join(item.categories),
             item.page_url, item.file_url]
    return normalise(" ".join(p for p in parts if p))


def classify(item: Item, target: dict) -> str:
    """Set and return item.match: exact | family | brand | other."""
    text = haystack(item)
    if _any(target.get("exclude", []), text):
        item.match = "other"
    elif _any(target.get("exact", []), text) and (
        not target.get("require_any") or _any(target["require_any"], text)
    ):
        item.match = "exact"
    elif _any(target.get("family", []), text):
        item.match = "family"
    elif _any(target.get("brand", []), text):
        item.match = "brand"
    else:
        item.match = "other"
    return item.match


def dedupe_keys(item: Item) -> set[str]:
    """Keys under which the same picture shows up on different sources."""
    keys: set[str] = set()
    for url in (item.page_url, item.file_url):
        if not url:
            continue
        u = unquote(url).lower().split("#")[0].rstrip("/")
        u = re.sub(r"^https?://(www\.)?", "", u)
        keys.add(u)
        m = re.search(r"flickr\.com/photos/[^/]+/(\d+)", u)
        if m:
            keys.add("flickr:" + m.group(1))
        m = re.search(r"/wiki/(file:[^?]+)", u)
        if m:
            keys.add("commons:" + m.group(1).replace("_", " "))
        m = re.search(r"commons\.wikimedia\.org/wiki/(file:[^?]+)", u)
        if m:
            keys.add("commons:" + m.group(1).replace("_", " "))
    # Aggregators link to the same file through different URLs; title + author is the stable part.
    title = re.sub(r"^file ", "", normalise(item.title))
    title = re.sub(r" (jpe?g|png|webp|gif|tiff?|webm|ogv)$", "", title)
    who = normalise(item.creator)
    if title and who:
        keys.add(f"tc:{title}|{who}")
    return keys
