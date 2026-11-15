"""Film #1, wersja 3 — jedno źródło prawdy (skrypt 3.0 użytkownika + poprawki po weryfikacji faktów).

Układ: zimny start (Machu Picchu 1912) -> teza na klipie z wybrzeżem -> obietnica z czterema stemplami
-> 4 miejsca -> mid-roll (8 kropek) -> 3 miejsca -> payoff Machu Picchu (pętla) -> podsumowanie 4/2/1/1 + CTA.
Siedem mechanizmów: skala, pora dnia, wydarzenie, wybór, wysokość, pogoda, czas (Wielki Kanion = powtórka skali,
oznaczona ↺ i bez zwiększania licznika).

Składnia tekstu: [[napis||mowa]] — napis (cyfry, poprawna pisownia) do podpisu, mowa do syntezatora.
Zdania PL i EN muszą mieć tę samą liczbę (sprawdza make_texts3.py). Zdania nie mogą zawierać wewnętrznych . ! ? .

Zmiany względem skryptu 3.0 (powód: fakt nieweryfikowalny lub sprzeczność wewnętrzna):
 - licznik werdyktów 4/2/1/1 (skrypt miał „trzy razy rzeczywistość większa” — są dwa);
 - mid-roll: „cztery przed nami”, nie „dwa ostatnie”;
 - Gokyo: klip źródłowy NIE zawiera ludzi — dwie postacie są na zdjęciu CC BY, więc to ono dostaje pierścień;
 - Wielki Kanion: klip nie zawiera człowieka (gałąź, mgła) — człowiek jest na zdjęciach z szlaku Bright Angel;
 - usunięte, bo niezweryfikowane: „>80 erupcji”, „czerwona przez godzinę”, „za dwadzieścia szósta”, „jedna szósta”,
   „największy kanion Ameryki Północnej”, „sto lat konserwacji”, „4500 osób dziennie” (Wikipedia: ok. 4100 w 2025),
   „Wyższe niż większość Europy”, „Ama Dablam nad nimi”, „czekał na wieczór”, „woda do pływania”;
 - wspomnienia pierwszoosobowe („stałem tam”) zastąpione opinią bez zmyślonych przeżyć.
"""
import re

SRC = {
    "id": "eCtUQp9aISc",
    "title": "The 10 Most Beautiful Places I've ever Visited!",
    "author": "Ryan Van Duzer",
    "url": "https://www.youtube.com/watch?v=eCtUQp9aISc",
    "license": "Creative Commons Attribution license (reuse allowed)",
}

# okna oryginału (s źródła). coast: ujęcie z wybrzeża bez ludzi, cięcia wykryte ffmpeg scene na 501.58 i 503.29, brak do 512.
WINDOWS = {"coast": (503.4, 510.0), "machu": (279.0, 284.25), "nepal": (163.86, 170.66), "utah": (322.9, 329.75),
           "fuego": (385.5, 391.55), "copper": (403.0, 410.0), "burning": (595.4, 602.3),
           "grand": (663.95, 670.8), "ometepe": (721.7, 728.7)}

VERDICT = {  # kod -> napis stempla, kolor
    "W": {"pl": "KADR WYBIERA", "en": "THE FRAME CHOOSES", "rgb": (255, 196, 61)},
    "H": {"pl": "RZECZYWISTOŚĆ WIĘKSZA", "en": "REALITY IS BIGGER", "rgb": (92, 190, 255)},
    "U": {"pl": "UCZCIWY KADR", "en": "HONEST FRAME", "rgb": (86, 204, 130)},
    "B": {"pl": "LEPIEJ NIŻ W VLOGU", "en": "BETTER THAN THE VLOG", "rgb": (214, 140, 255)},
}

# ---------- zimny start ----------
HOOK1 = [("To jest [[Machu Picchu||Maczu Piczu]].", "This is Machu Picchu."),
         ("[[Rok 1912||Rok tysiąc dziewięćset dwunasty]].", "The year is [[1912||nineteen twelve]]."),
         ("Pole gruzu.", "A field of rubble.")]
HOOK2 = [("A to też jest [[Machu Picchu||Maczu Piczu]].", "And this is also Machu Picchu."),
         ("To samo miejsce.", "The same place."),
         ("Różni je jedna decyzja.", "One decision apart.")]
