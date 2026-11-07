"""Sondy: czy transkrypt Whispera zawiera daną liczbę, ułamek lub jednostkę (w formie cyfrowej albo słownej).
PROBES[tekst] = lista (etykieta, {język: [regex, ...]}), dopasowanie do transkryptu zapisanego małymi literami."""

def P(label, en, es, hi, pl):
    return (label, {"en": en, "es": es, "hi": hi, "pl": pl})

HUN = "(दशमलव|पॉइंट|प्वाइंट|पॉइन्ट|दशम)"
T2 = [
 P("17-inch", [r"17[- ]inch", r"seventeen[- ]inch"], [r"17 pulgadas", r"diecisiete pulgadas"], [r"17 इंच", r"सत्र\w* इंच", r"17[- ]inch"], [r"17[- ]cal", r"siedemnastocal", r"17 cali"]),
 P("199.5", [r"199\.5", r"ninety[- ]nine point five"], [r"199[,.]5", r"noventa y nueve (coma|punto) cinco"], [r"199[.,]5", r"(निन्यान|नियान)\w* " + HUN, r"(निन्यान|नियान)\w* (पाँच|पांच|पाथ)"], [r"199[,.]5", r"dziewięćdziesiąt dziewięć (przecinek|i) pięć"]),
 P("cc", [r"\bc ?c\b", r"cubic cent", r"cm ?3|cm³"], [r"\bc ?c\b", r"centímetros cúbicos", r"cm ?3|cm³", r"ce ce"], [r"सीसी", r"\bcc\b", r"c ?c\b", r"सेंटीमीटर|सेमी|क्यूबिक"], [r"\bc ?c\b", r"ce ce", r"cm ?3|cm³", r"centymetr"]),
 P("100/80-17", [r"100[/ -]+80[/ -]+17", r"100 (over|slash|by) 80", r"hundred (over|slash|by|and) eighty"], [r"100[/ -]+80[/ -]+17", r"100 barra 80", r"cien (sobre|entre|barra)? ?ochenta"], [r"100[/ -]+80[/ -]+17", r"(100|एक स[ोौ]).{0,20}(80|अस्सी).{0,25}(17|सत्र)"], [r"100[/ -]+80[/ -]+17", r"sto (na|przez|slash|ukośnik)? ?osiemdziesiąt"]),
 P("130/70-17", [r"130[/ -]+70[/ -]+17", r"130 (over|slash|by) 70", r"thirty (over|slash|by|and) seventy"], [r"130[/ -]+70[/ -]+17", r"130 barra 70", r"ciento treinta (sobre|entre|barra)? ?setenta"], [r"130[/ -]+70[/ -]+17", r"(130|एक स[ोौ] तीस).{0,20}(70|सत्तर).{0,25}(17|सत्र)"], [r"130[/ -]+70[/ -]+17", r"sto trzydzieści (na|przez|slash|ukośnik)? ?siedemdziesiąt"]),
 P("Rouser NS200", [r"rouser"], [r"rouser"], [r"rouser", r"राउज़र|राउसर|रौज़र|राऊज़र|वाउसर|रौसर"], [r"rouser"]),
 P("NS200", [r"ns ?200", r"n s (200|two hundred)"], [r"ns ?200", r"ene ese (200|doscientos)"], [r"ns ?200", r"(एन|इन) ?(एस|स) ?(200|दो सौ)", r"इनस ?200"], [r"ns ?200", r"en es (200|dwieście)"]),
 P("DTS-i", [r"dts[- ]?i", r"d ?t ?s[- ]?i"], [r"dts[- ]?i", r"d ?t ?s[- ]?i"], [r"dts[- ]?i", r"d ?t ?s[- ]?i", r"डीटीएस"], [r"dts[- ]?i", r"d ?t ?s[- ]?i"]),
 P("2014", [r"2014", r"twenty fourteen", r"two thousand (and )?fourteen"], [r"2014", r"dos mil catorce"], [r"2014", r"दो ह[ज़ज]ार चौदह"], [r"2014", r"dwa tysiące czternast"]),
 P("7 October", [r"7 oct", r"7th of oct", r"october 7", r"seventh of oct"], [r"7 de octubre", r"siete de octubre"], [r"7 अक्टूबर", r"सात अक्टूबर"], [r"7 października", r"siódmego października"]),
 P("2026", [r"2026", r"twenty twenty[- ]six", r"two thousand (and )?twenty[- ]six"], [r"2026", r"dos mil veintiséis"], [r"2026", r"दो ह[ज़ज]ार छब्बीस"], [r"2026", r"dwa tysiące dwudziest"]),
 P("CC0", [r"cc ?0", r"c c (zero|0)", r"creative commons (zero|0)"], [r"cc ?0", r"c c (cero|0)", r"ce ce cero"], [r"cc ?0", r"सी ?सी ?(0|ज़ीरो|जीरो|शून्य)"], [r"cc ?0", r"ce ce (zero|0)"]),
]
T3 = [
 P("199.5", T2[1][1]["en"], T2[1][1]["es"], T2[1][1]["hi"], T2[1][1]["pl"]),
 P("cm³", [r"cubic cent", r"cm ?3|cm³", r"\bc ?c\b"], [r"centímetros cúbicos", r"cm ?3|cm³", r"\bc ?c\b"], [r"सेंटीमीटर|सेमी|\bcm\b|cm ?3|सीसी|क्यूबिक"], [r"centymetr\w* sześcien", r"cm ?3|cm³", r"\bc ?c\b"]),
 P("1/5", [r"1/5", r"one[- ]fifth", r"a fifth", r"one over five"], [r"1/5", r"un quinto", r"uno (entre|sobre) cinco"], [r"1 ?/ ?5", r"(एक|1) (बटा|बटे) (पाँच|पांच|5)", r"पाँचवाँ|पांचवां|पाँचवा|पांचवा", r"(पाँच|पांच|5) में से (एक|1)"], [r"1/5", r"jedn\w+ piąt\w+", r"jeden na pięć"]),
 P("24.5", [r"24\.5", r"twenty[- ]four point five"], [r"24[,.]5", r"veinticuatro (coma|punto) cinco"], [r"24[.,]5", r"चौबीस " + HUN], [r"24[,.]5", r"dwadzieścia cztery (przecinek|i) pięć"]),
 P("PS", [r"\bps\b", r"p s\b", r"horsepower", r"pferdest", r"metric horse"], [r"\bps\b", r"p s\b", r"caballos", r"\bcv\b"], [r"पी ?एस", r"\bps\b", r"हॉर्स ?पावर|अश्व"], [r"\bps\b", r"pe es", r"koni", r"\bkm\b"]),
 P("9,750", [r"9,?750", r"nine thousand,? seven hundred (and )?fifty"], [r"9\.?750", r"nueve mil setecientos cincuenta"], [r"9,?750", r"नौ ह[ज़ज]ार सात सौ पचास"], [r"9 ?750", r"dziewięć tysięcy siedemset pięćdziesiąt"]),
 P("rpm", [r"rpm", r"r p m", r"revolutions per minute", r"revs"], [r"rpm", r"r p m", r"revoluciones por minuto"], [r"rpm", r"आर ?पी ?एम", r"चक्कर|रोटेशन"], [r"obr", r"rpm", r"obrot", r"r p m"]),
 P("18.5", [r"18\.5", r"eighteen point five"], [r"18[,.]5", r"dieciocho (coma|punto) cinco"], [r"18[.,]5", r"अठारह " + HUN], [r"18[,.]5", r"osiemnaście (przecinek|i) pięć"]),
 P("N·m", [r"n·m", r"\bnm\b", r"n m\b", r"newton"], [r"n·m", r"\bnm\b", r"n m\b", r"newton"], [r"न्यूटन", r"\bnm\b", r"n·m", r"एन ?एम"], [r"niutonometr", r"newton", r"\bnm\b", r"n·m", r"n m\b"]),
 P("3 1/2", [r"3 1/2", r"three and (a )?(one[- ])?half", r"3\.5", r"three point five"], [r"3 1/2", r"tres y medio", r"tres galones y medio", r"3,5", r"tres coma cinco"], [r"3 1/2", r"साढ़े तीन|साढे तीन|साडे तीन", r"3[.,]5"], [r"3 1/2", r"trzy i pół", r"trzy i jedna druga", r"3,5", r"trzy przecinek pięć"]),
 P("13 L", [r"13 ?l\b", r"thirteen lit", r"13 lit"], [r"13 ?l\b", r"trece litros", r"13 litros"], [r"13 ?l\b", r"तेरह लीटर|13 लीटर"], [r"13 ?l\b", r"trzynaście litr|13 litr"]),
 P("150 kg", [r"150 ?kg", r"hundred (and )?fifty (kilo|k)"], [r"150 ?kg", r"ciento cincuenta kilo"], [r"150 ?kg|150 किलो|डेढ़ सौ|एक सौ पचास"], [r"150 ?kg", r"sto pięćdziesiąt kilo"]),
 P("1.75", [r"1\.75", r"one point (seven five|seventy[- ]five)"], [r"1[,.]75", r"uno (coma|punto) (setenta y cinco|siete cinco)"], [r"1\.75", r"एक " + HUN + r" (सात पांच|सात पाँच|पचहत्तर)"], [r"1[,.]75", r"jeden przecinek siedemdziesiąt pięć", r"jeden i siedemdziesiąt pięć"]),
 P("bar", [r"\bbar\b"], [r"\bbar\b"], [r"बार|\bbar\b"], [r"\bbar\w*"]),
 P("4.5 s", [r"4\.5", r"four point five"], [r"4[,.]5", r"cuatro (coma|punto) cinco"], [r"4\.5", r"साढ़े चार|साढे चार", r"चार " + HUN], [r"4[,.]5", r"cztery (przecinek pięć|i pół)"]),
 P("100 km/h", [r"100 ?(km|kph)", r"hundred (kilometers|kilometres|k)"], [r"100 ?(km|kph)", r"cien kil"], [r"100 ?(km|किमी|किलोमीटर)", r"सौ (किलोमीटर|किमी)"], [r"100 ?(km|kilometr)", r"sto kilometr"]),
 P("140 km/h", [r"140", r"hundred (and )?forty"], [r"140", r"ciento cuarenta"], [r"140", r"(एक )?सौ चालीस"], [r"140", r"sto czterdzieści"]),
 P("3/4", [r"3/4", r"three[- ]quarters", r"three fourths"], [r"3/4", r"tres cuartos", r"tres cuartas"], [r"3 ?/ ?4", r"तीन (चौथाई|बटा चार|बटे चार|चौथे)", r"पौन"], [r"3/4", r"trzy czwart\w+", r"trzech czwartych"]),
 P("20–25", [r"20.{0,8}25", r"twenty.{0,12}twenty[- ]five"], [r"20.{0,8}25", r"veinte.{0,12}veinticinco"], [r"20.{0,8}25", r"बीस.{0,12}पच्चीस"], [r"20.{0,8}25", r"dwadzieścia.{0,14}dwadzieścia pięć"]),
 P("°C", [r"°c", r"degrees", r"celsius"], [r"°c", r"grados", r"celsius"], [r"°c", r"डिग्री", r"सेल्सियस"], [r"°c", r"stopni", r"celsj", r"celsius"]),
 P("1 in 5", [r"1 in 5", r"one in five", r"one out of five", r"1 out of 5"], [r"1 de cada 5", r"uno de cada cinco"], [r"हर (5|पाँच|पांच) में से (1|एक)", r"(5|पाँच|पांच) में से (1|एक)"], [r"1 (jazda )?na (5|pięć)", r"jedn\w+ (jazda )?na (5|pięć)", r"co piąta"]),
]
T1 = [
 P("17-inch", T2[0][1]["en"], T2[0][1]["es"], T2[0][1]["hi"], T2[0][1]["pl"]),
 P("NS200", T2[6][1]["en"], T2[6][1]["es"], T2[6][1]["hi"], T2[6][1]["pl"]),
]
PROBES = {"t1": T1, "t2": T2, "t3": T3}
