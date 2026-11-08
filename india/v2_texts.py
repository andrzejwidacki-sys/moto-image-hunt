# -*- coding: utf-8 -*-
"""Teksty wersji 2 filmu 'Indie. Pięć twarzy wody': dla każdego języka i sceny lista zdań (mówione, napis).
mówione = pisownia pod TTS (liczby słowami, fonetyczne nazwy), napis = zapis na ekranie (cyfry, poprawne nazwy).
Uruchomienie: python3 india/v2_texts.py  -> dopisuje klucze iv0..iv6 do tts/texts.json i zapisuje india/captions_v2.json."""
import json, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
S = {}
S["pl"] = [
 # iv0 hook
 [("Pięć miejsc w Indiach.", "Pięć miejsc w Indiach."), ("Pięć rodzajów wody.", "Pięć rodzajów wody."),
  ("W jednym z nich ludzie uprawiają ryż poniżej poziomu morza.", "W jednym z nich ludzie uprawiają ryż poniżej poziomu morza."), ("Zgadniesz, w którym?", "Zgadniesz, w którym?")],
 # iv1 Pangong
 [("Najwyżej: Pangong Tso w Ladakhu, ponad cztery tysiące dwieście metrów nad poziomem morza.", "Najwyżej: Pangong Tso w Ladakhu, ponad 4200 m n.p.m."),
  ("Jezioro ma sto trzydzieści cztery kilometry długości.", "Jezioro ma 134 km długości."),
  ("Mimo zasolenia zimą zamarza.", "Mimo zasolenia zimą zamarza.")],
 # iv2 Varanasi
 [("Waranasi, jedno z najstarszych żywych miast świata.", "Waranasi, jedno z najstarszych żywych miast świata."),
  ("Ponad osiemdziesiąt ghatów schodzi tu do Gangesu.", "Ponad 80 ghatów schodzi tu do Gangesu."),
  ("Od tysięcy lat pielgrzymi marzą o tym, by zanurzyć się w tej rzece.", "Od tysięcy lat pielgrzymi marzą o tym, by zanurzyć się w tej rzece.")],
 # iv3 Rann
 [("Wielki Ran Kucz w Gudżaracie ma około siedmiu i pół tysiąca kilometrów kwadratowych.", "Wielki Rann Kutch w Gudżaracie ma ok. 7500 km²."),
  ("W porze monsunowej wypełnia go woda, a gdy ta wyparuje, zostaje biała, słona równina.", "W porze monsunowej wypełnia go woda, a gdy ta wyparuje, zostaje biała, słona równina."),
  ("To jedno z najgorętszych miejsc w Indiach, a zimą temperatura potrafi spaść poniżej zera.", "To jedno z najgorętszych miejsc w Indiach, a zimą temperatura potrafi spaść poniżej zera.")],
 # iv4 Radhanagar
 [("Radha Nagar na wyspie Havelok w archipelagu Andamanów: biały piasek, turkusowa woda, łagodne fale.", "Radhanagar na wyspie Havelock (Andamany): biały piasek, turkusowa woda, łagodne fale."),
  ("Plaża ma międzynarodowy certyfikat Blue Flag, przyznawany za czystość i bezpieczeństwo.", "Plaża ma międzynarodowy certyfikat Blue Flag, przyznawany za czystość i bezpieczeństwo."),
  ("W dwa tysiące czwartym roku magazyn Time wymienił ją wśród najlepszych plaż świata.", "W 2004 roku magazyn Time wymienił ją wśród najlepszych plaż świata.")],
 # iv5 Kuttanad
 [("Odpowiedź: Kuttanad w Kerali, region o najniższym położeniu w Indiach.", "Odpowiedź: Kuttanad w Kerali, region o najniższym położeniu w Indiach."),
  ("Ryż uprawia się tu od ponad metra do trzech metrów poniżej poziomu morza.", "Ryż uprawia się tu od ponad 1 m do 3 m poniżej poziomu morza."),
  ("W dwa tysiące trzynastym roku organizacja ONZ do spraw wyżywienia i rolnictwa uznała ten system uprawy za Globalnie Ważny System Dziedzictwa Rolniczego.", "W 2013 roku FAO (ONZ) uznała ten system uprawy za Globalnie Ważny System Dziedzictwa Rolniczego.")],
 # iv6 payoff
 [("Jezioro, które zamarza na ponad czterech tysiącach metrów, i pola ryżowe poniżej poziomu morza.", "Jezioro, które zamarza na ponad 4000 m, i pola ryżowe poniżej poziomu morza."),
  ("To są te same Indie.", "To są te same Indie."),
  ("Która z tych pięciu wód zaskoczyła cię najbardziej?", "Która z tych pięciu wód zaskoczyła cię najbardziej?"), ("Napisz w komentarzu.", "Napisz w komentarzu.")],
]
S["en"] = [
 [("Five places in India.", "Five places in India."), ("Five kinds of water.", "Five kinds of water."),
  ("In one of them, people grow rice below sea level.", "In one of them, people grow rice below sea level."), ("Can you guess which?", "Can you guess which?")],
 [("Highest: Pangong Tso in Ladakh, more than four thousand two hundred metres above sea level.", "Highest: Pangong Tso in Ladakh, over 4,200 m above sea level."),
  ("The lake is one hundred and thirty-four kilometres long.", "The lake is 134 km long."),
  ("Despite its salinity, it freezes over in winter.", "Despite its salinity, it freezes over in winter.")],
 [("Varanasi, one of the world's oldest living cities.", "Varanasi, one of the world's oldest living cities."),
  ("More than eighty [ghats](/ɡɑːts/) lead down to the Ganges.", "More than 80 ghats lead down to the Ganges."),
  ("For thousands of years, pilgrims have hoped to bathe in this river.", "For thousands of years, pilgrims have hoped to bathe in this river.")],
 [("The Great Rann of Kutch in Gujarat covers about seven and a half thousand square kilometres.", "The Great Rann of Kutch in Gujarat covers about 7,500 km²."),
  ("In the monsoon, water fills it; when the water evaporates, a white salt plain is left.", "In the monsoon, water fills it; when the water evaporates, a white salt plain is left."),
  ("It is one of the hottest places in India, yet in winter the temperature can fall below zero.", "It is one of the hottest places in India, yet in winter the temperature can fall below zero.")],
 [("Radha Nagar on Havelock Island in the Andamans: white sand, turquoise water, gentle waves.", "Radhanagar on Havelock Island in the Andamans: white sand, turquoise water, gentle waves."),
  ("The beach holds the international Blue Flag certification, awarded for cleanliness and safety.", "The beach holds the international Blue Flag certification, awarded for cleanliness and safety."),
  ("In two thousand and four, Time magazine listed it among the best beaches in the world.", "In 2004, Time magazine listed it among the best beaches in the world.")],
 [("The answer: Kuttanad in Kerala, the region with the lowest altitude in India.", "The answer: Kuttanad in Kerala, the region with the lowest altitude in India."),
  ("Rice is grown here from just over one metre to three metres below sea level.", "Rice is grown here from just over 1 m to 3 m below sea level."),
  ("In two thousand and thirteen, the UN Food and Agriculture Organization recognised this farming system as a Globally Important Agricultural Heritage System.", "In 2013, the UN's FAO recognised this farming system as a Globally Important Agricultural Heritage System.")],
 [("A lake that freezes above four thousand metres, and rice fields below sea level.", "A lake that freezes above 4,000 m, and rice fields below sea level."),
  ("Same India.", "Same India."),
  ("Which of these five waters surprised you most?", "Which of these five waters surprised you most?"), ("Tell me in the comments.", "Tell me in the comments.")],
]
S["es"] = [
 [("Cinco lugares de la India.", "Cinco lugares de la India."), ("Cinco clases de agua.", "Cinco clases de agua."),
  ("En uno de ellos se cultiva arroz por debajo del nivel del mar.", "En uno de ellos se cultiva arroz por debajo del nivel del mar."), ("¿Adivinas cuál?", "¿Adivinas cuál?")],
 [("El más alto: Pangong Tso, en Ladakh, a más de cuatro mil doscientos metros sobre el nivel del mar.", "El más alto: Pangong Tso, en Ladakh, a más de 4200 m sobre el nivel del mar."),
  ("El lago mide ciento treinta y cuatro kilómetros de largo.", "El lago mide 134 km de largo."),
  ("Pese a su salinidad, en invierno se congela.", "Pese a su salinidad, en invierno se congela.")],
 [("Varanasi, una de las ciudades vivas más antiguas del mundo.", "Varanasi, una de las ciudades vivas más antiguas del mundo."),
  ("Más de ochenta ghats bajan hasta el Ganges.", "Más de 80 ghats bajan hasta el Ganges."),
  ("Desde hace miles de años, los peregrinos sueñan con bañarse en este río.", "Desde hace miles de años, los peregrinos sueñan con bañarse en este río.")],
 [("El Gran Ran de Kuch, en Guyarat, abarca unos siete mil quinientos kilómetros cuadrados.", "El Gran Rann de Kutch, en Gujarat, abarca unos 7500 km²."),
  ("En el monzón se llena de agua; cuando esta se evapora, queda una llanura blanca de sal.", "En el monzón se llena de agua; cuando esta se evapora, queda una llanura blanca de sal."),
  ("Es uno de los lugares más calurosos de la India, pero en invierno la temperatura puede bajar de cero.", "Es uno de los lugares más calurosos de la India, pero en invierno la temperatura puede bajar de cero.")],
 [("Radha Nagar, en la isla Havelok, en las Andamán: arena blanca, agua turquesa y olas suaves.", "Radhanagar, en la isla Havelock (Andamán): arena blanca, agua turquesa y olas suaves."),
  ("La playa tiene la certificación internacional Bandera Azul, que se concede por limpieza y seguridad.", "La playa tiene la certificación internacional Bandera Azul, que se concede por limpieza y seguridad."),
  ("En dos mil cuatro, la revista Time la incluyó entre las mejores playas del mundo.", "En 2004, la revista Time la incluyó entre las mejores playas del mundo.")],
 [("La respuesta: Kuttanad, en Kerala, la región más baja de la India.", "La respuesta: Kuttanad, en Kerala, la región más baja de la India."),
  ("Aquí se cultiva arroz desde algo más de un metro hasta tres metros por debajo del nivel del mar.", "Aquí se cultiva arroz desde algo más de 1 m hasta 3 m por debajo del nivel del mar."),
  ("En dos mil trece, la FAO reconoció este sistema agrícola como Sistema Importante del Patrimonio Agrícola Mundial.", "En 2013, la FAO reconoció este sistema agrícola como Sistema Importante del Patrimonio Agrícola Mundial.")],
 [("Un lago que se congela a más de cuatro mil metros y arrozales por debajo del nivel del mar.", "Un lago que se congela a más de 4000 m y arrozales por debajo del nivel del mar."),
  ("Es la misma India.", "Es la misma India."),
  ("¿Cuál de estas cinco aguas te sorprendió más?", "¿Cuál de estas cinco aguas te sorprendió más?"), ("Cuéntamelo en los comentarios.", "Cuéntamelo en los comentarios.")],
]
S["hi"] = [
 [("भारत की पाँच जगहें।", "भारत की पाँच जगहें।"), ("पानी के पाँच रूप।", "पानी के पाँच रूप।"),
  ("इनमें से एक जगह पर लोग समुद्र तल से नीचे धान उगाते हैं।", "इनमें से एक जगह पर लोग समुद्र तल से नीचे धान उगाते हैं।"), ("क्या आप बता सकते हैं, कौन-सी?", "क्या आप बता सकते हैं, कौन-सी?")],
 [("सबसे ऊँचाई पर: लद्दाख की पैंगोंग त्सो झील, समुद्र तल से चार हज़ार दो सौ मीटर से भी ज़्यादा ऊपर।", "सबसे ऊँचाई पर: लद्दाख की पैंगोंग त्सो झील, समुद्र तल से 4200 मीटर से भी ज़्यादा ऊपर।"),
  ("यह झील एक सौ चौंतीस किलोमीटर लंबी है।", "यह झील 134 किलोमीटर लंबी है।"),
  ("खारेपन के बावजूद सर्दियों में यह जम जाती है।", "खारेपन के बावजूद सर्दियों में यह जम जाती है।")],
 [("वाराणसी, दुनिया के सबसे पुराने जीवित शहरों में से एक।", "वाराणसी, दुनिया के सबसे पुराने जीवित शहरों में से एक।"),
  ("यहाँ अस्सी से ज़्यादा घाट गंगा तक उतरते हैं।", "यहाँ 80 से ज़्यादा घाट गंगा तक उतरते हैं।"),
  ("हज़ारों सालों से तीर्थयात्री इस नदी में स्नान करने की आस रखते हैं।", "हज़ारों सालों से तीर्थयात्री इस नदी में स्नान करने की आस रखते हैं।")],
 [("गुजरात का कच्छ का बड़ा रण लगभग साढ़े सात हज़ार वर्ग किलोमीटर में फैला है।", "गुजरात का कच्छ का बड़ा रण लगभग 7500 वर्ग किलोमीटर में फैला है।"),
  ("मानसून में इसमें पानी भर जाता है, और पानी सूखने पर सफ़ेद नमक का मैदान बचता है।", "मानसून में इसमें पानी भर जाता है, और पानी सूखने पर सफ़ेद नमक का मैदान बचता है।"),
  ("यह भारत की सबसे गर्म जगहों में से एक है, फिर भी सर्दियों में तापमान शून्य से नीचे जा सकता है।", "यह भारत की सबसे गर्म जगहों में से एक है, फिर भी सर्दियों में तापमान शून्य से नीचे जा सकता है।")],
 [("अंडमान के हैवलॉक द्वीप पर राधानगर: सफ़ेद रेत, फ़िरोज़ी पानी और धीमी लहरें।", "अंडमान के हैवलॉक द्वीप पर राधानगर: सफ़ेद रेत, फ़िरोज़ी पानी और धीमी लहरें।"),
  ("इस समुद्र तट को सफ़ाई और सुरक्षा के लिए अंतरराष्ट्रीय ब्लू फ़्लैग प्रमाणन मिला है।", "इस समुद्र तट को सफ़ाई और सुरक्षा के लिए अंतरराष्ट्रीय ब्लू फ़्लैग प्रमाणन मिला है।"),
  ("दो हज़ार चार में टाइम पत्रिका ने इसे दुनिया के सबसे अच्छे समुद्र तटों में गिना।", "2004 में टाइम पत्रिका ने इसे दुनिया के सबसे अच्छे समुद्र तटों में गिना।")],
 [("जवाब: केरल का कुट्टनाड, भारत का सबसे नीचा इलाक़ा।", "जवाब: केरल का कुट्टनाड, भारत का सबसे नीचा इलाक़ा।"),
  ("यहाँ धान की खेती समुद्र तल से लगभग एक से तीन मीटर नीचे होती है।", "यहाँ धान की खेती समुद्र तल से लगभग 1 से 3 मीटर नीचे होती है।"),
  ("दो हज़ार तेरह में संयुक्त राष्ट्र के खाद्य और कृषि संगठन ने इस कृषि प्रणाली को विश्व स्तर पर महत्वपूर्ण कृषि विरासत प्रणाली घोषित किया।", "2013 में संयुक्त राष्ट्र के खाद्य और कृषि संगठन (FAO) ने इस कृषि प्रणाली को विश्व स्तर पर महत्वपूर्ण कृषि विरासत प्रणाली घोषित किया।")],
 [("चार हज़ार मीटर से ऊपर जमने वाली झील और समुद्र तल से नीचे धान के खेत।", "4000 मीटर से ऊपर जमने वाली झील और समुद्र तल से नीचे धान के खेत।"),
  ("ये एक ही भारत है।", "ये एक ही भारत है।"),
  ("इन पाँच जलों में से किसने आपको सबसे ज़्यादा चौंकाया?", "इन पाँच जलों में से किसने आपको सबसे ज़्यादा चौंकाया?"), ("कमेंट में बताइए।", "कमेंट में बताइए।")],
]
TAGS = {"en": ["Pangong Tso, Ladakh", "Varanasi, Uttar Pradesh", "Great Rann of Kutch, Gujarat", "Radhanagar Beach, Andamans", "Kuttanad, Kerala"],
        "es": ["Pangong Tso, Ladakh", "Varanasi, Uttar Pradesh", "Gran Rann de Kutch, Gujarat", "Playa de Radhanagar, Andamán", "Kuttanad, Kerala"],
        "hi": ["पैंगोंग त्सो, लद्दाख", "वाराणसी, उत्तर प्रदेश", "कच्छ का बड़ा रण, गुजरात", "राधानगर बीच, अंडमान", "कुट्टनाड, केरल"],
        "pl": ["Pangong Tso, Ladakh", "Waranasi, Uttar Pradesh", "Wielki Rann Kutch, Gudżarat", "Plaża Radhanagar, Andamany", "Kuttanad, Kerala"]}

