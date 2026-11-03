"""CLI: python -m image_hunt --target pulsar-ns125 --out results"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import yaml

from .http import Http
from .report import write_all
from .runner import run
from .sources import BY_NAME
from .sources.base import Ctx


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="targets.yml")
    ap.add_argument("--target", default="pulsar-ns125")
    ap.add_argument("--extra-queries", default="", help="extra phrases separated by ';'")
    ap.add_argument("--max-per-query", type=int, default=200)
    ap.add_argument("--include-video", action="store_true")
    ap.add_argument("--sources", default="all", help="comma list of: " + ", ".join(BY_NAME))
    ap.add_argument("--out", default="results")
    ap.add_argument("--source-budget", type=float, default=420, help="max seconds per source (partial results kept)")
    ap.add_argument("--verbose", action="store_true", help="log every HTTP request with its duration to stderr")
    args = ap.parse_args(argv)

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))["targets"]
    if args.target not in cfg:
        print(f"unknown target '{args.target}'. Available: {', '.join(cfg)}", file=sys.stderr)
        return 1
    target = cfg[args.target]
    extra = [q.strip() for q in re.split(r"[;\n]", args.extra_queries) if q.strip()]
    queries = list(dict.fromkeys(target["queries"] + extra))

    selected = None
    if args.sources != "all":
        selected = [s.strip() for s in args.sources.split(",") if s.strip()]
        bad = [s for s in selected if s not in BY_NAME]
        if bad:
            print(f"unknown sources: {bad}", file=sys.stderr)
            return 1

    repo = os.environ.get("GITHUB_REPOSITORY")
    agent = f"image-hunt/1.0 (+https://github.com/{repo})" if repo else "image-hunt/1.0 (open-licence image finder)"
    ctx = Ctx(http=Http(agent, verbose=args.verbose), queries=queries, target=target, max_per_query=args.max_per_query,
              include_video=args.include_video, env=os.environ)
    items, statuses = run(ctx, selected, source_budget=args.source_budget)
    write_all(Path(args.out), items, statuses, target["label"], queries)

    for st in statuses:
        print(f"{st.name:10} {st.status:8} fetched={st.fetched:5} dropped={st.dropped_other:5} {st.message}")
    print(f"unique relevant items: {len(items)} -> {args.out}/")
    return 0 if any(s.status in ("ok", "partial") for s in statuses) else 2


if __name__ == "__main__":
    sys.exit(main())
