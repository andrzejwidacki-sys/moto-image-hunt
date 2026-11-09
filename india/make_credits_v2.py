"""Generuje CREDITS_V2.md z photos_v2.json (ujęcia faktycznie użyte wg planów) + muzyka + dźwięki tła."""
import json, sys, glob, os
P = json.load(open(os.environ.get("PHOTOS", "photos_v2.json")))
plans = {}
for f in glob.glob(os.environ.get("PLANS", "plans/plan_*.json")):
    pl = json.load(open(f)); plans[os.path.basename(f)[5:7]] = {s["name"]: s.get("n_shots") for s in pl["segments"]}
used = {}
for k, shots in P.items():
    n = max([pl.get(k) or len(shots) for pl in plans.values()] or [len(shots)])
    for s in shots[:n]: used.setdefault(s["id"], dict(s, scenes=[]))["scenes"].append(k)
PLACE = {"hook": "Pangong Tso", "s1": "Pangong Tso", "s2": "Varanasi", "s3": "Great Rann of Kutch", "s4": "Radhanagar Beach", "s5": "Kuttanad", "payoff": "Pangong Tso"}
out = ["# Credits — „Indie. Pięć twarzy wody” (%s)" % os.environ.get("VER", "v2") + "\n", "## Zdjęcia (tylko CC0 / public domain / CC BY)\n",
       "| Miejsce | Autor | Licencja | Tytuł / strona | Data |", "|---|---|---|---|---|"]
for i, s in sorted(used.items(), key=lambda kv: list(PLACE).index(kv[1]["scenes"][0])):
    out.append(f"| {PLACE[s['scenes'][0]]} | {s['author']} | [{s['license']}]({s['license_url']}) | [{s['title']}]({s['page']}) | {s.get('date','')} |")
out += ["", "Uwaga: zdjęcia sceny „Havelock” pochodzą z plaż wyspy Havelock; nie każde jest opisane jako Radhanagar.", "Zmiany: kadrowanie, ruch kamery (zoom/przesunięcie), jednolita korekcja kolorów, winieta.", "",
        "## Muzyka", "", "- Transformations 3 — HoliznaCC0, CC0 1.0 — https://freemusicarchive.org/music/holiznacc0/transformations/transformations-3/", "",
        "## Dźwięki tła (domena publiczna wg metadanych Wikimedia Commons)", "",
        "- On a pebble beach — earthcalling (2007) — https://commons.wikimedia.org/wiki/File:On_a_pebble_beach.ogg",
        "- Boat by a wharf 2 — ezwa (2008) — https://commons.wikimedia.org/wiki/File:Boat_by_a_wharf_2.ogg",
        "- Boat by a wharf 3 — ezwa (2008) — https://commons.wikimedia.org/wiki/File:Boat_by_a_wharf_3.ogg",
        "- Beach sounds South Carolina — Anthropic42 (en.wikipedia, 2003) — https://commons.wikimedia.org/wiki/File:Beach_sounds_South_Carolina.ogg", "",
        "Uwaga: nagrania tła nie są z Indii (to generyczne ambience; zostały użyte jako tło dźwiękowe, nie jako dokument).", "",
        "## Głos", "", "- EN/ES/HI: Kokoro-82M (Apache-2.0), głosy af_heart / ef_dora / hf_alpha — synteza mowy.",
        "- PL: Piper pl_PL-gosia-medium (zbiór danych CC0) — synteza mowy.", "- Wszystkie wersje: lektor syntetyczny; teksty ES/HI/PL wymagają weryfikacji przez native speakera."]
open(os.environ.get("OUTMD", "CREDITS_V2.md"), "w").write("\n".join(out) + "\n"); print("\n".join(out))
