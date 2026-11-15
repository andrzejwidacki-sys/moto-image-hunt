"""Waliduje data3.py i dopisuje teksty mówione v3 do tts/texts.json (klucze w0a..w0d, w{n}p/a/b, wm, w9)."""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import data3 as d

def split_sentences(t):
    return [x for x in re.split(r"(?<=[.!?।])\s+", t.strip()) if x]

def blocks():
    yield "w0a", d.HOOK1
    yield "w0b", d.HOOK2
    yield "w0c", d.HOOK3
    yield "w0d", d.HOOK4
    for ch in d.CH:
        n = ch["n"]
        if ch.get("pre"):
            yield f"w{n}p", ch["pre"]
        if ch["a"]:
            yield f"w{n}a", ch["a"]
        yield f"w{n}b", ch["b"]
    yield "wm", d.MID
    yield "w9", d.OUTRO

def main():
    tp = Path(__file__).parent.parent / "tts" / "texts.json"
    T = json.loads(tp.read_text(encoding="utf-8"))
    keys = []
    for key, pairs in blocks():
        for li, l in enumerate(("pl", "en")):
            sp = " ".join(d.spoken(p[li]) for p in pairs)
            n = len(split_sentences(sp))
            assert n == len(pairs), (key, l, n, len(pairs), sp)
            T["v3" + key] = T.get("v3" + key, {}); T["v3" + key][l] = sp
        keys.append("v3" + key)
    for ch in d.CH:
        cov = sorted(i for _, idx, _ in ch["shots"] for i in idx)
        assert cov == list(range(len(ch["b"]))), (ch["id"], "shots", cov)
        for _, idx, _ in ch["shots"]:
            assert idx == list(range(idx[0], idx[-1] + 1)), (ch["id"], idx)
        for k in ch["pops"]:
            assert k < len(ch["b"])
        vi = ch["vi"]
        assert ch["b"][vi][0].startswith("Wyrok") and ch["b"][vi][1].startswith("Verdict"), (ch["id"], vi)
        assert ch["chip"][0] in ("a", "b") and ch["chip"][1] < len(ch[ch["chip"][0]]), ch["id"]
        assert "mechani" in d.spoken(ch[ch["chip"][0]][ch["chip"][1]][0]).lower() or ch["id"] in ("grand",), ch["id"]
        assert "mechanism" in d.spoken(ch[ch["chip"][0]][ch["chip"][1]][1]).lower(), ch["id"]
    t = d.tally()
    assert t == {"W": 4, "H": 2, "U": 1, "B": 1}, t
    assert d.ORDER and sorted(d.ORDER) == sorted(c["id"] for c in d.CH)
    for code, idx in d.HOOK4_STAMPS:
        assert d.VERDICT[code]["en"].split()[-1].lower().strip(".") in d.HOOK4[idx][1].lower(), (code, idx)
    # kolejność werdyktów w outro zgodna z licznikami
    for code, idx in d.OUTRO_TALLY:
        assert d.OUTRO[idx][1].split()[0] in ("Four", "Twice", "Once", "And"), (code, idx)
    words = sum(len(" ".join(d.spoken(p[0]) for p in pairs).split()) for _, pairs in blocks())
    wen = sum(len(" ".join(d.spoken(p[1]) for p in pairs).split()) for _, pairs in blocks())
    print("słowa mowy PL/EN:", words, wen)
    tp.write_text(json.dumps(T, ensure_ascii=False, indent=1), encoding="utf-8")
    print("OK", ",".join(keys))

if __name__ == "__main__":
    main()
