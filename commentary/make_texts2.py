"""Waliduje data2.py i dopisuje teksty mówione v2 do tts/texts.json (klucze w0a..w9)."""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import data2 as d

def split_sentences(t):
    return [x for x in re.split(r"(?<=[.!?।])\s+", t.strip()) if x]

def blocks():
    yield "w0a", d.HOOK1
    yield "w0b", d.HOOK2
    yield "w0c", d.HOOK3
    yield "w0d", d.HOOK4
    for i, ch in enumerate(d.CH):
        if ch["a"]:
            yield f"w{i+1}a", ch["a"]
        yield f"w{i+1}b", ch["b"]
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
            T[key] = T.get(key, {}); T[key][l] = sp
        keys.append(key)
    for ch in d.CH:
        cov = sorted(i for _, idx in ch["shots"] for i in idx)
        assert cov == list(range(len(ch["b"]))), (ch["id"], "shots", cov)
        for k in ch["pops"]:
            assert k < len(ch["b"])
        assert ch["b"][-1][0].startswith("Werdykt") and ch["b"][-1][1].startswith("Verdict"), ch["id"]
    assert len(d.MECH_WORDS["pl"]) == len(d.HOOK4_WORD_IDX) == 7
    t = d.tally()
    assert t == {"W": 3, "H": 3, "U": 2}, t
    words = sum(len(" ".join(d.spoken(p[0]) for p in pairs).split()) for _, pairs in blocks())
    print("słowa PL (mowa):", words)
    tp.write_text(json.dumps(T, ensure_ascii=False, indent=1), encoding="utf-8")
    print("OK", ",".join(keys))

if __name__ == "__main__":
    main()