HOOK3 = [("Każdy vlog podróżniczy pokazuje tę drugą wersję.", "Every travel vlog shows you the second version."),
         ("I nikt tu nie kłamie.", "And nobody is lying to you.")]

# obietnica: zdania 5..8 = cztery stemple (W, H, U, B)
HOOK4 = [("Kadr nie kłamie.", "A frame does not lie."),
         ("Kadr wybiera.", "A frame chooses."),
         ("Osiem miejsc z jednego vloga na licencji [[Creative Commons||Kriejtiw Komons]].", "Eight places, from one Creative Commons vlog."),
         ("Siedem sposobów, na jakie kadr zmienia świat.", "Seven ways a frame changes the world."),
         ("Każde miejsce dostaje wyrok, a ja mam tylko cztery.", "Every place gets a verdict, and I only have four."),
         ("Kadr wybiera.", "The frame chooses."),
         ("Rzeczywistość jest większa.", "Reality is bigger."),
         ("Uczciwy kadr.", "Honest frame."),
         ("A czwarty jest tym, którego nikt się nie spodziewa: lepiej niż w vlogu.", "And the fourth is the one nobody expects, better than the vlog."),
         ("Siedem z tych ośmiu miejsc dostaje jeden z trzech pierwszych wyroków.", "Seven of these eight get one of the first three."),
         ("Jedno dostaje czwarty.", "One gets the fourth."),
         ("Które, powiem na końcu.", "I will tell you which at the end.")]
HOOK4_STAMPS = [("W", 5), ("H", 6), ("U", 7), ("B", 8)]

