"""Write results.json / results.csv / report.md / gallery.html / attribution.txt."""
from __future__ import annotations

import csv
import html
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .models import CHECK, MATCH_LEVELS, NO, OK, Item
from .runner import SourceStatus

LEVEL_LABEL = {"exact": "dokładnie ten model", "family": "rodzina modeli", "brand": "sama marka"}
CSV_COLUMNS = ["match", "verdict", "source", "kind", "title", "creator", "license", "attribution_required",
               "license_url", "page_url", "file_url", "width", "height", "note", "tags", "categories",
               "query", "credit"]


def _group(source: str) -> str:
    return source.split("/")[0]


def _cell(items: list[Item]) -> str:
    if not items:
        return "0"
    c = Counter(i.verdict for i in items)
    return f"**{len(items)}** ({c[OK]} OK / {c[CHECK]} CHECK / {c[NO]} NO)"


def _md(text: str, limit: int = 70) -> str:
    """Untrusted text (titles, author names) -> safe single-line Markdown table cell."""
    text = " ".join((text or "").split())
    text = text[:limit] + ("…" if len(text) > limit else "")
    return html.escape(text, quote=False).replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")


def _md_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        return "#"
    return url.replace(" ", "%20").replace("(", "%28").replace(")", "%29")


def _table(rows: list[Item]) -> list[str]:
    out = ["| Źródło | Typ | Tytuł | Autor | Licencja | Link |", "|---|---|---|---|---|---|"]
    for i in rows:
        out.append(f"| {_group(i.source)} | {i.kind} | {_md(i.title)} | {_md(i.creator, 40)} | "
                   f"{_md(i.license, 30)} | [strona]({_md_url(i.page_url)}) |")
    return out


STATUS_PL = {"ok": "ok", "partial": "częściowo", "skipped": "pominięte", "error": "błąd"}


def build_markdown(items: list[Item], statuses: list[SourceStatus], label: str, queries: list[str]) -> str:
    by_src: dict[str, dict[str, list[Item]]] = defaultdict(lambda: defaultdict(list))
    for i in items:
        by_src[_group(i.source)][i.match].append(i)

    L = [f"# Wyniki wyszukiwania: {label}", "",
         f"Uruchomiono: {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}. Zapytania: " + "; ".join(f"`{q}`" for q in queries),
         "", "## Ile zdjęć znaleziono i gdzie", "",
         "| Źródło | Status | Pobrano | " + " | ".join(LEVEL_LABEL[m] for m in MATCH_LEVELS) + " | Nietrafne | Duplikaty |",
         "|---|---|---|" + "---|" * len(MATCH_LEVELS) + "---|---|"]
    for st in statuses:
        cells = [_cell(by_src[st.name][m]) for m in MATCH_LEVELS]
        L.append(f"| {st.name} | {STATUS_PL[st.status]} | {st.fetched} | " + " | ".join(cells) + f" | {st.dropped_other} | {st.duplicates} |")
    kinds = Counter(i.kind for i in items)
    L += ["", f"Razem unikalnych trafień: **{len(items)}** (zdjęcia: {kinds['image']}, wideo: {kinds['video']}). "
          "OK = można użyć w wideo (komercyjnie, z edycją), CHECK = wymaga sprawdzenia, NO = nie wolno.", ""]

    exact_ok = [i for i in items if i.match == "exact" and i.verdict == OK]
    exact_other = [i for i in items if i.match == "exact" and i.verdict != OK]
    family_ok = [i for i in items if i.match == "family" and i.verdict == OK]
    L += [f"## {label} - licencja OK ({len(exact_ok)})", ""]
    L += _table(exact_ok[:100]) if exact_ok else ["Brak trafień."]
    if exact_other:
        L += ["", f"## {label} - wymaga sprawdzenia lub niedozwolone ({len(exact_other)})", ""] + _table(exact_other[:50])
    L += ["", f"## Ta sama rodzina modeli - licencja OK ({len(family_ok)})", ""]
    L += _table(family_ok[:60]) if family_ok else ["Brak trafień."]
    if len(family_ok) > 60 or len(exact_ok) > 100:
        L += ["", "Pełna lista: `results.csv` i `gallery.html` w artefaktach."]

    L += ["", "## Statusy źródeł i uwagi", ""]
    for st in statuses:
        line = f"- **{st.name}**: {STATUS_PL[st.status]}, {st.seconds}s"
        if st.message:
            line += f" - {_md(st.message, 300)}"
        L.append(line)
        L += [f"  - {_md(n, 400)}" for n in st.notes]
    L += ["", "## Zastrzeżenia", "",
          "- Licencję deklaruje autor lub platforma. Przed publikacją otwórz stronę zdjęcia i sprawdź ją.",
          "- CC BY / BY-SA wymagają podania autora i licencji w opisie filmu (patrz `attribution.txt`).",
          "- Licencja do zdjęcia nie obejmuje znaków towarowych ani rozpoznawalnych osób na zdjęciu.",
          "- Pierwsze trafienie 'dokładnie ten model' bywa fałszywe, gdy podpis jest błędny - obejrzyj zdjęcie."]
    return "\n".join(L) + "\n"