if __name__ == "__main__":
    v1 = json.load(open(ROOT / "india/captions.json"))
    tx = json.load(open(ROOT / "tts/texts.json"))
    cap = {}
    for lang, scenes in S.items():
        assert len(scenes) == 7, lang
        for k, sc in enumerate(scenes):
            spoken = " ".join(sp for sp, _ in sc)
            n = len(re.split(r"(?<=[.!?।])\s+", spoken.strip()))
            assert n == len(sc), (lang, k, n, len(sc), spoken)
            tx.setdefault(f"iv{k}", {})[lang] = spoken
        cap[lang] = dict(title=v1[lang]["title"], tags=TAGS[lang], subs=[[c for _, c in sc] for sc in scenes],
                         credits_head=v1[lang]["credits_head"], changes=v1[lang]["changes"], links=v1[lang]["links"], music=v1[lang]["music"],
                         ambient=dict(en="Ambience", es="Ambiente", hi="परिवेश ध्वनि", pl="Dźwięki tła")[lang])
    json.dump(tx, open(ROOT / "tts/texts.json", "w"), ensure_ascii=False, indent=1)
    json.dump(cap, open(ROOT / "india/captions_v2.json", "w"), ensure_ascii=False, indent=1)
    print("ok", [len(cap[l]["subs"]) for l in cap])
