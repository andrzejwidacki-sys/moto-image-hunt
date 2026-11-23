"""Film #4 — komentarz do „Top 10 places around Bangalore for a two days trip” (Sakre Cubes, CC BY).

Teza: autor podaje na ekranie kilometry („Distance: … km from Bangalore”), a weekend liczy się w godzinach.
Werdykt z godzin jazdy w obie strony (dane ze stron podróżniczych, bez postojów): do 11 h = mieści się,
do 15 h = na styk, więcej = za daleko. Werdykty są liczone z HOURS_ONE_WAY, nie wpisywane ręcznie.

Składnia tekstu: [[napis||mowa]] — napis (cyfry, poprawna pisownia) do podpisu, mowa do syntezatora.
Zdania PL i EN muszą mieć tę samą liczbę (sprawdza make_texts4.py). Zdania nie mogą zawierać wewnętrznych . ! ? .

Pominięte: Yercaud — cały fragment oryginału to cudze zdjęcia z podpisami „Image Credits”; Wayanad, Sakleshpur,
Udupi — poza zakresem (sześć miejsc z jednym motywem).
"""
import re

SRC = {
    "id": "VfDp6C1I-58",
    "title": "Top 10 places around Bangalore for a two days trip",
    "author": "Sakre Cubes",
    "url": "https://www.youtube.com/watch?v=VfDp6C1I-58",
    "license": "Creative Commons Attribution license (reuse allowed)",
}

# okna oryginału (s źródła); początek/koniec na granicach słów z ASR (koniec = koniec ostatniego słowa)
WINDOWS = {"pond": (29.10, 36.07), "coorg": (107.70, 113.62), "gok": (191.00, 197.94),
           "ooty": (282.84, 288.54), "chik": (352.79, 358.09), "mys": (590.56, 595.30)}

# godziny jazdy w jedną stronę (źródła w CH[..]["sources"]); progi w godzinach w obie strony
HOURS_ONE_WAY = {"pond": 7.0, "coorg": 5 + 10 / 60, "gok": 9.5, "ooty": 6.5, "chik": 4.5, "mys": 2.5}
FIT_MAX, TIGHT_MAX = 11.0, 15.0


def code_for(hours_one_way):
    rt = 2 * hours_one_way
    return "F" if rt <= FIT_MAX else ("T" if rt <= TIGHT_MAX else "N")


VERDICT = {
    "F": {"pl": "MIEŚCI SIĘ", "en": "IT FITS", "rgb": (86, 204, 130)},
    "T": {"pl": "NA STYK", "en": "TIGHT", "rgb": (255, 196, 61)},
    "N": {"pl": "ZA DALEKO", "en": "TOO FAR", "rgb": (255, 105, 97)},
}

# ---------- zimny start ----------
HOOK1 = [("Wypad na dwa dni do [[Gokarny||Gokarny]].", "A two-day trip to Gokarna."),
         ("Droga w jedną stronę: dziewięć i pół godziny.", "One way by road: nine and a half hours."),
         ("W obie strony: dziewiętnaście.", "Round trip: nineteen.")]
HOOK1_PHOTO = ("gok1", "gok1@h1")
HOOK1_POPS = {1: ("9,5 h", "9.5 h"), 2: ("19 h", "19 h")}

HOOK2 = [("A [[Mysuru||Majsuru]]?", "And [[Mysuru||[Mysuru](/maɪˈsuːɹuː/)]]?"),
         ("Dwie i pół godziny w jedną stronę.", "Two and a half hours each way."),
         ("Ten sam film obiecuje oba wypady na dwa dni.", "The same video promises both trips in two days.")]
HOOK2_PHOTO = ("mys1", "mys1@h2")
HOOK2_POPS = {1: ("2,5 h", "2.5 h")}

# obietnica: stemple na zdaniach 3, 4, 5
HOOK3 = [("Sześć miejsc z jednego filmu o wypadach z [[Bangalore||Bengaluru]].", "Six places from one video about trips out of Bangalore."),
         ("Autor podaje na ekranie kilometry.", "On screen, the author gives kilometres."),
         ("Ja liczę godziny w aucie, w obie strony.", "I count the hours in the car, both ways."),
         ("Do jedenastu godzin: mieści się.", "Up to eleven hours: it fits."),
         ("Do piętnastu: na styk.", "Up to fifteen: tight."),
         ("Więcej: za daleko.", "More: too far."),
         ("Ile z sześciu przejdzie ten test?", "How many of the six pass this test?"),
         ("Zaczynamy od [[Pondicherry||Pondiczeri]].", "We start with Pondicherry.")]
