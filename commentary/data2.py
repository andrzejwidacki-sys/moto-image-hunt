"""Film #1, wersja 2 (dynamiczna) — jedno źródło prawdy.

Zasady z audytu VidIQ (13.11.2026): zimny start (Machu Picchu 1912 od 0:00), brak noty licencyjnej w
mowie (stały podpis w rogu + opis), lektor mówi przez cały fragment oryginału, przerwy w mowie
<= 3 s, krótkie zdania, pytania, zero opisów obrazka ("na ekranie widać..."), teza i łuk
(siedem mechanizmów kadrowania), stempel-werdykt po każdym miejscu, wniosek na końcu.

Składnia tekstu: [[napis||mowa]] — napis (cyfry, poprawna pisownia) trafia do podpisu, mowa
(liczby słowami, zapis fonetyczny) do syntezatora. Tekst bez znaczników jest taki sam w obu.
Zdania PL i EN muszą mieć tę samą liczbę (sprawdza make_texts2.py).
"""
import re

SRC = {
    "id": "eCtUQp9aISc",
    "title": "The 10 Most Beautiful Places I've ever Visited!",
    "author": "Ryan Van Duzer",
    "url": "https://www.youtube.com/watch?v=eCtUQp9aISc",
    "license": "Creative Commons Attribution license (reuse allowed)",
}

# okna oryginału (s źródła). Machu: ujęcie cytadeli (chmury -> odsłonięcie), cięcia wykryte ffmpeg scene (278.90 i 284.37).
# Fuego: ucięte przed ujęciem twarzy autora (cięcie na 391.77).
WINDOWS = {"machu": (279.0, 284.25), "nepal": (163.86, 170.66), "utah": (322.9, 329.75),
           "fuego": (385.5, 391.55), "copper": (403.0, 410.0), "burning": (595.4, 602.3),
           "grand": (663.95, 670.8), "ometepe": (721.7, 728.7)}

VERDICT = {  # kod -> (napis na stemplu, kolor RGB)
    "U": {"pl": "UCZCIWY KADR", "en": "HONEST FRAME", "rgb": (86, 204, 130)},
    "W": {"pl": "KADR WYBIERA", "en": "THE FRAME CHOOSES", "rgb": (255, 196, 61)},
    "H": {"pl": "RZECZYWISTOŚĆ WIĘKSZA", "en": "REALITY IS BIGGER", "rgb": (92, 190, 255)},
}

# ---------- zimny start ----------
HOOK1 = [("To jest [[Machu Picchu||Maczu Piczu]].", "This is Machu Picchu."),
         ("[[Rok 1912||Rok tysiąc dziewięćset dwunasty]].", "The year is [[1912||nineteen twelve]]."),
         ("Pole gruzu.", "A field of rubble.")]
HOOK2 = [("A to też jest [[Machu Picchu||Maczu Piczu]].", "And this is also Machu Picchu."),
         ("To samo miejsce.", "The same place."),
         ("Ponad sto lat i jedna decyzja: co pokazać.", "Over a hundred years, and one decision: what to show.")]
HOOK3 = [("W każdym vlogu zobaczysz tę wersję.", "Every vlog shows you this version."),
         ("I nikt tu nie kłamie.", "And nobody is lying to you.")]
MECH_WORDS = {"pl": ["Czas", "Skala", "Zasięg", "Pora dnia", "Wybór", "Wysokość", "Pogoda"],
              "en": ["Time", "Scale", "Reach", "Hour", "Choice", "Height", "Weather"]}
# lista zdań obietnicy (para PL/EN); indeksy 5..11 to siedem mechanizmów (napisy słów na ekranie)
HOOK4 = [("Kadr nie kłamie.", "A frame does not lie."),
         ("Kadr wybiera.", "A frame chooses."),
         ("Osiem miejsc z jednego vloga.", "Eight places from one vlog."),
         ("Potem sprawdzam, jak jest naprawdę.", "Then I show you how it really is."),
         ("Siedem sposobów, na jakie kadr zmienia świat.", "Seven ways a frame changes the world."),
         ("[[Czas||To jest czas]].", "Time."), ("[[Skala||To jest skala]].", "Scale."), ("[[Zasięg||To jest zasięg]].", "Reach."), ("[[Pora dnia||To jest pora dnia]].", "Hour."),
         ("[[Wybór||To jest wybór]].", "Choice."), ("[[Wysokość||To jest wysokość]].", "Height."), ("[[Pogoda||To jest pogoda]].", "Weather."),
         ("Każde miejsce dostaje wyrok.", "Every place gets a verdict."),
         ("Zaczynamy od [[Machu Picchu||Maczu Piczu]].", "We start with Machu Picchu.")]
