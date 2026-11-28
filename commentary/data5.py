"""Film #5 — komentarz do „Most DANGEROUS Places in Nature” (VG Top 10s, CC BY, Pufqk2m0BSA).

Teza: film podaje wiele liczb. Z każdego z ośmiu miejsc sprawdzam jedną liczbę ze źródeł otwartych w sesji
i daję stempel: POTWIERDZONE / NIEŚCISŁE / BŁĘDNE. Werdykty to moje oceny „liczba filmu kontra źródło”,
wpisane ręcznie na podstawie FACTS poniżej; make_texts5.py sprawdza, czy słowo w tekście zgadza się z kodem.

Składnia tekstu: [[napis||mowa]] — napis (cyfry, poprawna pisownia) do podpisu, mowa do syntezatora.
Zdania PL i EN muszą mieć tę samą liczbę (sprawdza make_texts5.py). Zdania nie mogą zawierać wewnętrznych . ! ? .
Kody werdyktu: F = potwierdzone, T = nieścisłe, N = błędne.
"""
import re

SRC = {
    "id": "Pufqk2m0BSA",
    "title": "Most DANGEROUS Places in Nature",
    "author": "VG Top 10s",
    "url": "https://www.youtube.com/watch?v=Pufqk2m0BSA",
    "license": "Creative Commons Attribution license (reuse allowed)",
}

# okna oryginału (s źródła); początek/koniec na granicach słów z ASR
WINDOWS = {"dan": (20.02, 26.06), "skel": (150.80, 157.04), "wash": (249.22, 253.88), "sin": (353.42, 358.70),
           "dv": (487.80, 493.34), "ev": (600.31, 606.89), "fra": (679.95, 685.39), "snk": (772.62, 779.30)}

VERDICT = {
    "F": {"pl": "POTWIERDZONE", "en": "CONFIRMED", "rgb": (86, 204, 130)},
    "T": {"pl": "NIEŚCISŁE", "en": "INEXACT", "rgb": (255, 196, 61)},
    "N": {"pl": "BŁĘDNE", "en": "WRONG", "rgb": (255, 105, 97)},
}
WORD_PL = {"F": "potwierdzone", "T": "nieścisłe", "N": "błędne"}
WORD_EN = {"F": "confirmed", "T": "inexact", "N": "wrong"}

# Fakty (otwarte w tej sesji 25–28.11.2026). Film = co mówi film (ASR); źródło = co podają strony.
FACTS = {
    "dan": "Film: do 131 °F (55 °C) w upalne dni; najgorętsze miejsce wg średniej rocznej. Wikipedia (Danakil Desert): "
           "'The highest temperature ever recorded is 49 °C (121 °F)'; Dallol 'highest average temperature recorded on earth', "
           "34,6 °C (94,3 °F) w latach 1960–1966. => tytuł średniej potwierdzony, rekord 55 °C nie.",
    "skel": "Film: 976 mil, ponad 500 statków. HuffPost: '976-mile (1579-kilometer) stretch'. Wikipedia: 'Length: 310 miles (500 km)', "
            "'hundreds of vessels'. internationalparks.org: park ok. 500 km. Dunedin Star: 1942, 106 osób (85 załogi + 21 pasażerów), "
            "stracono holownik i samolot (Wikipedia, namibian.com.na).",
    "wash": "Film: 1934, rekord najszybszego wiatru na lądzie, 231 mph. NBC: '231 mph record set atop Mount Washington on April 12, 1934'; "
            "MPR: 'The peak gust of 253 mph was recorded during the passage of Tropical Cyclone Olivia on April 10th, 1996', Barrow Island; "
            "NBC: 'Mount Washington still holds the record for the Northern and Western hemispheres'.",
    "sin": "Film: 16 ofiar w lutym 2014 'for venturing into restricted areas'; ponad 9 000 przesiedlonych. EarthSky (5.02.2014): "
           "'death toll from a February 1 eruption ... has risen to 16'; wybuch 'just as many villagers were returning home following an "
           "evacuation order that was partially lifted'; 'More than 30,000 people have been displaced since ... September 2013'.",
    "dv": "Film: lipiec 2021, 130 °F, najgorętsze wiarygodnie zmierzone. NPR (10.07.2021): 'recorded high temperatures of 130 degrees Fahrenheit "
          "on Friday', 'matches 130 degrees recorded in August 2020', 'the hottest that we have seen with some of the more reliable equipment', "
          "1913 (134 °F) 'widely disputed'.",
    "ev": "Film: strefa śmierci od 8 000 m, <356 mbar, tlen 40% poziomu morza, minus 120 °F (minus 49 °C). Wikipedia (Death zone): od 8 000 m, "
          "poniżej 356 mbar; ciśnienie parcjalne tlenu na szczycie 'less than a third'. Rachunek: (−120−32)·5/9 = −84,4 °C, nie −49 °C.",
    "fra": "Film: dingo, rekiny, kubomeduzy i Irukandji, silne prądy. Intrepid: 'large numbers of sharks and jellyfish', 'powerful riptides that can pull "
           "even the strongest swimmers out to sea'. Queensland Parks (marine stingers): 'Irukandji jellyfish ... especially during the summer months' "
           "w wodach K'gari. Nie znalazłem w otwartych źródłach: żarłacz biały, kubomeduza.",
    "snk": "Film: 106 akrów, 2 000–4 000 węży, 'in certain areas ... one snake per square meter', śmiertelność ukąszenia ok. 7% / 3%. "
           "Wikipedia (Ilha da Queimada Grande): 43 ha (106 akrów), 2 000–4 000 żararak, starsza ocena ok. 430 000 'revised downward'; "
           "Discover: 'There is no official record of a golden lancehead biting a human'; Skeptoid: 1 na m² to stary szacunek, który dał 430 000. "
           "Rachunek: 430 000 m² / 4 000 = 107 m², / 2 000 = 215 m² na węża.",
}