HOOK3_STAMPS = [("F", 3), ("T", 4), ("N", 5)]
PROMISE_BG = ["mys1", "gok1", "ooty1", "coorg2", "chik3", "pond1", "mys2", "pond3"]

# ---------- rozdziały ----------
# a: lektor na fragmencie oryginału; b: lektor na zdjęciach; shots: (zdjęcie, [zdania b], klucz ruchu lub None)
CH = [
 {"id": "pond", "n": 1, "km_author": 322, "name": {"pl": "Pondicherry", "en": "Pondicherry"},
  "a": [("[[Pondicherry||Pondiczeri]]: na ekranie [[322 km||trzysta dwadzieścia dwa kilometry]].", "Pondicherry: [[322 km||three hundred twenty-two kilometres]] on screen."),
        ("A ile to godzin?", "And how many hours is that?")],
  "b": [("Tak wygląda [[Promenade Beach||Promenejd Biecz]]: czarne głazy i fale.", "This is Promenade Beach: black boulders and surf."),
        ("W filmie był piasek i słomiane parasole.", "The video showed sand and thatched umbrellas."),
        ("A tu stare molo.", "And here, an old pier."),
        ("Ludzie kąpią się w morzu.", "People are swimming in the sea."),
        ("Dzielnica Francuska: dom z kolumnami i palmy.", "The French Quarter: a house with columns and palms."),
        ("[[Z Bangalore: około 300 km i 7 godzin||Z Bengaluru: około trzystu kilometrów i siedem godzin]].", "From Bangalore: about [[300 km and 7 hours||three hundred kilometres and seven hours]]."),
        ("W obie strony: czternaście godzin w aucie.", "Round trip: fourteen hours in the car."),
        ("Werdykt: na styk.", "Verdict: tight."),
        ("Moim zdaniem to wypad na trzy dni.", "My read: this is a three-day trip.")],
  "shots": [("pond1", [0, 1], None), ("pond2", [2, 3], None), ("pond3", [4, 5], None), ("pond1", [6, 7, 8], "pond1~2")],
  "vi": 7,
  "pops": {5: ("300 km · 7 h", "300 km · 7 h"), 6: ("14 h", "14 h")},
  "apop": {0: ("autor: 322 km", "author: 322 km")},
  "sources": ["https://www.savaari.com/blog/bangalore/bangalore-to-pondicherry/"]},

 {"id": "coorg", "n": 2, "km_author": 250, "name": {"pl": "Coorg (Kodagu)", "en": "Coorg (Kodagu)"},
  "a": [("[[Coorg||Kurg]]: na ekranie [[250 km||dwieście pięćdziesiąt kilometrów]].", "[[Coorg||[Coorg](/kʊɹɡ/)]]: [[250 km||two hundred fifty kilometres]] on screen."),
        ("Autor mówi: tylko.", "The author says: only.")],
  "b": [("To widok z [[Raja's Seat||Radżas Sit]] w [[Madikeri||Madikeri]].", "This is the view from [[Raja's Seat||[Raja's Seat](/ˈɹɑːdʒɑːz ˈsiːt/)]], in [[Madikeri||[Madikeri](/mɑːdɪˈkeɪɹi/)]]."),
        ("W filmie na wzgórzu była tylko mgła.", "In the video, the hilltop was all mist."),
        ("Tu też chmury wiszą nisko, ale widać dolinę.", "Here the cloud hangs low too, but you can see the valley."),
        ("[[Wodospad Abbey||Wodospad Abbi]]: osiem kilometrów od [[Madikeri||Madikeri]].", "Abbey Falls: eight kilometres from [[Madikeri||[Madikeri](/mɑːdɪˈkeɪɹi/)]]."),
        ("Woda spada kaskadami po skałach.", "The water drops in cascades down the rock."),
        ("Dachy [[Madikeri||Madikeri]], widziane z fortu.", "The rooftops of [[Madikeri||[Madikeri](/mɑːdɪˈkeɪɹi/)]], seen from the fort."),
        ("[[Z Bangalore: 264 km i 5 godzin 10 minut||Z Bengaluru: dwieście sześćdziesiąt cztery kilometry i pięć godzin dziesięć minut]].", "From Bangalore: [[264 km and 5 h 10 min||two hundred sixty-four kilometres and five hours ten minutes]]."),
        ("W obie strony: ponad dziesięć godzin.", "Round trip: over ten hours."),
        ("Werdykt: mieści się.", "Verdict: it fits."),
        ("Moim zdaniem to pierwsze miejsce, gdzie dwa dni mają sens.", "My read: the first place here where two days make sense.")],
  "shots": [("coorg1", [0, 1, 2], None), ("coorg2", [3, 4], None), ("coorg3", [5, 6, 7], None), ("coorg1", [8, 9], "coorg1~2")],
  "vi": 8,
  "pops": {6: ("264 km · 5 h 10", "264 km · 5 h 10"), 7: ("10 h 20", "10 h 20")},
  "apop": {0: ("autor: 250 km", "author: 250 km")},
  "sources": ["https://www.holidify.com/places/coorg/how-to-reach/bangalore-to-coorg-390.html", "https://en.wikipedia.org/wiki/Abbey_Falls"]},

 {"id": "gok", "n": 3, "km_author": 500, "name": {"pl": "Gokarna", "en": "Gokarna"},
  "a": [("[[Gokarna||Gokarna]]: na ekranie [[500 km||pięćset kilometrów]].", "Gokarna: [[500 km||five hundred kilometres]] on screen."),
        ("Zgadnij, ile to godzin.", "Guess the hours.")],
  "b": [("To plaża [[Kudle||Kudle]]: zatoka i sucha trawa na wzgórzu.", "This is [[Kudle||[Kudle](/ˈkuːdleɪ/)]] Beach: a bay and dry grass on the hill."),
        ("Autor obiecuje czyste, spokojne plaże.", "The author promises clean, quiet beaches."),
        ("Plaża przy świątyni w pochmurny dzień.", "The beach by the temple on a cloudy day."),
        ("Motocykle zamiast ciszy.", "Motorbikes instead of silence."),
        ("I zachód słońca nad morzem.", "And a sunset over the sea."),
        ("[[Z Bangalore: około 490 km||Z Bengaluru: około czterystu dziewięćdziesięciu kilometrów]].", "From Bangalore: [[about 490 km||about four hundred ninety kilometres]]."),
        ("Dziewięć i pół godziny w jedną stronę.", "Nine and a half hours one way."),
        ("Dziewiętnaście w obie strony.", "Nineteen both ways."),
        ("Z dwóch dni zostaje dwadzieścia dziewięć godzin.", "Out of two days, twenty-nine hours are left."),
        ("Werdykt: za daleko.", "Verdict: too far."),
        ("Moim zdaniem [[Gokarna||Gokarna]] to wypad na cztery dni.", "My read: Gokarna is a four-day trip.")],
  "shots": [("gok1", [0, 1], None), ("gok2", [2, 3], None), ("gok3", [4, 5, 6], None), ("gok1", [7, 8], "gok1~2"), ("gok3", [9, 10], "gok3~2")],
  "vi": 9,
  "pops": {5: ("490 km", "490 km"), 6: ("9,5 h", "9.5 h"), 7: ("19 h", "19 h"), 8: ("48 − 19 = 29 h", "48 − 19 = 29 h")},
  "apop": {0: ("autor: 500 km", "author: 500 km")},
  "sources": ["https://www.savaari.com/blog/bangalore/bangalore-to-gokarna/"]},

 {"id": "ooty", "n": 4, "km_author": 260, "name": {"pl": "Ooty (Udhagamandalam)", "en": "Ooty (Udhagamandalam)"},
  "a": [("[[Ooty||Uti]]: na ekranie [[260 km||dwieście sześćdziesiąt kilometrów]].", "[[Ooty||[Ooty](/ˈuːti/)]]: [[260 km||two hundred sixty kilometres]] on screen."),
        ("Plantacje herbaty, góry, jezioro.", "Tea plantations, mountains, a lake.")],
  "b": [("Tak wygląda [[Ooty||Uti]] z bliska: domy na zboczu i słupy energetyczne.", "This is [[Ooty||[Ooty](/ˈuːti/)]] up close: houses on a slope and power pylons."),
        ("W kadrze filmu była tylko herbata i góry.", "In the video's frame there was only tea and mountains."),
        ("A to przystań łodzi nad jeziorem.", "And this is the boat dock on the lake."),
        ("Autor sam ostrzega, że miasto może wydać się zbyt komercyjne.", "The author himself warns the town may feel too commercial."),
        ("Kolejka górska [[Nilgiri||Nilgiri]] należy do światowego dziedzictwa [[UNESCO||Unesko]].", "The Nilgiri Mountain Railway is a UNESCO World Heritage site."),
        ("[[Ooty leży na wysokości 2240 m||Uti leży na wysokości dwóch tysięcy dwustu czterdziestu metrów]].", "[[Ooty||[Ooty](/ˈuːti/)]] sits at [[2,240 metres||two thousand two hundred forty metres]]."),
        ("[[Z Bangalore: około 270 km i 6,5 godziny||Z Bengaluru: około dwustu siedemdziesięciu kilometrów i sześć i pół godziny]].", "From Bangalore: [[about 270 km and 6.5 hours||about two hundred seventy kilometres and six and a half hours]]."),
        ("W obie strony: trzynaście godzin.", "Round trip: thirteen hours."),
        ("Werdykt: na styk.", "Verdict: tight."),
        ("Moim zdaniem warto dołożyć trzeci dzień.", "My read: give it a third day.")],
  "shots": [("ooty1", [0, 1], None), ("ooty2", [2, 3], None), ("ooty3", [4, 5], None), ("ooty1", [6, 7, 8, 9], "ooty1~2")],
  "vi": 8,
  "pops": {5: ("2240 m", "2,240 m"), 6: ("270 km · 6,5 h", "270 km · 6.5 h"), 7: ("13 h", "13 h")},
  "apop": {0: ("autor: 260 km", "author: 260 km")},
  "sources": ["https://www.savaari.com/blog/bangalore/bangalore-to-ooty/", "https://en.wikipedia.org/wiki/Ooty"]},

 {"id": "chik", "n": 5, "km_author": 250, "name": {"pl": "Chikmagalur", "en": "Chikmagalur"},
  "a": [("[[Chikmagalur||Czikmagalur]]: na ekranie [[250 km||dwieście pięćdziesiąt kilometrów]].", "[[Chikmagalur||[Chikmagalur](/tʃɪkmɑːˈɡɑːlʊɹ/)]]: [[250 km||two hundred fifty kilometres]] on screen."),
        ("Kraina kawy.", "Coffee country.")],
  "b": [("[[Mullayanagiri||Mulajanagiri]], najwyższy szczyt [[Karnataki||Karnataki]]: [[1925 m||tysiąc dziewięćset dwadzieścia pięć metrów]].", "[[Mullayanagiri||[Mullayanagiri](/mʊlɑːjɑːnɑːˈɡɪɹi/)]], the highest peak in Karnataka: [[1,925 metres||nineteen hundred twenty-five metres]]."),
        ("Widok ze szczytu: równina w mgiełce.", "The view from the top: a plain under haze."),
        ("Autor porównał krajobrazy do tapety z Windowsa.", "The author compared the landscapes to a Windows wallpaper."),
        ("A tak wygląda mgła wśród wysokich drzew.", "And this is mist among tall trees."),
        ("[[Z Bangalore: 244 km i 4,5 godziny||Z Bengaluru: dwieście czterdzieści cztery kilometry i cztery i pół godziny]].", "From Bangalore: [[244 km and 4.5 hours||two hundred forty-four kilometres and four and a half hours]]."),
        ("W obie strony: dziewięć godzin.", "Round trip: nine hours."),
        ("Werdykt: mieści się.", "Verdict: it fits."),
        ("Moim zdaniem tu autor ma rację: dwa dni wystarczą.", "My read: here the author is right, two days are enough.")],
  "shots": [("chik2", [0, 1, 2], None), ("chik3", [3, 4], None), ("chik2", [5, 6, 7], "chik2~2")],
  "vi": 6,
  "pops": {0: ("1925 m", "1,925 m"), 4: ("244 km · 4,5 h", "244 km · 4.5 h"), 5: ("9 h", "9 h")},
  "apop": {0: ("autor: 250 km", "author: 250 km")},
  "sources": ["https://www.savaari.com/blog/bangalore/bangalore-to-chikmagalur/", "https://en.wikipedia.org/wiki/Mullayyanagiri"]},

 {"id": "mys", "n": 6, "km_author": 140, "name": {"pl": "Mysuru (Mysore)", "en": "Mysuru (Mysore)"},
  "a": [("[[Mysuru||Majsuru]]: [[140 km||sto czterdzieści kilometrów]].", "Mysuru: [[140 km||a hundred forty kilometres]]."),
        ("Najbliżej z sześciu.", "The closest of six.")],
  "b": [("Pałac w [[Mysuru||Majsuru]].", "The palace in Mysuru."),
        ("Autor: jeden z najczęściej odwiedzanych pałaców w Indiach.", "The author: one of the most visited palaces in India."),
        ("Fontanny w ogrodach [[Brindavan||Brindawan]] po zmroku.", "Fountains in Brindavan Gardens after dark."),
        ("Dla tych świateł warto zostać na noc.", "Those lights are worth staying the night for."),
        ("A za dnia: aleje i trawniki.", "And by day: paths and lawns."),
        ("[[Z Bangalore: 146 km i 2,5 godziny||Z Bengaluru: sto czterdzieści sześć kilometrów i dwie i pół godziny]].", "From Bangalore: [[146 km and 2.5 hours||a hundred forty-six kilometres and two and a half hours]]."),
        ("W obie strony: pięć godzin.", "Round trip: five hours."),
        ("Werdykt: mieści się.", "Verdict: it fits."),
        ("Moim zdaniem tu droga nie jest problemem.", "My read: here the road is not the problem.")],
  "shots": [("mys1", [0, 1], None), ("mys2", [2, 3], None), ("mys3", [4, 5], None), ("mys1", [6, 7, 8], "mys1~2")],
  "vi": 7,
  "pops": {5: ("146 km · 2,5 h", "146 km · 2.5 h"), 6: ("5 h", "5 h")},
  "apop": {0: ("autor: 140 km", "author: 140 km")},
  "sources": ["https://www.savaari.com/blog/bangalore/bangalore-to-mysore/"]},
]
CH_BY = {c["id"]: c for c in CH}
ORDER = [c["id"] for c in CH]
for c in CH:
    c["verdict"] = code_for(HOURS_ONE_WAY[c["id"]])

