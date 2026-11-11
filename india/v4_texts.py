# -*- coding: utf-8 -*-
"""v4 = v3 po weryfikacji faktów z otwartych źródeł (patrz india/SOURCES_V4.md). Zmiany względem v3:
 - Pangong: 4300 m (Wikipedia: 14,200 ft / 4,300 m), nie „ponad 4200”;
 - Varanasi: usunięte „od tysięcy lat pielgrzymi marzą…” (brak w źródłach) -> „większość ghatów służy do kąpieli i ceremonii” (Wikipedia: Varanasi);
 - Rann: usunięte „gdy woda wyparuje, zostaje biała równina” (niepotwierdzone) -> „w porze monsunowej wypełnia się stojącą wodą” (Wikipedia);
 - Radhanagar: „łagodne fale” (brak w źródle) -> „tropikalny las” (Wikipedia: white sand, clear turquoise waters, dense tropical forests);
 - Kuttanad: kettuvallam = barki wożące ryż i przyprawy, deski połączone włóknem kokosowym (Kerala Tourism); bez gatunku drewna.
 - EN: „ghats” z jawną fonetyką dla Kokoro; zdanie 2 sceny Waranasi przebudowane na liczbę pojedynczą (Whisper: „ghats” -> „gods” w każdym wariancie)."""
import json, pathlib, re, importlib.util, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("v3t", ROOT / "india/v3_texts.py"); v3 = importlib.util.module_from_spec(spec); sys.modules["v3t"] = v3; spec.loader.exec_module(v3)
S = {l: [list(sc) for sc in scenes] for l, scenes in v3.S.items()}
def rep(k, i, per):
    for lang, pair in per.items(): S[lang][k][i] = pair
rep(1, 0, dict(
 en=("Highest: Pangong Tso in Ladakh, about four thousand three hundred metres above sea level.", "Highest: Pangong Tso in Ladakh, about 4,300 m above sea level."),
 es=("El más alto: Pangong Tso, en Ladakh, a unos cuatro mil trescientos metros sobre el nivel del mar.", "El más alto: Pangong Tso, en Ladakh, a unos 4300 m sobre el nivel del mar."),
 hi=("सबसे ऊँचाई पर: लद्दाख की पैंगोंग त्सो झील, समुद्र तल से लगभग चार हज़ार तीन सौ मीटर ऊपर।", "सबसे ऊँचाई पर: लद्दाख की पैंगोंग त्सो झील, समुद्र तल से लगभग 4300 मीटर ऊपर।"),
 pl=("Najwyżej: Pangong Co w Ladaku, około czterech tysięcy trzystu metrów nad poziomem morza.", "Najwyżej: Pangong Tso w Ladakhu, około 4300 m n.p.m.")))
rep(2, 2, dict(
 en=("Pilgrims use most of them for bathing and prayer ceremonies.", "Pilgrims use most of them for bathing and prayer ceremonies."),
 es=("Los peregrinos usan la mayoría para bañarse y para ceremonias de oración.", "Los peregrinos usan la mayoría para bañarse y para ceremonias de oración."),
 hi=("तीर्थयात्री ज़्यादातर घाटों का उपयोग स्नान और पूजा-अनुष्ठानों के लिए करते हैं।", "तीर्थयात्री ज़्यादातर घाटों का उपयोग स्नान और पूजा-अनुष्ठानों के लिए करते हैं।"),
 pl=("Pielgrzymi używają większości z nich do kąpieli i ceremonii modlitewnych.", "Pielgrzymi używają większości z nich do kąpieli i ceremonii modlitewnych.")))
rep(3, 1, dict(
 en=("In the monsoon, this plain of salty clay and mud fills with standing water.", "In the monsoon, this plain of salty clay and mud fills with standing water."),
 es=("En el monzón, esta llanura de arcilla salada y barro se llena de agua estancada.", "En el monzón, esta llanura de arcilla salada y barro se llena de agua estancada."),
 hi=("मानसून में नमकीन मिट्टी और कीचड़ का यह मैदान ठहरे हुए पानी से भर जाता है।", "मानसून में नमकीन मिट्टी और कीचड़ का यह मैदान ठहरे हुए पानी से भर जाता है।"),
 pl=("W porze monsunowej ta równina słonej gliny i błota wypełnia się stojącą wodą.", "W porze monsunowej ta równina słonej gliny i błota wypełnia się stojącą wodą.")))