# ---------- zimny start ----------
HOOK1 = [("Jeden wąż na metr kwadratowy?", "One snake per square metre?"),
         ("Tak film opisuje Wyspę Węży.", "That is how the video describes Snake Island."),
         ("Wyspa ma czterdzieści trzy hektary.", "The island covers forty-three hectares."),
         ("Węży jest od dwóch do czterech tysięcy.", "There are two to four thousand snakes."),
         ("Średnio wychodzi jeden wąż na sto do dwustu metrów.", "On average, that is one snake per hundred to two hundred metres.")]
HOOK1_SHOTS = [("snk1", [0, 1], "snk1@h1"), ("snk2", [2, 3], None), ("snk1", [4], "snk1@h2")]
HOOK1_POPS = {0: ("1 wąż / 1 m²?", "1 snake / 1 m²?"), 2: ("43 ha", "43 ha"), 3: ("2000–4000", "2,000–4,000"),
              4: ("1 wąż / 100–200 m²", "1 snake / 100–200 m²")}

HOOK2 = [("Najsilniejszy wiatr w historii: [[231 mph||dwieście trzydzieści jeden mil na godzinę]]?", "The strongest wind in history: [[231 mph||two hundred thirty-one miles per hour]]?"),
         ("Tak film pisze o [[Mount Washington||Maunt Waszyngton]].", "That is what the video says about Mount Washington."),
         ("Ale w tysiąc dziewięćset dziewięćdziesiątym szóstym wiało mocniej.", "But in nineteen ninety-six, it blew harder."),
         ("[[253 mph||Dwieście pięćdziesiąt trzy mile na godzinę]], na wyspie Barrow.", "[[253 mph||Two hundred fifty-three miles per hour]], on Barrow Island.")]
HOOK2_SHOTS = [("wash1", [0, 1], "wash1@h2"), ("wash3", [2], None), ("wash2", [3], "wash2@h2")]
HOOK2_POPS = {0: ("231 mph", "231 mph"), 3: ("253 mph", "253 mph")}

# obietnica: stemple na zdaniach 2, 3, 4
HOOK3 = [("Osiem miejsc z jednego filmu o najniebezpieczniejszych miejscach natury.", "Eight places from one video about the most dangerous places in nature."),
         ("Z każdego sprawdzam jedną liczbę.", "From each, I check one number."),
         ("Zgadza się: potwierdzone.", "It checks out: confirmed."),
         ("Z zastrzeżeniem: nieścisłe.", "Fine print: inexact."),
         ("Źródło mówi co innego: błędne.", "The source says otherwise: wrong."),
         ("Ile z ośmiu liczb się obroni?", "How many of the eight numbers hold up?"),
         ("Zaczynamy od [[Danakilu||Danakilu]].", "We start with Danakil.")]
