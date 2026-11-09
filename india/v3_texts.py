# -*- coding: utf-8 -*-
"""Wersja 3 = v2 + po jednym dodatkowym, zweryfikowanym zdaniu w scenach 1-5. Hak (iv0) i puenta (iv6) bez zmian.
Źródła nowych zdań: Wikipedia (Pangong Tso: ~2/3 jeziora na obszarze administrowanym przez Chiny; Dashashwamedh Ghat: aarti codziennie o zmierzchu;
Great Rann of Kutch: lęgowisko największych stad flamingów różowych i małych; Radhanagar Beach: długość 2 km), Kerala Tourism + Audley Travel (kettuvallam)."""
import json, pathlib, re, importlib.util, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("v2t", ROOT / "india/v2_texts.py"); v2 = importlib.util.module_from_spec(spec); sys.modules["v2t"] = v2; spec.loader.exec_module(v2)
S = {l: [list(sc) for sc in scenes] for l, scenes in v2.S.items()}
# (scena, pozycja wstawienia) -> {język: (mówione, napis)}
NEW = {
 (1, 2): dict(
  en=("About two thirds of the lake lies in the area administered by China.", "About two-thirds of the lake lies in China-administered territory."),
  es=("Aproximadamente dos tercios del lago se encuentran en la zona administrada por China.", "Aproximadamente dos tercios del lago están en la zona administrada por China."),
  hi=("झील का लगभग दो-तिहाई हिस्सा चीन के प्रशासन वाले क्षेत्र में है।", "झील का लगभग दो-तिहाई हिस्सा चीन के प्रशासन वाले क्षेत्र में है।"),
  pl=("Około dwie trzecie jeziora leży na obszarze administrowanym przez Chiny.", "Około dwie trzecie jeziora leży na obszarze administrowanym przez Chiny.")),
 (2, 3): dict(
  en=("Every day at dusk, priests perform the Ganga aarti ceremony at the Dashashwamedh Ghat.", "Every day at dusk, priests perform the Ganga aarti ceremony at Dashashwamedh Ghat."),
  es=("Cada día, al anochecer, los sacerdotes realizan la ceremonia Ganga aarti en el ghat Dashashwamedh.", "Cada día, al anochecer, los sacerdotes realizan la ceremonia Ganga aarti en el ghat Dashashwamedh."),
  hi=("हर दिन शाम के समय पुजारी दशाश्वमेध घाट पर गंगा आरती करते हैं।", "हर दिन शाम के समय पुजारी दशाश्वमेध घाट पर गंगा आरती करते हैं।"),
  pl=("Każdego dnia o zmierzchu kapłani odprawiają na ghacie Daśaśwamedh ceremonię Ganga aarti.", "Każdego dnia o zmierzchu kapłani odprawiają na ghacie Dashashwamedh ceremonię Ganga aarti.")),
 (3, 2): dict(
  en=("It is also a breeding ground for some of the largest flocks of greater and lesser flamingos.", "It is also a breeding ground for some of the largest flocks of greater and lesser flamingos."),
  es=("También es zona de cría de algunas de las mayores bandadas de flamencos comunes y flamencos enanos.", "También es zona de cría de algunas de las mayores bandadas de flamencos comunes y flamencos enanos."),
  hi=("यह बड़े और छोटे फ़्लेमिंगो के कुछ सबसे बड़े झुंडों का प्रजनन स्थल भी है।", "यह बड़े और छोटे फ़्लेमिंगो के कुछ सबसे बड़े झुंडों का प्रजनन स्थल भी है।"),
  pl=("To także miejsce lęgowe jednych z największych stad flamingów różowych i małych.", "To także miejsce lęgowe jednych z największych stad flamingów różowych i małych.")),
 (4, 1): dict(
  en=("The beach is about two kilometres long.", "The beach is about 2 km long."),
  es=("La playa mide unos dos kilómetros de largo.", "La playa mide unos 2 km de largo."),
  hi=("यह समुद्र तट लगभग दो किलोमीटर लंबा है।", "यह समुद्र तट लगभग 2 किलोमीटर लंबा है।"),
  pl=("Plaża ma około dwóch kilometrów długości.", "Plaża ma około 2 km długości.")),
 (5, 3): dict(
  en=("Today's houseboats are rebuilt versions of the kettuvallam: rice barges made of jackwood planks tied together with coir rope.", "Today's houseboats are rebuilt kettuvallam: rice barges made of jackwood planks tied together with coir rope."),
  es=("Las casas flotantes de hoy son versiones reformadas de los kettuvallam: barcazas arroceras de tablones de yaca atados con cuerda de fibra de coco.", "Las casas flotantes de hoy son versiones reformadas de los kettuvallam: barcazas arroceras de tablones de yaca atados con cuerda de fibra de coco."),
  hi=("आज के हाउसबोट केट्टुवल्लम का नया रूप हैं: धान ढोने वाली नावें, जिनके कटहल की लकड़ी के तख्ते नारियल की रस्सी से बाँधे जाते थे।", "आज के हाउसबोट केट्टुवल्लम का नया रूप हैं: धान ढोने वाली नावें, जिनके कटहल की लकड़ी के तख्ते नारियल की रस्सी से बाँधे जाते थे।"),
  pl=("Dzisiejsze domy na wodzie to przebudowane kettuvallam: barki do przewozu ryżu z desek chlebowca, związanych sznurem z włókna kokosowego.", "Dzisiejsze domy na wodzie to przebudowane kettuvallam: barki do przewozu ryżu z desek chlebowca, związanych sznurem z włókna kokosowego.")),
}
for (k, pos), per in NEW.items():
    for lang, pair in per.items(): S[lang][k].insert(pos, pair)

if __name__ == "__main__":
    tx = json.load(open(ROOT / "tts/texts.json")); cap = json.load(open(ROOT / "india/captions_v2.json"))
    for lang, scenes in S.items():
        assert len(scenes) == 7
        for k, sc in enumerate(scenes):
            spoken = " ".join(sp for sp, _ in sc)
            assert len(re.split(r"(?<=[.!?।])\s+", spoken.strip())) == len(sc), (lang, k, spoken)
            if 1 <= k <= 5: tx.setdefault(f"iw{k}", {})[lang] = spoken
        cap[lang]["tags"] = list(cap[lang]["tags"]); cap[lang]["tags"][3] = dict(pl="Wyspa Havelock, Andamany", en="Havelock Island, Andamans", es="Isla Havelock, Andamán", hi="हैवलॉक द्वीप, अंडमान")[lang]
        cap[lang]["subs"] = [[c for _, c in sc] for sc in scenes]
    json.dump(tx, open(ROOT / "tts/texts.json", "w"), ensure_ascii=False, indent=1)
    json.dump(cap, open(ROOT / "india/captions_v3.json", "w"), ensure_ascii=False, indent=1)
    print("ok", {l: [len(s) for s in sc] for l, sc in S.items()})
