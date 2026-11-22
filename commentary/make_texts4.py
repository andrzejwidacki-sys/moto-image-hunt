"""Waliduje data4.py i dopisuje teksty mówione v4 (Bangalore) do tts/texts.json.
Klucze: v4h1, v4h2, v4h3 (zimny start, obietnica), v4{n}a / v4{n}b (rozdziały), v4o (outro)."""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import data4 as d


def split_sentences(t):
    return [x for x in re.split(r"(?<=[.!?।])\s+", t.strip()) if x]


def blocks():
    yield "h1", d.HOOK1
    yield "h2", d.HOOK2
    yield "h3", d.HOOK3
    for ch in d.CH:
        yield f"{ch['n']}a", ch["a"]
        yield f"{ch['n']}b", ch["b"]
    yield "o", d.OUTRO


def main():
    tp = Path(__file__).parent.parent / "tts" / "texts.json"
    T = json.loads(tp.read_text(encoding="utf-8"))
    keys = []
    for key, pairs in blocks():
        for li, l in enumerate(("pl", "en")):
            sp = " ".join(d.spoken(p[li]) for p in pairs)
            assert not re.search(r"\d", sp), (key, l, "cyfra w tekście mówionym", sp)
            n = len(split_sentences(sp))
            assert n == len(pairs), (key, l, n, len(pairs), sp)
            T["v4" + key] = T.get("v4" + key, {})
            T["v4" + key][l] = sp
        keys.append("v4" + key)
    for ch in d.CH:
        cov = sorted(i for _, idx, _ in ch["shots"] for i in idx)
        assert cov == list(range(len(ch["b"]))), (ch["id"], "shots", cov)
        for _, idx, _ in ch["shots"]:
            assert idx == list(range(idx[0], idx[-1] + 1)), (ch["id"], idx)
        for k in ch["pops"]:
            assert k < len(ch["b"]), (ch["id"], k)
        for k in ch["apop"]:
            assert k < len(ch["a"]), (ch["id"], k)
        vi = ch["vi"]
        assert ch["b"][vi][0].startswith("Wyrok") and ch["b"][vi][1].startswith("Verdict"), (ch["id"], vi)
        word = {"F": "mieści", "T": "styk", "N": "daleko"}[ch["verdict"]]
        assert word in ch["b"][vi][0], (ch["id"], "werdykt w tekście != obliczony", ch["verdict"])
        assert d.code_for(d.HOURS_ONE_WAY[ch["id"]]) == ch["verdict"]
        assert ch["km_author"] and str(ch["km_author"]) in d.disp(ch["a"][0][0]), ch["id"]
    t = d.tally()
    assert t == {"F": 3, "T": 2, "N": 1}, t
    for code, idx in d.HOOK3_STAMPS:
        assert d.VERDICT[code]["en"].split()[-1].lower() in d.HOOK3[idx][1].lower(), (code, idx)
    # liczby w outro zgodne z licznikami
    for code, idx in d.OUTRO_TALLY:
        want = {"F": "Three", "T": "Twice", "N": "Once"}[code]
        assert d.OUTRO[idx][1].startswith(want), (code, idx)
    assert sorted(d.ORDER) == sorted(d.WINDOWS)
    for k, (a, b) in d.WINDOWS.items():
        assert 4.5 <= b - a <= 7.0, (k, b - a)
    words = sum(len(" ".join(d.spoken(p[0]) for p in pairs).split()) for _, pairs in blocks())
    wen = sum(len(" ".join(d.spoken(p[1]) for p in pairs).split()) for _, pairs in blocks())
    print("słowa mowy PL/EN:", words, wen)
    tp.write_text(json.dumps(T, ensure_ascii=False, indent=1), encoding="utf-8")
    print("OK", ",".join(keys))


if __name__ == "__main__":
    main()
