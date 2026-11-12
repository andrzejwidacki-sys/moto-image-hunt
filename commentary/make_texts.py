"""Waliduje data.py i dopisuje teksty mówione do tts/texts.json (klucze cm0..cm8)."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import data

def main():
    tp = Path(__file__).parent.parent / "tts" / "texts.json"
    T = json.loads(tp.read_text(encoding="utf-8"))
    blocks = [("cm0", data.INTRO)] + [(f"cm{i+1}", p) for i, p in enumerate(data.PLACES)]
    for key, b in blocks:
        for l in ("pl", "en"):
            assert len(b["spoken"][l]) == len(b["caption"][l]), (key, l, "spoken/caption")
        assert len(b["spoken"]["pl"]) == len(b["spoken"]["en"]), (key, "pl/en")
        if "shots" in b:
            cov = sorted(i for _, idx in b["shots"] for i in idx)
            assert cov == list(range(len(b["spoken"]["pl"]))), (key, "shots coverage", cov)
        T[key] = {l: " ".join(b["spoken"][l]) for l in ("pl", "en")}
    tp.write_text(json.dumps(T, ensure_ascii=False, indent=1), encoding="utf-8")
    print("OK", [k for k, _ in blocks])

if __name__ == "__main__":
    main()