def _safe_url(url: str) -> str:
    return html.escape(url, quote=True) if url.startswith(("http://", "https://")) else ""


def build_gallery(items: list[Item], label: str) -> str:
    cards = []
    for i in items:
        thumb = _safe_url(i.thumb_url)
        img = (f'<img src="{thumb}" loading="lazy" referrerpolicy="no-referrer" alt="">' if thumb
               else '<div class="nothumb">brak miniatury</div>')
        cards.append(
            f'<article class="card" data-match="{i.match}" data-verdict="{i.verdict}" '
            f'data-text="{html.escape((i.title + " " + i.creator + " " + i.source).lower(), quote=True)}">'
            f'<a href="{_safe_url(i.page_url)}" target="_blank" rel="noopener noreferrer">{img}</a>'
            f'<div class="meta"><span class="badge {i.verdict}">{i.verdict}</span> '
            f'<span class="badge m">{LEVEL_LABEL.get(i.match, i.match)}</span>'
            f'<p class="t">{html.escape(i.title or i.id)[:120]}</p>'
            f'<p>{html.escape(i.kind)} · {html.escape(_group(i.source))} · {html.escape(i.creator)[:60]}</p>'
            f'<p>{html.escape(i.license)}</p></div></article>')
    return f"""<!doctype html><html lang="pl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(label)} - galeria</title>
<style>
:root{{--bg:#fff;--fg:#1a1a1a;--card:#f4f4f5;--bd:#d4d4d8}}
@media(prefers-color-scheme:dark){{:root{{--bg:#111;--fg:#eee;--card:#1c1c1f;--bd:#3f3f46}}}}
body{{margin:0;padding:16px;background:var(--bg);color:var(--fg);font:14px system-ui,sans-serif}}
.bar{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:8px;overflow:hidden}}
.card img,.nothumb{{width:100%;height:160px;object-fit:cover;display:block}}
.nothumb{{display:flex;align-items:center;justify-content:center}}
.meta{{padding:8px}} .meta p{{margin:4px 0;word-break:break-word}} .t{{font-weight:600}}
.badge{{padding:1px 6px;border-radius:4px;font-size:12px;border:1px solid var(--bd)}}
.badge.OK{{background:#166534;color:#fff}} .badge.CHECK{{background:#a16207;color:#fff}} .badge.NO{{background:#991b1b;color:#fff}}
</style></head><body><h1>{html.escape(label)}</h1>
<div class="bar"><input id="q" placeholder="szukaj w tytule/autorze">
<select id="v"><option value="">każda licencja</option><option>OK</option><option>CHECK</option><option>NO</option></select>
<select id="m"><option value="">każdy poziom</option><option value="exact">dokładnie ten model</option>
<option value="family">rodzina modeli</option><option value="brand">sama marka</option></select>
<span id="n"></span></div><div class="grid" id="g">{''.join(cards)}</div>
<script>
const q=document.getElementById('q'),v=document.getElementById('v'),m=document.getElementById('m'),n=document.getElementById('n');
function f(){{let c=0;document.querySelectorAll('.card').forEach(e=>{{
const ok=(!v.value||e.dataset.verdict===v.value)&&(!m.value||e.dataset.match===m.value)&&e.dataset.text.includes(q.value.toLowerCase());
e.style.display=ok?'':'none';if(ok)c++}});n.textContent=c+' wyników'}}
[q,v,m].forEach(e=>e.addEventListener('input',f));f();
</script></body></html>"""


def write_all(out: Path, items: list[Item], statuses: list[SourceStatus], label: str, queries: list[str]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps({
        "target": label, "queries": queries, "items": [i.as_dict() for i in items],
        "sources": [vars(s) for s in statuses]}, ensure_ascii=False, indent=1), encoding="utf-8")
    with (out / "results.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for i in items:
            row = i.as_dict()
            row["tags"], row["categories"], row["credit"] = ", ".join(i.tags), ", ".join(i.categories), i.credit()
            w.writerow({k: row[k] for k in CSV_COLUMNS})
    (out / "report.md").write_text(build_markdown(items, statuses, label, queries), encoding="utf-8")
    (out / "gallery.html").write_text(build_gallery(items, label), encoding="utf-8")
    credits = [i.credit() for i in items if i.verdict == OK and i.attribution_required and i.match in ("exact", "family")]
    (out / "attribution.txt").write_text("\n".join(credits) + ("\n" if credits else ""), encoding="utf-8")