# ---------- rozdziały ----------
# a: lektor na fragmencie oryginału; b: lektor na zdjęciach; shots: (zdjęcie, [zdania b], klucz ruchu lub None)
# chip: ("a"|"b", indeks zdania, w którym padają słowa „mechanizm …”); vi: zdanie werdyktu w b; ring: pierścień na zdjęciu
CH = [
 {"id": "nepal", "mech": {"pl": "SKALA", "en": "SCALE"}, "n": 1, "verdict": "H", "chip": ("a", 0), "vi": 7,
  "name": {"pl": "Region Everestu, Nepal", "en": "Everest region, Nepal"},
  "a": [("Mechanizm pierwszy to skala.", "Mechanism one: scale."),
        ("Znajdź w tym kadrze człowieka.", "Find a person in this frame."),
        ("Nie ma tu nikogo.", "There is nobody.")],
  "b": [("To jest Ama Dablam.", "This is [[Ama Dablam||[Ama Dablam](/ˈɑmɑ dˈɑblɑm/)]]."),
        ("Ma [[6812 m||sześć tysięcy osiemset dwanaście metrów]].", "It is [[6,812 metres||six thousand eight hundred twelve metres]] high."),
        ("A to jeziora [[Gokyo||Gokjo]].", "And these are the [[Gokyo||[Gokyo](/ɡˈOkjO/)]] Lakes."),
        ("To park narodowy [[Sagarmatha||Sagarmata]] w Nepalu.", "[[Sagarmatha||[Sagarmatha](/sɑɡˈɑɹmɑtɑ/)]] National Park, Nepal."),
        ("Teraz znajdź na zboczu dwie malutkie postacie.", "Now find the two tiny figures on the slope."),
        ("To jest prawdziwa skala.", "That is the real scale."),
        ("Góra bez człowieka to tapeta.", "A mountain with no one in it is wallpaper."),
        ("Wyrok: rzeczywistość jest większa.", "Verdict: reality is bigger."),
        ("Moim zdaniem vlog niedoceniał tego miejsca, bo ekran telefonu nie pokaże wysokości.",
         "My read: the vlog undersold this place, because a phone screen cannot show you altitude.")],
  "shots": [("nepal1", [0, 1], None), ("nepal3", [2, 3, 4, 5, 6], None), ("nepal3", [7, 8], "nepal3~2")],
  "ring": {"photo": "nepal3", "xy": (0.70, 0.78), "from": 4, "to": 6},
  "pops": {1: ("6812 m", "6,812 m"), 4: ("2 postacie", "2 figures")},
  "sources": ["https://en.wikipedia.org/wiki/Ama_Dablam", "https://en.wikipedia.org/wiki/Gokyo_Lakes"]},

 {"id": "utah", "mech": {"pl": "PORA DNIA", "en": "HOUR"}, "n": 2, "verdict": "W", "chip": ("b", 4), "vi": 7,
  "name": {"pl": "White Rim Road, Utah", "en": "White Rim Road, Utah"},
  "a": [("Dwóch rowerzystów, czerwona skała.", "Two cyclists, a red mesa."),
        ("To droga [[White Rim||Łajt Rim]] w [[Canyonlands||Kanion Lends]], w [[Utah||Jutah]].", "This is White Rim, in Canyonlands, Utah.")],
  "b": [("[[71 mil||Siedemdziesiąt jeden mil]] nieutwardzonej drogi.", "[[71 miles||Seventy-one miles]] of unpaved road."),
        ("Zbudowano ją w [[latach 50.||latach pięćdziesiątych]], żeby poszukiwacze mogli dojechać do uranu.", "It was built in the [[1950s||nineteen fifties]], so prospectors could reach uranium."),
        ("Ten kadr niczego nie ukrywa.", "This frame hides nothing."),
        ("Po prostu słońce stoi nisko.", "The sun is simply low."),
        ("Mechanizm drugi: pora dnia.", "Mechanism two: hour."),
        ("Przy niskim słońcu czerwona skała robi się czerwieńsza.", "Low sun turns red rock redder."),
        ("W południe ta sama droga potrafi wyglądać płasko i blado.", "At noon the same road can look flat and pale."),
        ("Wyrok: kadr wybiera.", "Verdict: the frame chooses."),
        ("Moim zdaniem złota godzina stała się wymówką.", "My read: golden hour has become an excuse."),
        ("Przestaliśmy pytać, jak wygląda miejsce, a zaczęliśmy pytać, jak wygląda oświetlone.",
         "We stopped asking what a place looks like, and started asking what it looks like lit.")],
  "shots": [("utah1", [0, 1, 2, 3], None), ("utah3", [4, 5, 6], None), ("utah1", [7, 8, 9], "utah1~2")],
  "pops": {0: ("71 mil", "71 miles"), 1: ("lata 50.", "1950s")},
  "sources": ["https://en.wikipedia.org/wiki/White_Rim_Road"]},

 {"id": "fuego", "mech": {"pl": "WYDARZENIE", "en": "EVENT"}, "n": 3, "verdict": "W", "chip": ("b", 4), "vi": 6,
  "name": {"pl": "Wulkan Fuego, Gwatemala", "en": "Fuego volcano, Guatemala"},
  "a": [("Wulkan Fuego w Gwatemali.", "That is Fuego, in Guatemala."),
        ("I naprawdę jest aktywny.", "And it really is active.")],
  "b": [("Małe wybuchy zdarzają się [[co 15–20 minut||co piętnaście do dwudziestu minut]].", "Small explosions come [[every 15–20 minutes||every fifteen to twenty minutes]]."),
        ("Większe erupcje zdarzają się rzadziej.", "Larger eruptions are rarer."),
        ("A tak wygląda ten wulkan nocą, w [[listopadzie 2017||listopadzie dwa tysiące siedemnastego]].", "And this is the volcano at night, in [[November 2017||November twenty seventeen]]."),
        ("Satelita uchwycił smugę popiołu [[1 lutego 2018||pierwszego lutego dwa tysiące osiemnastego]].", "A satellite caught the ash plume on [[1 February 2018||the first of February twenty eighteen]]."),
        ("Mechanizm trzeci: wydarzenie.", "Mechanism three: event."),
        ("Kadr łapie wybuch i pozwala mu udawać całą górę.", "A frame catches the blast and lets it stand for the whole mountain."),
        ("Wyrok: kadr wybiera.", "Verdict: the frame chooses."),
        ("Moim zdaniem filmowanie erupcji nie jest nieuczciwe.", "My read: filming an eruption is not dishonest."),
        ("Nieuczciwe jest nazywanie tego krajobrazem.", "Calling it a landscape is.")],
  "shots": [("fuego1", [0, 1, 2], None), ("fuego3", [3, 4, 5], None), ("fuego3", [6, 7, 8], "fuego3~2")],
  "pops": {0: ("co 15–20 min", "every 15–20 min"), 3: ("1 II 2018", "1 Feb 2018")},
  "sources": ["https://en.wikipedia.org/wiki/Volc%C3%A1n_de_Fuego"]},

 {"id": "copper", "mech": {"pl": "WYBÓR", "en": "CHOICE"}, "n": 4, "verdict": "H", "chip": ("b", 4), "vi": 7,
  "name": {"pl": "Kanion Miedziany, Meksyk", "en": "Copper Canyon, Mexico"},
  "a": [("Punkt widokowy i jeden stok.", "A viewpoint and one slope."),
        ("Czy to cały Kanion Miedziany?", "Is this the whole Copper Canyon?"),
        ("Nie, to jeden kawałek.", "No, it is one piece.")],
  "b": [("Kanion Miedziany to nie jeden kanion.", "Copper Canyon is not one canyon."),
        ("[[To system 6 kanionów||To system sześciu kanionów]].", "[[It is a system of 6 canyons||It is a system of six canyons]]."),
        ("[[Wyżłobiło je 6 rzek||Wyżłobiło je sześć rzek]].", "[[Six rivers cut them||Six rivers cut them]]."),
        ("To [[Sierra Madre Zachodnia||Sjerra Madre Zachodnia]], północno-zachodni Meksyk.", "That is the [[Sierra Madre Occidental||[Sierra](/siˈɛɹə/) [Madre](/mˈɑdɹA/) Occidental]], in northwestern Mexico."),
        ("Mechanizm czwarty: wybór.", "Mechanism four: choice."),
        ("Vlog stanął na jednym punkcie widokowym.", "The vlog stood at one viewpoint."),
        ("Vlog pokazał jeden stok systemu o powierzchni [[65 000 km²||sześćdziesięciu pięciu tysięcy kilometrów kwadratowych]].", "The vlog showed one slope of a system covering [[65,000 km²||sixty-five thousand square kilometres]]."),
        ("Wyrok: rzeczywistość jest większa.", "Verdict: reality is bigger."),
        ("Moim zdaniem punkt widokowy daje stok, a nie system.", "My read: a viewpoint gives you a slope, not a system.")],
  "shots": [("copper1", [0, 1, 2, 3], None), ("copper2", [4, 5, 6], None), ("copper2", [7, 8], "copper2~2")],
  "schema": {"from": 5, "to": 6},
  "pops": {1: ("6 kanionów", "6 canyons"), 6: ("65 000 km²", "65,000 km²")},
  "sources": ["https://en.wikipedia.org/wiki/Copper_Canyon"]},

 {"id": "burning", "mech": {"pl": "WYSOKOŚĆ", "en": "HEIGHT"}, "n": 5, "verdict": "W", "chip": ("b", 4), "vi": 8,
  "name": {"pl": "Black Rock City, Nevada", "en": "Black Rock City, Nevada"},
  "a": [("Z drona: miasto narysowane linijką.", "From a drone: a city drawn with a ruler."),
        ("To [[Black Rock City||Blek Rok Siti]] w Nevadzie.", "This is Black Rock City, in Nevada.")],
  "b": [("[[W 2019 roku miało 78 850 uczestników||W dwa tysiące dziewiętnastym roku miało siedemdziesiąt osiem tysięcy osiemset pięćdziesięciu uczestników]].",
         "In 2019 it had [[78,850 participants||seventy-eight thousand eight hundred fifty participants]]."),
        ("Przez dziewięć dni, na pustyni.", "For nine days, in a desert."),
        ("Teraz zejdź na ziemię.", "Now come down to the ground."),
        ("Pył wszędzie, miasto z wysokości roweru.", "Dust everywhere, the city at bicycle height."),
        ("Mechanizm piąty: wysokość.", "Mechanism five: height."),
        ("Z góry widać plan.", "From above you see a plan."),
        ("I ten plan jest prawdziwy, bo miasto zaprojektowano.", "And the plan is real, because the city is designed."),
        ("Z ziemi widać pył.", "From the ground you see dust."),
        ("Wyrok: kadr wybiera.", "Verdict: the frame chooses."),
        ("Moim zdaniem zdjęcie z drona to lepsza fotografia i gorsza prawda.", "My read: the drone shot is the better photograph and the worse truth.")],
  "shots": [("burning1", [0, 1], None), ("burning3", [2, 3, 4], None), ("burning1", [5, 6], "burning1~2"), ("burning3", [7, 8, 9], "burning3~2")],
  "pops": {0: ("78 850", "78,850")},
  "sources": ["https://en.wikipedia.org/wiki/Burning_Man"]},

 {"id": "ometepe", "mech": {"pl": "POGODA", "en": "WEATHER"}, "n": 6, "verdict": "B", "chip": ("b", 4), "vi": 7,
  "name": {"pl": "Wyspa Ometepe, Nikaragua", "en": "Ometepe Island, Nicaragua"},
  "a": [("Jedna wyspa, dwa wulkany.", "One island, two volcanoes."),
        ("To Ometepe na jeziorze Nikaragua.", "This is [[Ometepe||[Ometepe](/ˌOmɛtˈɛpA/)]], in Lake Nicaragua.")],
  "b": [("[[Concepción||Konsepsjon]] i [[Maderas||Maderas]] łączy niski przesmyk.", "Concepción and [[Maderas||[Maderas](/mɑdˈɛɾɑs/)]] are joined by a low isthmus."),
        ("[[Concepción||Konsepsjon]] jest aktywny, ze stożkiem jak z podręcznika.", "Concepción is the active one, with a textbook cone."),
        ("[[Maderas||Maderas]] ma jezioro w kraterze, wśród lasu deszczowego.", "[[Maderas||[Maderas](/mɑdˈɛɾɑs/)]] has a crater lake, in rainforest."),
        ("W vlogu górę zasłania chmura.", "In the vlog, cloud covers the mountain."),
        ("Mechanizm szósty: pogoda.", "Mechanism six: weather."),
        ("Chmura decyduje, ile stożka zobaczysz.", "Cloud decides how much of the cone you get."),
        ("A tak wygląda ten wulkan w pogodny dzień.", "And this is the volcano on a clear day."),
        ("Wyrok: lepiej niż w vlogu.", "Verdict: better than the vlog."),
        ("Moim zdaniem tu rzeczywistość pokonała vloga.", "My read: here the place beat its vlog."),
        ("Jeśli któreś z tych miejsc jest warte podróży, to właśnie to.", "If any place on this list is worth the trip, it is this one.")],
  "shots": [("ometepe2", [0, 1, 2], None), ("ometepe3", [3, 4, 5], None), ("ometepe1", [6, 7, 8, 9], None)],
  "pops": {},
  "sources": ["https://en.wikipedia.org/wiki/Ometepe"]},

 {"id": "grand", "mech": {"pl": "SKALA, ZNOWU", "en": "SCALE, AGAIN"}, "n": 7, "repeat": True, "verdict": "U", "chip": ("b", 5), "vi": 6,
  "name": {"pl": "Wielki Kanion, Arizona", "en": "Grand Canyon, Arizona"},
  "a": [("Ponad milę w głąb.", "Over a mile deep."),
        ("To jedyna liczba, której tu potrzeba.", "That is the only number you need.")],
  "b": [("Ten kadr niczego nie upiększa.", "This frame does not prettify anything."),
        ("Mgła, gałąź, żadnego zachodu słońca.", "Haze, a branch, no sunset."),
        ("Brakuje w nim tylko człowieka.", "Only a person is missing."),
        ("Trasa [[Bright Angel||Brajt Endżel]] to wąska linia zakosów na ścianie.", "The Bright Angel Trail is a thin line of switchbacks on the wall."),
        ("A o zachodzie słońca jeden turysta pokazuje skalę.", "At sunset, a single hiker shows the scale."),
        ("To znowu mechanizm pierwszy: skala.", "That is mechanism one again: scale."),
        ("Wyrok: uczciwy kadr.", "Verdict: honest frame."),
        ("Moim zdaniem właśnie surowość czyni go uczciwym.", "My read: its plainness is what makes it honest."),
        ("Mniej ładny, bardziej prawdziwy.", "Less pretty, more true.")],
  "shots": [("grand2", [0, 1], None), ("grand1", [2, 3], None), ("grand3", [4, 5, 6], None), ("grand3", [7, 8], "grand3~2")],
  "pops": {},
  "sources": ["https://en.wikipedia.org/wiki/Grand_Canyon"]},

 # payoff: pre (zdjęcie 1912) -> a (klip) -> karta -> b (dziś, werdykt)
 {"id": "machu", "mech": {"pl": "CZAS", "en": "TIME"}, "n": 8, "last": True, "verdict": "W", "chip": ("b", 0), "vi": 6,
  "name": {"pl": "Machu Picchu, Peru", "en": "Machu Picchu, Peru"},
  "pre": [("Wróćmy do pierwszej sekundy tego filmu.", "Back to the first second of this film."),
          ("To zdjęcie zrobił w [[1912 roku||tysiąc dziewięćset dwunastym roku]] Hiram Bingham.", "Hiram Bingham took this photo in [[1912||nineteen twelve]]."),
          ("Po oczyszczeniu terenu, a przed rekonstrukcją.", "After the clearing, before the reconstruction.")],
  "a": [("A tak to miejsce wygląda w vlogu.", "And this is the place in the vlog."),
        ("Nie widać tu tłumu.", "No crowd in sight.")],
  "b": [("Mechanizm siódmy: czas.", "Mechanism seven: time."),
        ("Renowacja trwała od [[1929 do 1971||tysiąc dziewięćset dwudziestego dziewiątego do tysiąc dziewięćset siedemdziesiątego pierwszego]].", "Restoration work ran from [[1929 to 1971||nineteen twenty-nine to nineteen seventy-one]]."),
        ("Vlog pokazuje miejsce po tych pracach.", "The vlog shows the place after that work."),
        ("I to nadal jest wybór.", "And it is still a choice."),
        ("[[W 2025 roku przyjęło około 4100 gości dziennie||W dwa tysiące dwudziestym piątym roku przyjęło około czterech tysięcy stu gości dziennie]].", "In 2025 it received about [[4,100 visitors a day||forty-one hundred visitors a day]]."),
        ("A w vlogu prawie nikogo nie widać.", "And in the vlog there is hardly anyone."),
        ("Wyrok: kadr wybiera.", "Verdict: the frame chooses."),
        ("Moim zdaniem największe wrażenie robi to, że to miejsce w ogóle stoi.", "My read: the most impressive thing is that this place stands at all.")],
  "shots": [("machu3", [0, 1, 2], None), ("machu1", [3, 4, 5], None), ("machu1", [6, 7], "machu1@h2")],
  "pops": {1: ("1929–1971", "1929–1971"), 4: ("4100 / dzień", "4,100 / day")},
  "sources": ["https://en.wikipedia.org/wiki/Machu_Picchu"]},
]
CH_BY = {c["id"]: c for c in CH}
ORDER = ["nepal", "utah", "fuego", "copper", "burning", "ometepe", "grand", "machu"]  # kolejność w filmie (mid-roll po czwartym)