HOOK3_STAMPS = [("F", 2), ("T", 3), ("N", 4)]
PROMISE_BG = ["dan3", "skel3", "wash1", "sin1", "dv2", "ev2", "dan1"]

# ---------- rozdziały ----------
# a: lektor na fragmencie oryginału; b: lektor na zdjęciach; shots: (zdjęcie, [zdania b], klucz ruchu lub None)
CH = [
 {"id": "dan", "n": 1, "name": {"pl": "Danakil (Etiopia)", "en": "Danakil (Ethiopia)"}, "verdict": "T",
  "a": [("Pierwszy: [[Danakil||Danakil]].", "First: Danakil."),
        ("Film: najgorętsze miejsce na Ziemi.", "The video: the hottest place on Earth.")],
  "b": [("To [[Erta Ale||Erta Ale]]: jezioro lawy w Etiopii.", "This is [[Erta Ale||[Erta Ale](/ˈɛɹtə ˈɑːleɪ/)]]: a lava lake in Ethiopia."),
        ("Film pokazuje żółte, zielone i rdzawe plamy na ziemi.", "The video shows yellow, green and rust-coloured patches on the ground."),
        ("A tak całą depresję widać z satelity.", "And this is the whole depression seen from a satellite."),
        ("Film mówi: do [[55 °C||pięćdziesięciu pięciu stopni]] w upalne dni.", "The video says: up to [[55 °C||fifty-five degrees Celsius]] on hot days."),
        ("Wikipedia: najwyższa zmierzona temperatura to [[49 °C||czterdzieści dziewięć]].", "Wikipedia: the highest recorded temperature is [[49 °C||forty-nine]]."),
        ("Za to tytuł najwyższej średniej dla [[Dallol||Dalol]] jest prawdziwy.", "The title for the highest average, for [[Dallol||[Dallol](/dæˈlɒl/)]], is real."),
        ("[[34,6 °C||Trzydzieści cztery i sześć dziesiątych]], ale z lat sześćdziesiątych.", "[[34.6 °C||Thirty-four point six]], but from the nineteen sixties."),
        ("Werdykt: nieścisłe.", "Verdict: inexact."),
        ("Moim zdaniem to rekord średniej, nie rekord dnia.", "My read: it is a record for the average, not for a day.")],
  "shots": [("dan1", [0, 1], None), ("dan3", [2, 3], None), ("dan2", [4, 5], None), ("dan3", [6, 7], "dan3~2"), ("dan2", [8], "dan2~2")],
  "vi": 7,
  "pops": {3: ("film: 55 °C", "video: 55 °C"), 4: ("Wikipedia: 49 °C", "Wikipedia: 49 °C"), 6: ("34,6 °C (1960–66)", "34.6 °C (1960–66)")},
  "apop": {},
  "sources": ["https://en.wikipedia.org/wiki/Danakil_Desert"]},

 {"id": "skel", "n": 2, "name": {"pl": "Wybrzeże Szkieletów (Namibia)", "en": "Skeleton Coast (Namibia)"}, "verdict": "T",
  "a": [("[[976 mil||Dziewięćset siedemdziesiąt sześć mil]] wybrzeża, tak mówi film.", "[[976 miles||Nine hundred seventy-six miles]] of coast, says the video.")],
  "b": [("Wrak [[Suiderkus||Sajderkus]] na [[Wybrzeżu Szkieletów||Wybrzeżu Szkieletów]].", "The Suiderkus wreck on the Skeleton Coast."),
        ("W filmie fale biją o wrak.", "In the video, waves pound a wreck."),
        ("Wrak [[Eduard Bohlen||Eduard Bolen]] przy wybrzeżu Namibii.", "The wreck of the Eduard Bohlen off Namibia's coast."),
        ("Park narodowy: około [[500 km||pięciuset kilometrów]].", "The national park page: about [[500 km||five hundred kilometres]]."),
        ("Wikipedia: [[310 mil||trzysta dziesięć mil]].", "Wikipedia: [[310 miles||three hundred ten miles]]."),
        ("[[976 mil||Dziewięćset siedemdziesiąt sześć mil]] podaje tylko [[HuffPost||Hafpost]].", "Only HuffPost gives [[976 miles||nine hundred seventy-six miles]]."),
        ("To ponad [[1500 km||tysiąc pięćset kilometrów]].", "That is over [[1,500 km||fifteen hundred kilometres]]."),
        ("Za to historia [[Dunedin Star||Danidin Star]] się zgadza.", "The story of the [[Dunedin Star||[Dunedin Star](/dʌˈniːdɪn stɑːɹ/)]] does check out."),
        ("Werdykt: nieścisłe.", "Verdict: inexact."),
        ("Moim zdaniem liczba bez granic wybrzeża nic nie znaczy.", "My read: a number without the coast's limits means nothing.")],
  "shots": [("skel1", [0, 1], None), ("skel3", [2, 3], None), ("skel2", [4, 5], None), ("skel1", [6, 7], "skel1~2"), ("skel3", [8, 9], "skel3~2")],
  "vi": 8,
  "pops": {3: ("park: ≈ 500 km", "park: ≈ 500 km"), 4: ("Wikipedia: 310 mil", "Wikipedia: 310 mi"), 5: ("976 mil", "976 mi")},
  "apop": {0: ("film: 976 mil", "video: 976 mi")},
  "sources": ["https://en.wikipedia.org/wiki/Skeleton_Coast", "https://www.huffpost.com/entry/the-eerie-shipwrecks-of-n_b_8122710",
              "https://www.internationalparks.org/namibia/Skeleton%20Coast", "https://www.namibian.com.na/shipwrecks-of-the-skeleton-coast/"]},

 {"id": "wash", "n": 3, "name": {"pl": "Mount Washington (USA)", "en": "Mount Washington (USA)"}, "verdict": "T",
  "a": [("Film: [[231 mph||dwieście trzydzieści jeden mil na godzinę]].", "The video: [[231 mph||two hundred thirty-one miles per hour]].")],
  "b": [("Szczyt [[Mount Washington||Maunt Waszyngton]] latem.", "The summit of Mount Washington in summer."),
        ("A to Sherman Adams Summit Building.", "And this is the Sherman Adams Summit Building."),
        ("I kolejka zębata na szczyt.", "And the cog railway to the summit."),
        ("Rekord z dwunastego kwietnia tysiąc dziewięćset trzydziestego czwartego.", "The record is from the twelfth of April, nineteen thirty-four."),
        ("Dziesiątego kwietnia tysiąc dziewięćset dziewięćdziesiątego szóstego zmierzono więcej.", "On the tenth of April, nineteen ninety-six, more was measured."),
        ("[[253 mph||Dwieście pięćdziesiąt trzy mile na godzinę]] na wyspie Barrow.", "[[253 mph||Two hundred fifty-three miles per hour]] on Barrow Island."),
        ("To było podczas cyklonu Olivia.", "That was during Cyclone Olivia."),
        ("[[Mount Washington||Maunt Waszyngton]] wciąż trzyma rekord półkuli północnej i zachodniej.", "Mount Washington still holds the record for the Northern and Western hemispheres."),
        ("Werdykt: nieścisłe.", "Verdict: inexact."),
        ("Moim zdaniem to rekord z dopiskiem, nie rekord świata.", "My read: a record with an asterisk, not a world record.")],
  "shots": [("wash1", [0, 1], None), ("wash3", [2, 3], None), ("wash2", [4, 5], None), ("wash1", [6, 7], "wash1~2"), ("wash3", [8, 9], "wash3~2")],
  "vi": 8,
  "pops": {3: ("12.04.1934: 231 mph", "12 Apr 1934: 231 mph"), 5: ("10.04.1996: 253 mph", "10 Apr 1996: 253 mph")},
  "apop": {},
  "sources": ["https://www.nbcnews.com/id/wbna35084480", "https://www.mprnews.org/story/2010/01/27/new-world-wind-record-verified"]},

 {"id": "sin", "n": 4, "name": {"pl": "Sinabung (Sumatra)", "en": "Sinabung (Sumatra)"}, "verdict": "T",
  "a": [("Film: szesnaście ofiar, bo weszli do stref zakazanych.", "The video: sixteen victims, because they entered restricted zones.")],
  "b": [("Tak wygląda [[Sinabung||Synabung]] podczas wybuchu.", "This is [[Sinabung||[Sinabung](/sɪnɑːˈbʊŋ/)]] during an eruption."),
        ("W filmie w tym miejscu widać śnieżny stok.", "In the video, at this point, you see a snowy slope."),
        ("Pierwszego lutego dwa tysiące czternastego zginęło [[16 osób||szesnaście osób]].", "On the first of February, twenty fourteen, sixteen people died."),
        ("To się zgadza.", "That checks out."),
        ("Ale wybuch zaskoczył wieśniaków wracających do domów.", "But the eruption caught villagers returning home."),
        ("Film: ponad [[9000||dziewięć tysięcy]] przesiedlonych.", "The video: over [[9,000||nine thousand]] displaced."),
        ("[[EarthSky||ErSky]] w lutym czternastego: ponad [[30 000||trzydzieści tysięcy]].", "EarthSky in February twenty fourteen: over [[30,000||thirty thousand]]."),
        ("Werdykt: nieścisłe.", "Verdict: inexact."),
        ("Moim zdaniem film uprościł historię tych szesnastu osób.", "My read: the video simplified the story of those sixteen people.")],
  "shots": [("sin1", [0, 1], None), ("sin2", [2, 3], None), ("sin1", [4, 5], "sin1~2"), ("sin2", [6, 7], "sin2~2"), ("sin1", [8], "sin1@h3")],
  "vi": 7,
  "pops": {2: ("16 ofiar", "16 deaths"), 5: ("film: 9000+", "video: 9,000+"), 6: ("EarthSky: 30 000+", "EarthSky: 30,000+")},
  "apop": {0: ("film: 16 ofiar", "video: 16 deaths")},
  "sources": ["https://earthsky.org/earth/death-toll-climbs-to-16-since-mount-sinabung-eruption"]},

 {"id": "dv", "n": 5, "name": {"pl": "Dolina Śmierci (USA)", "en": "Death Valley (USA)"}, "verdict": "F",
  "a": [("Film: [[130 °F||sto trzydzieści stopni]], rekord wiarygodnych pomiarów.", "The video: [[130 °F||one hundred thirty degrees]], a record of reliable readings.")],
  "b": [("Tak wygląda okolica [[Furnace Creek||Fyrnys Krik]].", "This is the area around [[Furnace Creek||[Furnace Creek](/ˈfɜːɹnɪs kɹiːk/)]]."),
        ("Film pokazuje jasne, urwiste zbocza.", "The video shows pale, steep slopes."),
        ("[[Badwater Basin||Badłoter Bejsin]] widziany z punktu [[Dante's View||Dantes Wiu]].", "Badwater Basin seen from Dante's View."),
        ("W lipcu dwa tysiące dwudziestego pierwszego: [[130 °F||sto trzydzieści]].", "In July twenty twenty-one: [[130 °F||one hundred thirty]]."),
        ("[[NPR||En Pi Ar]]: tyle samo co w sierpniu dwa tysiące dwudziestego.", "NPR: the same as in August twenty twenty."),
        ("Najgorętsze z wiarygodniejszego sprzętu, mówi meteorolog.", "The hottest with more reliable equipment, says a meteorologist."),
        ("Sto trzydzieści cztery z tysiąc dziewięćset trzynastego jest kwestionowane.", "The one hundred thirty-four from nineteen thirteen is disputed."),
        ("Werdykt: potwierdzone.", "Verdict: confirmed."),
        ("Moim zdaniem film ma rację, ale rekord jest tylko wyrównany.", "My read: the video is right, but the record is only matched.")],
  "shots": [("dv1", [0, 1], None), ("dv2", [2, 3], None), ("dv3", [4, 5], None), ("dv2", [6, 7], "dv2~2"), ("dv1", [8], "dv1~2")],
  "vi": 7,
  "pops": {3: ("130 °F = 54 °C", "130 °F = 54 °C"), 6: ("1913: 134 °F (sporne)", "1913: 134 °F (disputed)")},
  "apop": {0: ("film: 130 °F", "video: 130 °F")},
  "sources": ["https://www.npr.org/2021/07/10/1014941439/death-valley-posts-130-degree-heat-potentially-matching-a-record-high"]},

 {"id": "ev", "n": 6, "name": {"pl": "Everest (strefa śmierci)", "en": "Everest (the death zone)"}, "verdict": "N",
  "a": [("Film: tlen spada do czterdziestu procent.", "The video: oxygen drops to forty percent."),
        ("Sprawdźmy to.", "Let us check.")],
  "b": [("Szczyt Everestu w dwa tysiące siedemnastym roku.", "The summit of Everest in twenty seventeen."),
        ("Wikipedia: na szczycie ciśnienie tlenu to mniej niż jedna trzecia.", "Wikipedia: at the summit, oxygen pressure is less than a third."),
        ("Strefa śmierci zaczyna się od [[8000 m||ośmiu tysięcy metrów]].", "The death zone starts at [[8,000 m||eight thousand metres]]."),
        ("Widok na Everest z wioski [[Syangboche||Sjangboczi]].", "A view of Everest from the village of [[Syangboche||[Syangboche](/sjɑːŋˈboʊtʃeɪ/)]]."),
        ("Film podaje też minus sto dwadzieścia stopni Fahrenheita.", "The video also gives minus one hundred twenty degrees Fahrenheit."),
        ("I minus czterdzieści dziewięć Celsjusza.", "And minus forty-nine Celsius."),
        ("A minus sto dwadzieścia to minus osiemdziesiąt cztery.", "But minus one hundred twenty is minus eighty-four."),
        ("Werdykt: błędne.", "Verdict: wrong."),
        ("Moim zdaniem w jednym zdaniu film przeczy sam sobie.", "My read: in one sentence, the video contradicts itself.")],
  "shots": [("ev1", [0, 1], None), ("ev2", [2, 3], None), ("ev1", [4, 5], "ev1~2"), ("ev2", [6, 7], "ev2~2"), ("ev1", [8], "ev1@h3")],
  "vi": 7,
  "pops": {1: ("< 1/3 (Wikipedia)", "< 1/3 (Wikipedia)"), 2: ("8000 m", "8,000 m"), 6: ("−120 °F = −84 °C", "−120 °F = −84 °C")},
  "apop": {0: ("film: 40%", "video: 40%")},
  "sources": ["https://en.wikipedia.org/wiki/Death_zone"]},

 {"id": "fra", "n": 7, "name": {"pl": "K'gari / Fraser Island (Australia)", "en": "K'gari / Fraser Island (Australia)"}, "verdict": "F",
  "a": [("[[Wyspa Fraser||Wyspa Frejzer]], czyli [[K'gari||Kygari]].", "Fraser Island, or [[K'gari||[K'gari](/ˈɡɜːɹi/)]]."),
        ("Film: groźna woda.", "The video: dangerous water.")],
  "b": [("[[Maheno||Maheno]]: wrak statku na plaży wyspy.", "Maheno: a shipwreck on the island's beach."),
        ("W filmie widać wydmę nad lasem i płyciznę.", "In the video, you see a dune above a forest and shallows."),
        ("[[Dingo||Dindżo]] na [[Fraser Island||Frejzer Ajlend]].", "A dingo on Fraser Island."),
        ("Film ostrzega przed prądami, rekinami i meduzami.", "The video warns of currents, sharks and jellyfish."),
        ("Intrepid: potężne prądy, które wciągają nawet najlepszych pływaków.", "Intrepid: powerful rips that pull even the strongest swimmers out."),
        ("Rząd [[Queenslandu||Kłinslandu]]: meduzy [[Irukandji||Irukandżi]], zwłaszcza latem.", "The Queensland government: Irukandji jellyfish, especially in summer."),
        ("Jedyne, czego nie znalazłem w źródłach: żarłacz biały i kubomeduza.", "The only things I did not find in the sources: great whites and box jellyfish."),
        ("Werdykt: potwierdzone.", "Verdict: confirmed."),
        ("Moim zdaniem to uczciwe ostrzeżenie.", "My read: an honest warning.")],
  "shots": [("fra1", [0, 1], None), ("fra2", [2, 3], None), ("fra3", [4, 5], None), ("fra1", [6, 7], "fra1~2"), ("fra2", [8], "fra2~2")],
  "vi": 7,
  "pops": {4: ("prądy odpływowe", "rip currents"), 5: ("Irukandji: lato", "Irukandji: summer")},
  "apop": {},
  "sources": ["https://www.intrepidtravel.com/be/australia/fraser-island/can-you-swim-at-fraser-island",
              "https://parks.desi.qld.gov.au/__data/assets/pdf_file/0025/158506/marine-stingers-fraser.pdf"]},

 {"id": "snk", "n": 8, "name": {"pl": "Wyspa Węży (Brazylia)", "en": "Snake Island (Brazil)"}, "verdict": "T",
  "a": [("Ostatnie: film obiecuje jednego węża na metr.", "The last one: the video promises one snake per metre."),
        ("Zgadza się?", "Is that right?")],
  "b": [("To [[Bothrops insularis||Botrops insularis]], mieszkaniec tej wyspy.", "This is Bothrops insularis, a resident of this island."),
        ("W filmie widać turkusową wodę i skalisty brzeg z budynkami.", "In the video, you see turquoise water and a rocky shore with buildings."),
        ("Wyspa ma [[43 ha||czterdzieści trzy hektary]].", "The island covers [[43 ha||forty-three hectares]]."),
        ("Węży jest od dwóch do czterech tysięcy.", "There are two to four thousand snakes."),
        ("Stare szacunki: jeden na metr, czyli czterysta trzydzieści tysięcy.", "The old estimate: one per metre, which means four hundred thirty thousand."),
        ("Dziś wychodzi jeden wąż na sto do dwustu metrów.", "Today it works out to one snake per hundred to two hundred metres."),
        ("Film liczy też śmiertelność ukąszenia: siedem procent.", "The video also counts the bite fatality: seven percent."),
        ("[[Discover||Diskaver]]: nie ma oficjalnego zapisu ukąszenia człowieka.", "Discover: there is no official record of a bite on a human."),
        ("Werdykt: nieścisłe.", "Verdict: inexact."),
        ("Moim zdaniem straszne liczby działają tu lepiej niż prawdziwe.", "My read: scary numbers work better here than true ones.")],
  "shots": [("snk1", [0, 1], None), ("snk2", [2, 3], None), ("snk1", [4, 5], "snk1~2"), ("snk2", [6, 7], "snk2~2"), ("snk1", [8, 9], "snk1@h3")],
  "vi": 8,
  "pops": {2: ("43 ha", "43 ha"), 3: ("2000–4000 węży", "2,000–4,000 snakes"), 4: ("430 000?", "430,000?"), 7: ("0 zapisanych ukąszeń", "0 recorded bites")},
  "apop": {0: ("film: 1 wąż / m²", "video: 1 snake / m²")},
  "sources": ["https://en.wikipedia.org/wiki/Ilha_da_Queimada_Grande", "https://discovermagazine.com/planet-earth/almost-4-000-snakes-rule-this-brazilian-island",
              "https://skeptoid.com/episodes/913"]},
]
CH_BY = {c["id"]: c for c in CH}
ORDER = [c["id"] for c in CH]

# ---------- zakończenie ----------
OUTRO = [("Podsumujmy.", "Let's count."),
         ("Dwa razy: potwierdzone.", "Twice: confirmed."),
         ("Pięć razy: nieścisłe.", "Five times: inexact."),
         ("Raz: błędne.", "Once: wrong."),
         ("Film rzadko zmyśla, częściej upraszcza.", "The video rarely invents, more often it simplifies."),
         ("Rekordy się starzeją, a film nie.", "Records get old, the video does not."),
         ("Liczby i źródła są w opisie.", "The numbers and sources are in the description."),
         ("Teraz pytanie do ciebie.", "Now a question for you."),
         ("Które z tych ośmiu miejsc odwiedziłbyś mimo ostrzeżeń?", "Which of these eight places would you visit despite the warnings?"),
         ("Napisz w komentarzu, a następny film będzie o miejscu z największą liczbą głosów.", "Tell me in the comments, and the next video will be about the place with the most votes.")]
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