HOOK4_WORD_IDX = [5, 6, 7, 8, 9, 10, 11]

# ---------- rozdziały ----------
# a: lektor przez fragment oryginału; b: lektor na zdjęciach; shots: (zdjęcie, [zdania b]); pops: zdanie b -> (PL, EN)
CH = [
 {"id": "machu", "mech": {"pl": "CZAS", "en": "TIME"}, "verdict": "W",
  "name": {"pl": "Machu Picchu, Peru", "en": "Machu Picchu, Peru"}, "a": None,
  "b": [("[[Tak wyglądało to miejsce w roku 1912||Tak wyglądało to miejsce w tysiąc dziewięćset dwunastym roku]].", "This is how the place looked in [[1912||nineteen twelve]]."),
        ("Wyprawa [[Hirama Binghama||Hajrama Bingama]] zastała pole gruzu.", "Hiram Bingham's expedition found a field of rubble."),
        ("Potem przyszła renowacja: od [[1929 do 1971||tysiąc dziewięćset dwudziestego dziewiątego do tysiąc dziewięćset siedemdziesiątego pierwszego]].", "Then came the restoration: [[1929 to 1971||nineteen twenty-nine to nineteen seventy-one]]."),
        ("Vlog pokazuje miejsce po remoncie.", "The vlog shows the place after the work."),
        ("A dziś do cytadeli wchodzi do [[4500||czterech tysięcy pięciuset]] osób dziennie.", "And today the citadel admits up to [[4,500||forty-five hundred]] visitors a day."),
        ("Czasem nawet [[5600||pięć tysięcy sześćset]].", "In peak season: [[5,600||fifty-six hundred]]."),
        ("Ludzi tu prawie nie widać, a to też wybór.", "The clip shows no crowd, and that is a choice too."),
        ("Wyrok: kadr wybiera.", "Verdict: the frame chooses.")],
  "shots": [("machu2", [0, 1, 2]), ("machu3", [3, 4, 5]), ("machu1", [6, 7])],
  "pops": {0: ("1912", "1912"), 2: ("1929–1971", "1929–1971"), 4: ("4500 / dzień", "4,500 / day"), 5: ("5600", "5,600")},
  "sources": ["https://en.wikipedia.org/wiki/Machu_Picchu"]},

 {"id": "nepal", "mech": {"pl": "SKALA", "en": "SCALE"}, "verdict": "H",
  "name": {"pl": "Region Everestu, Nepal", "en": "Everest region, Nepal"},
  "a": [("Piękny kadr.", "A beautiful frame."),
        ("I ani jednego człowieka.", "And not one person in it."),
        ("A bez człowieka góra nie ma skali.", "Without a person, a mountain has no scale.")],
  "b": [("Popatrz na [[Ama Dablam||Ama Dabłam]].", "Look at [[Ama Dablam||[Ama Dablam](/ˈɑmɑ dˈɑblɑm/)]]."),
        ("Ma [[6812 m||sześć tysięcy osiemset dwanaście metrów]].", "[[6,812 m||Six thousand eight hundred twelve metres]]."),
        ("Przez kilka dni dominuje na wschodnim niebie każdemu, kto idzie do bazy pod Everestem.", "For several days it dominates the eastern sky for anyone trekking to Everest Base Camp."),
        ("A to jeziora [[Gokyo||Gokjo]] w Parku Narodowym Sagarmata.", "And these are the [[Gokyo||[Gokyo](/ɡˈOkjO/)]] Lakes, in Sagarmatha National Park."),
        ("[[Od 4700 do 5000 metrów nad morzem||Od czterech tysięcy siedmiuset do pięciu tysięcy metrów nad morzem]].", "[[4,700–5,000 m above sea level||Between forty-seven hundred and five thousand metres above sea level]]."),
        ("Teraz znajdź na zboczu dwie malutkie postacie.", "Now find the two tiny figures on the slope."),
        ("To jest prawdziwa skala.", "That is the real scale."),
        ("Wyrok: rzeczywistość jest większa.", "Verdict: reality is bigger.")],
  "shots": [("nepal1", [0, 1, 2]), ("nepal2", [3, 4]), ("nepal3", [5, 6, 7])],
  "pops": {1: ("6812 m", "6,812 m"), 4: ("4700–5000 m", "4,700–5,000 m"), 5: ("2 postacie", "2 figures")},
  "sources": ["https://en.wikipedia.org/wiki/Ama_Dablam", "https://en.wikipedia.org/wiki/Gokyo_Lakes"]},

 {"id": "utah", "mech": {"pl": "ZASIĘG", "en": "REACH"}, "verdict": "U",
  "name": {"pl": "White Rim Road, Utah", "en": "White Rim Road, Utah"},
  "a": [("Dwóch rowerzystów i czerwona skała.", "Two cyclists and a red mesa."),
        ("Prawdziwy kadr.", "An honest frame."),
        ("Tylko że to ułamek drogi.", "But it is a fraction of the road.")],
  "b": [("To droga [[White Rim||Łajt Rim]] w Parku Narodowym [[Canyonlands||Kanion Lends]].", "This road is White Rim, in Canyonlands National Park."),
        ("[[71 mil, czyli około 115 km||Siedemdziesiąt jeden mil, czyli około stu piętnastu kilometrów]].", "[[71 miles, about 115 km||Seventy-one miles, about one hundred fifteen kilometres]]."),
        ("Cała bez asfaltu.", "All of it unpaved."),
        ("Zbudowano ją w [[latach 50.||latach pięćdziesiątych]], pod mesą [[Island in the Sky||Ajlend in de Skaj]].", "It was built in the [[1950s||nineteen fifties]], below the Island in the Sky mesa."),
        ("Po co — żeby poszukiwacze uranu dojechali do złóż.", "The reason was uranium: prospectors needed to reach the deposits."),
        ("A teraz zobacz ją z góry, znad rzeki [[Green River||Grin Riwer]].", "Now see it from above, over the Green River."),
        ("Rzeka płynie wśród kanionów daleko w dole.", "The river winds through canyons far below."),
        ("Wyrok: ten kadr jest uczciwy.", "Verdict: an honest frame.")],
  "shots": [("utah1", [0, 1, 2]), ("utah3", [3, 4]), ("utah2", [5, 6, 7])],
  "pops": {1: ("115 km", "115 km"), 3: ("lata 50.", "1950s")},
  "sources": ["https://en.wikipedia.org/wiki/White_Rim_Road"]},

 {"id": "fuego", "mech": {"pl": "PORA DNIA", "en": "HOUR"}, "verdict": "W",
  "name": {"pl": "Wulkan Fuego, Gwatemala", "en": "Fuego volcano, Guatemala"},
  "a": [("Efektowna erupcja w dzień.", "A spectacular daytime eruption."),
        ("Ale ten wulkan ma drugą twarz.", "But this volcano has a second face.")],
  "b": [("Wulkan Fuego w Gwatemali jest niemal stale aktywny.", "Fuego in Guatemala is almost constantly active."),
        ("[[Mała eksplozja co 15–20 minut||Mała eksplozja z krateru co piętnaście do dwudziestu minut]].", "[[A small explosion every 15–20 minutes||A small explosion from the crater every fifteen to twenty minutes]]."),
        ("W nocy krater żarzy się na czerwono.", "At night the crater glows red."),
        ("[[Tak wygląda w listopadzie 2017||Tak wygląda w listopadzie dwa tysiące siedemnastego roku]].", "[[This is November 2017||This is November twenty seventeen]]."),
        ("Większe erupcje: [[Ponad 80 od 1999 roku||Ponad osiemdziesiąt od tysiąc dziewięćset dziewięćdziesiątego dziewiątego roku]].", "Larger eruptions: [[Over 80 since 1999||Over eighty since nineteen ninety-nine]]."),
        ("Jedna z nich: [[31 stycznia 2018||trzydziestego pierwszego stycznia dwa tysiące osiemnastego]].", "One of them: [[31 January 2018||the thirty-first of January twenty eighteen]]."),
        ("Dzień później satelita [[Landsat 8||Lendsat osiem]] sfotografował smugę popiołu.", "A day later the [[Landsat 8||Landsat eight]] satellite photographed the ash plume."),
        ("Wyrok: kadr wybiera.", "Verdict: the frame chooses.")],
  "shots": [("fuego1", [0, 1, 2]), ("fuego1", [3, 4]), ("fuego3", [5, 6, 7])],
  "pops": {1: ("co 15–20 min", "every 15–20 min"), 4: ("80+ od 1999", "80+ since 1999")},
  "sources": ["https://en.wikipedia.org/wiki/Volc%C3%A1n_de_Fuego"]},

 {"id": "copper", "mech": {"pl": "WYBÓR", "en": "CHOICE"}, "verdict": "H",
  "name": {"pl": "Kanion Miedziany, Meksyk", "en": "Copper Canyon, Mexico"},
  "a": [("Punkt widokowy i jeden stok.", "A viewpoint and one canyon slope."),
        ("Tak wygląda cały Kanion Miedziany?", "Is this the whole Copper Canyon?"),
        ("Nie, to jeden kawałek.", "No, it is one piece of it.")],
  "b": [("Kanion Miedziany to nie jeden kanion.", "Copper Canyon is not one canyon."),
        ("[[To system 6 kanionów||To system sześciu kanionów]].", "[[It is a system of 6 canyons||It is a system of six canyons]]."),
        ("[[Wyżłobiło je 6 rzek||Wyżłobiło je sześć rzek]].", "[[Six rivers cut them||Six rivers cut them]]."),
        ("[[Razem 65 000 km²||Razem sześćdziesiąt pięć tysięcy kilometrów kwadratowych]].", "[[Together 65,000 km²||Together sixty-five thousand square kilometres]]."),
        ("To w [[Sierra Madre Zachodniej||Sjerra Madre Zachodniej]].", "That is in the [[Sierra Madre Occidental||[Sierra](/siˈɛɹə/) [Madre](/mˈɑdɹA/) Occidental]]."),
        ("Z góry wygląda to jak labirynt grzbietów i wąwozów.", "From above it looks like a maze of ridges and gorges."),
        ("Ciągnie się aż po horyzont.", "It stretches all the way to the horizon."),
        ("Wyrok: rzeczywistość jest większa.", "Verdict: reality is bigger.")],
  "shots": [("copper1", [0, 1, 2, 3]), ("copper2", [4, 5, 6, 7])],
  "pops": {1: ("6 kanionów", "6 canyons"), 2: ("6 rzek", "6 rivers"), 3: ("65 000 km²", "65,000 km²")},
  "sources": ["https://en.wikipedia.org/wiki/Copper_Canyon"]},

 {"id": "burning", "mech": {"pl": "WYSOKOŚĆ", "en": "HEIGHT"}, "verdict": "W",
  "name": {"pl": "Burning Man, Nevada", "en": "Burning Man, Nevada"},
  "a": [("Z drona to porządny układ ulic.", "From a drone, a tidy grid of streets."),
        ("Miasto jak narysowane linijką.", "A city drawn with a ruler."),
        ("A jak wygląda z ziemi?", "But what does it look like from the ground?")],
  "b": [("To [[Black Rock City||Blek Rok Siti]].", "This is Black Rock City."),
        ("[[2019 rok: 78 850 uczestników||Dwa tysiące dziewiętnasty rok: siedemdziesiąt osiem tysięcy osiemset pięćdziesiąt uczestników]].", "[[2019: 78,850 participants||Twenty nineteen: seventy-eight thousand eight hundred fifty participants]]."),
        ("[[Dziewięć dni||Dziewięć dni]], do amerykańskiego Święta Pracy.", "Nine days, up to Labor Day."),
        ("Na pustyni [[Black Rock||Blek Rok]] w Nevadzie.", "In the Black Rock Desert in Nevada."),
        ("Teraz zejdź na ziemię.", "Now come down to the ground."),
        ("Kurz wisi nad miastem.", "Dust hangs in the air."),
        ("Miasto widać z poziomu roweru.", "The city is seen from bicycle level."),
        ("Wyrok: kadr wybiera.", "Verdict: the frame chooses.")],
  "shots": [("burning1", [0, 1, 2, 3]), ("burning3", [4, 5, 6, 7])],
  "pops": {1: ("78 850", "78,850"), 2: ("9 dni", "9 days")},
  "sources": ["https://en.wikipedia.org/wiki/Burning_Man"]},

 {"id": "ometepe", "mech": {"pl": "POGODA", "en": "WEATHER"}, "verdict": "U",
  "name": {"pl": "Wyspa Ometepe, Nikaragua", "en": "Ometepe Island, Nicaragua"},
  "a": [("Liście, potem dwa wulkany.", "Leaves, then two volcanoes across the lake."),
        ("Chmury nad szczytem.", "Clouds sit over the summit."),
        ("Tu pogoda robi połowę roboty.", "Here the weather does half the work.")],
  "b": [("[[Ometepe||Ometepe]] to jedna wyspa z dwóch wulkanów.", "[[Ometepe||[Ometepe](/ˌOmɛtˈɛpA/)]] is one island made of two volcanoes."),
        ("[[Concepción||Konsepsjon]] i [[Maderas||Maderas]] łączy niski przesmyk.", "Concepción and [[Maderas||[Maderas](/mɑdˈɛɹɑs/)]] are joined by a low isthmus."),
        ("[[Wyspa ma 31 km długości||Wyspa ma trzydzieści jeden kilometrów długości]].", "[[The island is 31 km long||The island is thirty-one kilometres long]]."),
        ("[[I od 5 do 10 km szerokości||I od pięciu do dziesięciu kilometrów szerokości]].", "[[And 5 to 10 km wide||And five to ten kilometres wide]]."),
        ("[[Concepción||Konsepsjon]] jest aktywny, ze stożkiem jak z podręcznika.", "Concepción is active, with a textbook cone."),
        ("[[Jego podstawa ma 16 km średnicy||Jego podstawa ma szesnaście kilometrów średnicy]].", "[[Its base is 16 km across||Its base is sixteen kilometres across]]."),
        ("Zbocza porasta gęsta zieleń.", "The slopes are covered in dense green."),
        ("Wyżej grzbiet znika w obłokach.", "Higher up, the ridge vanishes into cloud."),
        ("Wyrok: ten kadr jest uczciwy.", "Verdict: an honest frame.")],
  "shots": [("ometepe1", [0, 1, 2, 3]), ("ometepe1", [4, 5]), ("ometepe2", [6, 7, 8])],
  "pops": {2: ("31 km", "31 km"), 5: ("16 km", "16 km")},
  "sources": ["https://en.wikipedia.org/wiki/Ometepe"]},

 {"id": "grand", "mech": {"pl": "SKALA II", "en": "SCALE II"}, "verdict": "H",
  "name": {"pl": "Wielki Kanion, Arizona", "en": "Grand Canyon, Arizona"},
  "a": [("Gałąź na pierwszym planie, za nią mgła.", "A branch in the foreground, haze behind it."),
        ("Człowieka nie widać, więc znów brak skali.", "No person in sight, so again no scale.")],
  "b": [("[[Wielki Kanion ma 277 mil długości||Wielki Kanion ma dwieście siedemdziesiąt siedem mil długości]].", "[[The Grand Canyon is 277 miles long||The Grand Canyon is two hundred seventy-seven miles long]]."),
        ("[[To 446 kilometrów||To czterysta czterdzieści sześć kilometrów]].", "[[That is 446 kilometres||That is four hundred forty-six kilometres]]."),
        ("[[Do 18 mil szerokości||Do osiemnastu mil szerokości]].", "[[Up to 18 miles wide||Up to eighteen miles wide]]."),
        ("I głęboki na ponad jedną milę.", "And over a mile deep."),
        ("Teraz szlak [[Bright Angel||Brajt Endżel]].", "Now the Bright Angel Trail."),
        ("Droga w dół to tylko wąska linia zakosów na ścianie.", "The path is only a thin line of switchbacks on the wall."),
        ("A o zachodzie słońca jeden turysta pokazuje skalę.", "At sunset a single hiker shows the scale."),
        ("Poniżej świątynie ze skały łapią ostatnie światło.", "The rock temples below catch the last light."),
        ("Wyrok: rzeczywistość jest większa.", "Verdict: reality is bigger.")],
  "shots": [("grand2", [0, 1, 2, 3]), ("grand1", [4, 5]), ("grand3", [6, 7, 8])],
  "pops": {0: ("277 mil", "277 miles"), 1: ("446 km", "446 km")},
  "sources": ["https://en.wikipedia.org/wiki/Grand_Canyon"]},
]

