"""Kontrola mowy: transkrypcja Whisperem + WER + sondy liczb/ułamków/jednostek.
Użycie: python check_whisper.py <katalog_wyników> [model]. Zapisuje check.json i check.md, uzupełnia report.json."""
import json, re, sys, unicodedata
from pathlib import Path
from probes import PROBES

HERE = Path(__file__).parent
TEXTS = json.loads((HERE / "texts.json").read_text(encoding="utf-8"))


def norm_for_probe(s):
    s = unicodedata.normalize("NFKC", s).lower().replace(" ", " ")
    # kropki między literami ("c.c.") usuwamy, kropki w liczbach zostają
    s = re.sub(r"(?<=[^\W\d_])\.(?=[^\W\d_]|\s|$)", "", s)
    return s


def run_probes(text_key, lang, transcript):
    t = norm_for_probe(transcript)
    out = {}
    for label, by_lang in PROBES.get(text_key, []):
        out[label] = any(re.search(rx, t) for rx in by_lang.get(lang, []))
    return out


def words(s, lang):
    s = unicodedata.normalize("NFKC", s).lower()
    s = re.sub(r"(?<=\d)[,.](?=\d{3}\b)", "", s) if lang in ("en", "es") else s
    try:
        from num2words import num2words
        def conv(m):
            tok = m.group(0)
            if lang == "hi":
                return " "
            whole, _, frac = tok.replace(",", ".").partition(".")
            sep = {"en": " point ", "es": " coma ", "pl": " przecinek "}[lang]
            w = num2words(int(whole), lang=lang)
            if frac:
                w += sep + " ".join(num2words(int(d), lang=lang) for d in frac)
            return " " + w + " "
        s = re.sub(r"\d+(?:[.,]\d+)?", conv, s)
    except Exception:
        pass
    s = re.sub(r"[^\w\s]|_", " ", s)
    return s.split()


def wer(ref, hyp):
    if not ref:
        return None
    d = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        prev, d[0] = d[0], i
        for j, h in enumerate(hyp, 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (r != h))
            prev, d[j] = d[j], cur
    return round(d[-1] / len(ref), 3)


def main(out_dir, size="medium"):
    from faster_whisper import WhisperModel
    out = Path(out_dir)
    rep = json.loads((out / "report.json").read_text(encoding="utf-8"))
    model = WhisperModel(size, device="cpu", compute_type="int8")
    rows = []
    for it in rep["items"]:
        if not it.get("ok") or "file" not in it or it["text"] not in TEXTS:
            continue
        segs, _ = model.transcribe(str(out / it["file"]), language=it["lang"], beam_size=5, condition_on_previous_text=False)
        tr = " ".join(s.text.strip() for s in segs)
        ref = TEXTS[it["text"]][it["lang"]]
        pr = run_probes(it["text"], it["lang"], tr)
        it.update(transcript=tr, wer=wer(words(ref, it["lang"]), words(tr, it["lang"])),
                  probes=pr, probes_pass=sum(pr.values()), probes_total=len(pr))
        rows.append(it)
        print("CHECK", it["voice"], it["text"], it["lang"], it["wer"], f'{it["probes_pass"]}/{it["probes_total"]}', flush=True)
    rep["whisper_model"] = size
    (out / "report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "check.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    md = [f"# Kontrola Whisper ({size})", "", "| tekst | język | głos | WER | sondy | nie przeszły |", "|---|---|---|---|---|---|"]
    for r in rows:
        miss = ", ".join(k for k, v in r["probes"].items() if not v)
        md.append(f'| {r["text"]} | {r["lang"]} | {r["voice"]} | {r["wer"]} | {r["probes_pass"]}/{r["probes_total"]} | {miss} |')
    (out / "check.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "medium")
