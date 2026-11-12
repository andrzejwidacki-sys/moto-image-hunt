"""Dane komentarza do filmu #1 (Ryan Van Duzer, eCtUQp9aISc, CC BY).

Jedno źródło prawdy: teksty mówione (liczby słowami, nazwy zapisane fonetycznie),
podpisy (cyfry, poprawna pisownia), przypisanie zdjęć do zdań, źródła faktów.
Zdania PL i EN muszą mieć tę samą liczbę (sprawdza make_texts.py).
"""

SRC = {
    "id": "eCtUQp9aISc",
    "title": "Najbardziej malownicze miejsca ... (film #1)",
    "author": "Ryan Van Duzer",
    "url": "https://www.youtube.com/watch?v=eCtUQp9aISc",
    "license": "Creative Commons Attribution license (reuse allowed)",
}

# okno oryginału (sekundy źródła) -> 7 s
WINDOWS = {"nepal": (163.9, 170.9), "machu": (253.95, 260.95), "utah": (322.95, 329.95),
           "fuego": (385.0, 392.0), "copper": (402.8, 409.8), "burning": (595.7, 602.7),
           "grand": (663.9, 670.9), "ometepe": (721.7, 728.7)}

INTRO = {
    "spoken": {
        "pl": ["Komentarz do filmu podróżniczego Rajana Van Duzera, na licencji Creative Commons, uznanie autorstwa.",
               "Oglądamy po siedem sekund z każdego miejsca, a potem sprawdzamy, jak ono naprawdę wygląda."],
        "en": ["A commentary on a travel video by Ryan Van Duzer, licensed Creative Commons Attribution.",
               "We watch seven seconds of each place, and then check what it really looks like."],
    },
    "caption": {
        "pl": ["Komentarz do filmu Ryana Van Duzera (CC BY).",
               "7 sekund oryginału, potem: jak to miejsce naprawdę wygląda."],
        "en": ["A commentary on a video by Ryan Van Duzer (CC BY).",
               "7 seconds of the original, then: what the place really looks like."],
    },
}