# mid-roll po czterech miejscach
MID = [("Cztery miejsca za nami, cztery przed nami.", "Four places down, four to go."),
       ("Jeśli planujesz sprawdzić któreś z nich na własne oczy, zapisz ten film teraz.", "If you plan to check any of these yourself, save this video now."),
       ("Z czterech pozostałych tylko jedno pokonało własny vlog.", "Among the next four is the only place that beat its own vlog."),
       ("Jest też miejsce ze zdjęcia z pierwszej sekundy tego filmu.", "Another is the place from the photograph in the first second of this film.")]
MID_SHORT = {"nepal": "Gokyo", "utah": "White Rim", "fuego": "Fuego", "copper": "Copper Canyon"}

# ---------- zakończenie ----------
OUTRO = [("Podsumujmy.", "Let's count."),
         ("Cztery razy kadr wybierał.", "Four times the frame chose."),
         ("Dwa razy rzeczywistość była większa.", "Twice reality was bigger."),
         ("Jeden raz kadr był uczciwy.", "Once the frame was honest."),
         ("I raz miejsce pokonało własny vlog.", "And once the place beat its own vlog."),
         ("Chodzi o Ometepe, jeśli ktoś liczył punkty.", "That is [[Ometepe||[Ometepe](/ˌOmɛtˈɛpA/)]], if you were keeping score."),
         ("Vlog nie kłamie.", "A vlog does not lie."),
         ("Vlog kadruje.", "A vlog frames."),
         ("Jedyne pytanie, które się liczy, brzmi: na jaki kadr patrzysz.", "The only question worth asking is which frame you are looking at."),
         ("Teraz znasz ich siedem.", "And now you have seven of them."),
         ("Napisz w komentarzu, które z tych ośmiu miejsc znasz osobiście i czy wyrok się zgadza.", "Tell me in the comments which of these eight places you have seen yourself, and whether the verdict holds."),
         ("A jeśli chcesz następny film, o miejscach, które wyglądają lepiej niż w vlogu, podaj nazwę miejsca.", "And if you want the next one, places that look better than the vlog, name the place."),
         ("Zrobię ten, który dostanie najwięcej głosów.", "I will make the one that gets the most votes.")]
OUTRO_TALLY = [("W", 1), ("H", 2), ("U", 3), ("B", 4)]

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