# ---------- zakończenie ----------
OUTRO = [("Podsumujmy.", "Let's count."),
         ("Trzy razy: mieści się.", "Three times: it fits."),
         ("Dwa razy: na styk.", "Twice: tight."),
         ("Raz: za daleko.", "Once: too far."),
         ("Autor podawał kilometry.", "The author gave kilometres."),
         ("Weekend liczy się w godzinach.", "A weekend is counted in hours."),
         ("Czasy dojazdu to wartości orientacyjne z serwisów podróżniczych, bez postojów.", "Drive times are rough figures from travel sites, without stops."),
         ("Teraz pytanie do ciebie.", "Now a question for you."),
         ("Ile godzin w aucie jest warte dwóch dni?", "How many hours in a car are two days worth?"),
         ("Napisz w komentarzu, które z tych sześciu miejsc znasz i ile tam jechałeś.", "Tell me in the comments which of the six you know, and how long it took you."),
         ("A następny film zrobię o miejscu, które dostanie najwięcej głosów.", "And the next video will be about the place that gets the most votes.")]
OUTRO_TALLY = [("F", 1), ("T", 2), ("N", 3)]

_RX = re.compile(r"\[\[(.*?)\|\|(.*?)\]\]")


def disp(t):
    return _RX.sub(lambda m: m.group(1), t)


def spoken(t):
    return _RX.sub(lambda m: m.group(2), t)


def tally():
    from collections import Counter
    return dict(Counter(ch["verdict"] for ch in CH))


if __name__ == "__main__":
    print(tally())
