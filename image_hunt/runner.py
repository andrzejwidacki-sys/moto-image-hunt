"""Run sources, classify, de-duplicate and sort."""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from .models import MATCH_RANK, VERDICT_RANK, Item, classify, dedupe_keys
from .sources import ALL, BY_NAME
from .sources.base import Ctx


@dataclass
class SourceStatus:
    name: str
    status: str = "ok"          # ok | partial | skipped | error
    message: str = ""
    fetched: int = 0            # raw items returned by the source
    seconds: float = 0.0
    dropped_other: int = 0      # fetched but not about the target model/brand
    duplicates: int = 0         # already seen from another source
    notes: list[str] = field(default_factory=list)


def run(ctx: Ctx, selected: list[str] | None = None) -> tuple[list[Item], list[SourceStatus]]:
    modules = [BY_NAME[n] for n in selected] if selected else ALL
    items: list[Item] = []
    statuses: list[SourceStatus] = []
    seen: set[str] = set()

    for mod in modules:
        st = SourceStatus(mod.NAME)
        statuses.append(st)
        missing = [e for e in mod.ENV if not ctx.key(e)]
        if missing:
            st.status, st.message = "skipped", "brak klucza: " + ", ".join(missing)
            continue
        started = time.monotonic()
        ctx.notes = []
        try:
            for item in mod.search(ctx):
                st.fetched += 1
                if classify(item, ctx.target) == "other":
                    st.dropped_other += 1
                    continue
                keys = dedupe_keys(item)
                if keys & seen:
                    st.duplicates += 1
                    continue
                seen |= keys
                items.append(item)
        except Exception as exc:  # one broken source must not sink the run
            st.status = "partial" if st.fetched else "error"
            st.message = f"{type(exc).__name__}: {exc}"[:400]
        st.seconds = round(time.monotonic() - started, 1)
        st.notes = list(ctx.notes)

    items.sort(key=lambda i: (MATCH_RANK[i.match], VERDICT_RANK[i.verdict], i.source, i.title.lower()))
    return items, statuses