PLACES = [
 {"id": "nepal", "name": {"pl": "Region Everestu, Nepal", "en": "Everest region, Nepal"},
  "spoken": {
   "pl": ["W kadrze są zbliżenia szczytów, małe jezioro i flagi modlitewne.",
          "A tak wygląda Ama Dablam, sześć tysięcy osiemset dwanaście metrów, która przez kilka dni dominuje na wschodnim niebie każdemu, kto idzie do bazy pod Everestem.",
          "A to jeziora Gokjo w Parku Narodowym Sagarmata, na wysokości od czterech tysięcy siedmiuset do pięciu tysięcy metrów.",
          "Zobacz dwie malutkie postacie na zboczu: to jest prawdziwa skala tego krajobrazu."],
   "en": ["The clip shows close-ups of peaks, a small lake and prayer flags.",
          "This is Ama Dablam, six thousand eight hundred twelve metres high, which for several days dominates the eastern sky for anyone trekking to Everest Base Camp.",
          "And these are the Gokyo Lakes in Sagarmatha National Park, at an elevation of forty-seven hundred to five thousand metres.",
          "Look at the two tiny figures on the slope: that is the real scale of this landscape."]},
  "caption": {
   "pl": ["W kadrze: zbliżenia szczytów, małe jezioro, flagi modlitewne.",
          "Ama Dablam, 6812 m — przez kilka dni dominuje na wschodnim niebie na trasie do bazy pod Everestem.",
          "Jeziora Gokyo, Park Narodowy Sagarmatha, 4700–5000 m n.p.m.",
          "Dwie malutkie postacie na zboczu — prawdziwa skala krajobrazu."],
   "en": ["In the clip: close-ups of peaks, a small lake, prayer flags.",
          "Ama Dablam, 6,812 m — for several days it dominates the eastern sky on the trek to Everest Base Camp.",
          "Gokyo Lakes, Sagarmatha National Park, 4,700–5,000 m above sea level.",
          "Two tiny figures on the slope — the real scale of the landscape."]},
  # (zdjęcie, zdania które ono pokrywa)
  "shots": [("nepal1", [0, 1]), ("nepal2", [2]), ("nepal3", [3])],
  "sources": ["https://en.wikipedia.org/wiki/Ama_Dablam", "https://en.wikipedia.org/wiki/Gokyo_Lakes"]},

 {"id": "machu", "name": {"pl": "Machu Picchu, Peru", "en": "Machu Picchu, Peru"},
  "spoken": {
   "pl": ["W tym fragmencie widać piechurów i obóz, ale nie samą cytadelę.",
          "Tak naprawdę wygląda Maczu Piczu: kamienne tarasy i domy na grzbiecie, a za nimi szczyt, często owinięty chmurami.",
          "Zdjęcie z wyprawy Hirama Binghama z tysiąc dziewięćset dwunastego roku pokazuje to samo miejsce jako pole gruzu, jeszcze przed renowacją z lat tysiąc dziewięćset dwudziestego dziewiątego do tysiąc dziewięćset siedemdziesiątego pierwszego.",
          "Dziś do cytadeli wchodzi dziennie do czterech tysięcy pięciuset osób, a w szczycie sezonu do pięciu tysięcy sześciuset."],
   "en": ["This window shows trekkers and a camp, but not the citadel itself.",
          "This is what Machu Picchu really looks like: stone terraces and houses on a ridge, with the peak behind them, often wrapped in cloud.",
          "A photograph from Hiram Bingham's expedition in nineteen twelve shows the same place as a field of rubble, before the restoration of nineteen twenty-nine to nineteen seventy-one.",
          "Today the citadel admits up to forty-five hundred visitors a day, and up to fifty-six hundred in peak season."]},
  "caption": {
   "pl": ["W tym fragmencie: piesi i obóz, nie sama cytadela.",
          "Kamienne tarasy i domy na grzbiecie, za nimi szczyt często w chmurach.",
          "1912, wyprawa Hirama Binghama: pole gruzu — przed renowacją z lat 1929–1971.",
          "Dziś: do 4500 osób dziennie, w szczycie sezonu do 5600."],
   "en": ["In this window: trekkers and a camp, not the citadel itself.",
          "Stone terraces and houses on a ridge, the peak behind them often in cloud.",
          "1912, Hiram Bingham's expedition: a field of rubble — before the 1929–1971 restoration.",
          "Today: up to 4,500 visitors a day, up to 5,600 in peak season."]},
  "shots": [("machu1", [0, 1]), ("machu2", [2]), ("machu3", [3])],
  "sources": ["https://en.wikipedia.org/wiki/Machu_Picchu"]},

 {"id": "utah", "name": {"pl": "White Rim Road, Utah", "en": "White Rim Road, Utah"},
  "spoken": {
   "pl": ["W kadrze dwóch rowerzystów na polnej drodze i czerwona mesa w tle.",
          "To droga Łajt Rim w Parku Narodowym Kenionlends: siedemdziesiąt jeden mil, czyli około stu piętnastu kilometrów drogi bez asfaltu.",
          "Poprowadzono ją w latach pięćdziesiątych pod szczytem mesy Ajlend in de Skaj, żeby poszukiwacze mogli dojechać do złóż uranu.",
          "A tak ten krajobraz wygląda z góry, z punktu widokowego nad rzeką Grin Riwer, gdzie rzeka wije się w kanionach daleko w dole."],
   "en": ["The clip shows two cyclists on a dirt road, with a red mesa behind them.",
          "This is the White Rim Road in Canyonlands National Park: seventy-one miles, about one hundred fifteen kilometres, of unpaved road.",
          "It was built in the nineteen fifties below the Island in the Sky mesa, so that prospectors could reach uranium deposits.",
          "And this is the same country from above, at the Green River Overlook, where the river winds through canyons far below."]},
  "caption": {
   "pl": ["W kadrze: dwóch rowerzystów, czerwona mesa.",
          "White Rim Road, Canyonlands NP: 71,2 mili (114,6 km) drogi gruntowej.",
          "Zbudowana w latach 50. pod mesą Island in the Sky — dojazd do złóż uranu.",
          "Green River Overlook: rzeka wijąca się w kanionach."],
   "en": ["In the clip: two cyclists, a red mesa.",
          "White Rim Road, Canyonlands NP: 71.2 miles (114.6 km) of unpaved road.",
          "Built in the 1950s below the Island in the Sky mesa — access to uranium deposits.",
          "Green River Overlook: the river winding through the canyons."]},
  "shots": [("utah1", [0]), ("utah3", [1, 2]), ("utah2", [3])],
  "sources": ["https://en.wikipedia.org/wiki/White_Rim_Road"]},

 {"id": "fuego", "name": {"pl": "Wulkan Fuego, Gwatemala", "en": "Fuego volcano, Guatemala"},
  "spoken": {
   "pl": ["W kadrze erupcja w ciągu dnia: kolumna popiołu nad zboczem.",
          "Fuego w Gwatemali jest niemal stale aktywny: mały wybuch z krateru zdarza się co piętnaście do dwudziestu minut.",
          "W nocy krater żarzy się na czerwono, jak na tym zdjęciu z listopada dwa tysiące siedemnastego roku, a większe erupcje, ponad osiemdziesiąt od tysiąc dziewięćset dziewięćdziesiątego dziewiątego roku, zdarzają się dużo rzadziej."],
   "en": ["The clip shows a daytime eruption: a column of ash rising over the slope.",
          "Fuego in Guatemala is almost constantly active: a small explosion leaves the crater every fifteen to twenty minutes.",
          "At night the crater glows red, as in this photograph from November twenty seventeen, while larger eruptions, over eighty since nineteen ninety-nine, are much rarer."]},
  "caption": {
   "pl": ["W kadrze: erupcja w dzień, kolumna popiołu.",
          "Fuego jest niemal stale aktywny: mały wybuch co 15–20 minut.",
          "W nocy krater żarzy się na czerwono (listopad 2017). Większych erupcji: ponad 80 od 1999 r."],
   "en": ["In the clip: a daytime eruption, a column of ash.",
          "Fuego is almost constantly active: a small explosion every 15–20 minutes.",
          "At night the crater glows red (November 2017). Larger eruptions: over 80 since 1999."]},
  "shots": [("fuego1", [0, 1, 2])],
  "sources": ["https://en.wikipedia.org/wiki/Volc%C3%A1n_de_Fuego"]},

 {"id": "copper", "name": {"pl": "Kanion Miedziany, Meksyk", "en": "Copper Canyon, Mexico"},
  "spoken": {
   "pl": ["Ten punkt widokowy pokazuje jeden fragment kanionu, z małą wiatą na krawędzi.",
          "Ale Kanion Miedziany to nie jeden kanion: to system sześciu kanionów wyżłobionych przez sześć rzek, o powierzchni sześćdziesięciu pięciu tysięcy kilometrów kwadratowych w Sierra Madre Zachodniej.",
          "Z góry wygląda to jak labirynt grzbietów i wąwozów, który ciągnie się aż po horyzont."],
   "en": ["This viewpoint shows a single stretch of the canyon, with a small shelter at the edge.",
          "But Copper Canyon is not one canyon: it is a system of six canyons cut by six rivers, covering sixty-five thousand square kilometres in the Sierra Madre Occidental.",
          "From above it looks like a maze of ridges and gorges that stretches all the way to the horizon."]},
  "caption": {
   "pl": ["W kadrze: jeden punkt widokowy z wiatą na krawędzi.",
          "Kanion Miedziany: 6 kanionów, 6 rzek, 65 000 km² w Sierra Madre Zachodniej.",
          "Z góry: labirynt grzbietów i wąwozów po horyzont."],
   "en": ["In the clip: one viewpoint with a shelter at the edge.",
          "Copper Canyon: 6 canyons, 6 rivers, 65,000 km² in the Sierra Madre Occidental.",
          "From above: a maze of ridges and gorges to the horizon."]},
  "shots": [("copper1", [0, 1]), ("copper2", [2])],
  "sources": ["https://en.wikipedia.org/wiki/Copper_Canyon"]},

 {"id": "burning", "name": {"pl": "Burning Man, Nevada", "en": "Burning Man, Nevada"},
  "spoken": {
   "pl": ["Z lotu ptaka, tak jak w kadrze, Blek Rok Siti wygląda jak uporządkowany krąg pośrodku pustyni.",
          "W dwa tysiące dziewiętnastym roku wzięło w nim udział siedemdziesiąt osiem tysięcy osiemset pięćdziesiąt osób, przez dziewięć dni do amerykańskiego Święta Pracy, na pustyni Blek Rok w Nevadzie.",
          "Na ziemi obraz jest inny: w powietrzu wisi kurz, a miasto widać z siodełka roweru, jak na tym zdjęciu Biura Zarządzania Gruntami."],
   "en": ["From the air, as in the clip, Black Rock City looks like a tidy circle in an empty desert.",
          "In twenty nineteen it had seventy-eight thousand eight hundred fifty participants, over nine days leading up to Labor Day, in the Black Rock Desert in Nevada.",
          "On the ground the picture is different: dust hangs in the air, and the city is seen from the saddle of a bicycle, as in this photograph from the Bureau of Land Management."]},
  "caption": {
   "pl": ["W kadrze: Black Rock City z lotu ptaka.",
          "2019: 78 850 uczestników, 9 dni do Labor Day, pustynia Black Rock, Nevada.",
          "Na ziemi: kurz i rowery (zdjęcie BLM, 2012)."],
   "en": ["In the clip: Black Rock City from the air.",
          "2019: 78,850 participants, 9 days up to Labor Day, Black Rock Desert, Nevada.",
          "On the ground: dust and bicycles (BLM photo, 2012)."]},
  "shots": [("burning1", [0, 1]), ("burning3", [2])],
  "sources": ["https://en.wikipedia.org/wiki/Burning_Man"]},

 {"id": "grand", "name": {"pl": "Wielki Kanion, Arizona", "en": "Grand Canyon, Arizona"},
  "spoken": {
   "pl": ["W kadrze obraz jest miękki i zamglony, a na pierwszym planie widać gałąź.",
          "Wielki Kanion ma dwieście siedemdziesiąt siedem mil, czyli czterysta czterdzieści sześć kilometrów długości, do osiemnastu mil szerokości i ponad milę głębokości.",
          "Na szlaku Brajt Endżel ścieżka to tylko cienka linia zakosów na ścianie kanionu.",
          "A o zachodzie słońca pojedynczy turysta pokazuje skalę, podczas gdy skalne świątynie poniżej łapią ostatnie światło."],
   "en": ["In the clip the image is soft and hazy, with a branch in the foreground.",
          "The Grand Canyon is two hundred seventy-seven miles, four hundred forty-six kilometres, long, up to eighteen miles wide, and over a mile deep.",
          "On the Bright Angel Trail the path is only a thin line of switchbacks down the canyon wall.",
          "And at sunset a single hiker shows the scale, while the rock temples below catch the last light."]},
  "caption": {
   "pl": ["W kadrze: miękki, zamglony obraz, gałąź na pierwszym planie.",
          "Wielki Kanion: 277 mil (446 km) długości, do 18 mil szerokości, ponad milę głębokości.",
          "Szlak Bright Angel: cienka linia zakosów na ścianie kanionu.",
          "Zachód słońca: jeden turysta pokazuje skalę."],
   "en": ["In the clip: a soft, hazy image, a branch in the foreground.",
          "Grand Canyon: 277 miles (446 km) long, up to 18 miles wide, over a mile deep.",
          "Bright Angel Trail: a thin line of switchbacks on the canyon wall.",
          "Sunset: a single hiker shows the scale."]},
  "shots": [("grand2", [0, 1]), ("grand1", [2]), ("grand3", [3])],
  "sources": ["https://en.wikipedia.org/wiki/Grand_Canyon"]},

 {"id": "ometepe", "name": {"pl": "Wyspa Ometepe, Nikaragua", "en": "Ometepe Island, Nicaragua"},
  "spoken": {
   "pl": ["Film zaczyna się od zbliżeń liści, a potem pokazuje dwa wulkany daleko za jeziorem.",
          "Ometepe to jedna wyspa zbudowana z dwóch wulkanów, Konsepsjon i Maderas, połączonych niskim przesmykiem: ma trzydzieści jeden kilometrów długości i od pięciu do dziesięciu szerokości.",
          "Konsepsjon to aktywny wulkan o symetrycznym stożku, a jego podstawa ma szesnaście kilometrów średnicy.",
          "Zbocza porasta gęsta zieleń, a wyżej grzbiet znika w chmurach."],
   "en": ["The clip begins with close-ups of leaves, and then shows two volcanoes far across the lake.",
          "Ometepe is one island built from two volcanoes, Concepción and Maderas, joined by a low isthmus: it is thirty-one kilometres long and five to ten wide.",
          "Concepción is an active volcano with a symmetrical cone, and its base is sixteen kilometres across.",
          "Its slopes are covered in dense green vegetation, and higher up the ridge disappears into cloud."]},
  "caption": {
   "pl": ["W kadrze: zbliżenia liści, potem dwa wulkany za jeziorem.",
          "Ometepe: dwa wulkany (Concepción i Maderas) połączone przesmykiem; 31 km długości, 5–10 km szerokości.",
          "Concepción: aktywny, symetryczny stożek, podstawa 16 km.",
          "Zbocza w gęstej zieleni, wyżej grzbiet w chmurach."],
   "en": ["In the clip: close-ups of leaves, then two volcanoes across the lake.",
          "Ometepe: two volcanoes (Concepción and Maderas) joined by an isthmus; 31 km long, 5–10 km wide.",
          "Concepción: an active, symmetrical cone, base 16 km across.",
          "Slopes in dense green, the ridge above lost in cloud."]},
  "shots": [("ometepe1", [0, 1, 2]), ("ometepe2", [3])],
  "sources": ["https://en.wikipedia.org/wiki/Ometepe"]},
]