# ---------- zakończenie ----------
OUTRO = [("Podsumujmy.", "Let's count."),
         ("Kadr wybierał trzy razy.", "Three times the frame chose."),
         ("Rzeczywistość była większa trzy razy.", "Three times reality was bigger."),
         ("Kadr był uczciwy dwa razy.", "Twice the frame was honest."),
         ("Vlog nie kłamie.", "A vlog does not lie."),
         ("Vlog kadruje.", "A vlog frames."),
         ("Które miejsce zaskoczyło cię najbardziej?", "Which spot surprised you most?"),
         ("Napisz w komentarzu, które sprawdzić następne.", "Tell me in the comments which one to check next.")]
# indeksy zdań OUTRO, przy których wpada kolejny stempel w podsumowaniu (kod, indeks zdania)
OUTRO_TALLY = [("W", 1), ("H", 2), ("U", 3)]

_RX = re.compile(r"\[\[(.*?)\|\|(.*?)\]\]")


def disp(t):
    return _RX.sub(lambda m: m.group(1), t)


def spoken(t):
    return _RX.sub(lambda m: m.group(2), t)


def pair_lists(pairs, lang):
    i = 0 if lang == "pl" else 1
    return [p[i] for p in pairs]


def tally():
    from collections import Counter
    c = Counter(ch["verdict"] for ch in CH)
    return dict(c)


if __name__ == "__main__":
    print(tally())
