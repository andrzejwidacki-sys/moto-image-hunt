"""Shared context and helpers for source modules."""
from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from typing import Mapping
from urllib.parse import unquote, urlsplit

from ..http import Http


@dataclass
class Ctx:
    http: Http
    queries: list[str]
    target: dict
    max_per_query: int = 200
    include_video: bool = False
    env: Mapping[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)  # free-text remarks shown in the report

    def key(self, name: str) -> str:
        return (self.env.get(name) or "").strip()


def strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html.unescape(value or ""))
    return re.sub(r"\s+", " ", text).strip()


def slug_title(url: str) -> str:
    """'https://x/photo/urban-biker-in-ankara-34807170/' -> 'urban biker in ankara'."""
    segment = [s for s in urlsplit(url).path.split("/") if s][-1:] or [""]
    text = unquote(segment[0])
    text = re.sub(r"-\d+$", "", text)
    return text.replace("-", " ").replace("_", " ").strip()