rep(4, 0, dict(
 en=("Radha Nagar on Havelock Island in the Andamans: white sand, turquoise water and tropical forest.", "Radhanagar on Havelock Island in the Andamans: white sand, turquoise water and tropical forest."),
 es=("Rada Nagar, en la isla Havelok, en las islas Andamán: arena blanca, agua turquesa y selva tropical.", "Radhanagar, en la isla Havelock (Andamán): arena blanca, agua turquesa y selva tropical."),
 hi=("अंडमान के हैवलॉक द्वीप पर राधानगर: सफ़ेद रेत, फ़िरोज़ी पानी और उष्णकटिबंधीय जंगल।", "अंडमान के हैवलॉक द्वीप पर राधानगर: सफ़ेद रेत, फ़िरोज़ी पानी और उष्णकटिबंधीय जंगल।"),
 pl=("Rada Nagar na wyspie Havelok w archipelagu Andamanów: biały piasek, turkusowa woda i tropikalny las.", "Radhanagar na wyspie Havelock (Andamany): biały piasek, turkusowa woda i tropikalny las.")))
rep(5, 3, dict(
 en=("Today's houseboats are rebuilt kettuvallam: barges that once carried rice and spices, made of wooden planks joined with coconut fibre.", "Today's houseboats are rebuilt kettuvallam: barges that once carried rice and spices, made of wooden planks joined with coconut fibre."),
 es=("Las casas flotantes de hoy son versiones reformadas de los kettuvalam: barcazas que antes transportaban arroz y especias, hechas de tablones de madera unidos con fibra de coco.", "Las casas flotantes de hoy son versiones reformadas de los kettuvallam: barcazas que antes transportaban arroz y especias, hechas de tablones de madera unidos con fibra de coco."),
 hi=("आज के हाउसबोट केट्टुवल्लम का नया रूप हैं: ऐसी नावें जो कभी चावल और मसाले ढोती थीं, और लकड़ी के तख़्तों को नारियल के रेशे से जोड़कर बनाई जाती थीं।", "आज के हाउसबोट केट्टुवल्लम का नया रूप हैं: ऐसी नावें जो कभी चावल और मसाले ढोती थीं, और लकड़ी के तख़्तों को नारियल के रेशे से जोड़कर बनाई जाती थीं।"),
 pl=("Dzisiejsze domy na wodzie to przebudowane kettuvallam: barki, które dawniej wiozły ryż i przyprawy, zbudowane z drewnianych desek połączonych włóknem kokosowym.", "Dzisiejsze domy na wodzie to przebudowane kettuvallam: barki, które dawniej wiozły ryż i przyprawy, zbudowane z drewnianych desek połączonych włóknem kokosowym.")))
rep(2, 1, dict(en=("More than eighty riverside stairways, each one a ghat, lead down to the Ganges.", "More than 80 riverside stairways, each one a ghat, lead down to the Ganges.")))   # liczba mnoga „ghats” Whisper słyszał jako „gods” w 3 wariantach; liczba pojedyncza jest rozpoznawana
rep(4, 2, dict(pl=("Plaża ma międzynarodowy certyfikat Błękitna Flaga, przyznawany za czystość i bezpieczeństwo.", "Plaża ma międzynarodowy certyfikat Błękitna Flaga, przyznawany za czystość i bezpieczeństwo.")))   # Piper czytał „Blue Flag” jako „Blue of Lack”
rep(4, 3, dict(pl=("W dwa tysiące czwartym roku magazyn Tajm wymienił ją wśród najlepszych plaż świata.", "W 2004 roku magazyn Time wymienił ją wśród najlepszych plaż świata.")))   # mówione „Tajm”, napis „Time”
# EN: jawna fonetyka dla „ghat(s)” (Kokoro czytał „gahts” jako „gods”); [słowo](/IPA/) to składnia misaki
for sc in S["en"]:
    for i, (sp, cp) in enumerate(sc):
        sp2 = sp.replace("gahts", "[ghats](/ɡɔːts/)").replace("each one a ghat,", "each one a [ghat](/ɡɔːt/),").replace("Dashashwamedh Ghat", "Dashashwamedh [Ghat](/ɡɔːt/)")
        sc[i] = (sp2, cp)

if __name__ == "__main__":
    tx = json.load(open(ROOT / "tts/texts.json")); cap = json.load(open(ROOT / "india/captions_v3.json"))
    for lang, scenes in S.items():
        assert len(scenes) == 7
        for k, sc in enumerate(scenes):
            spoken = " ".join(sp for sp, _ in sc)
            assert len(re.split(r"(?<=[.!?।])\s+", spoken.strip())) == len(sc), (lang, k, spoken)
            assert len(sc) == 4
            if 1 <= k <= 5: tx.setdefault(f"ix{k}", {})[lang] = spoken
        cap[lang]["subs"] = [[c for _, c in sc] for sc in scenes]
    json.dump(tx, open(ROOT / "tts/texts.json", "w"), ensure_ascii=False, indent=1)
    json.dump(cap, open(ROOT / "india/captions_v4.json", "w"), ensure_ascii=False, indent=1)
    print("ok")
