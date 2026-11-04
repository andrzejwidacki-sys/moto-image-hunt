# moto-image-hunt

Workflow GitHub Actions, który szuka zdjęć i wideo wybranego motocykla w darmowych bazach i **sprawdza ich licencje pod kątem użycia w filmie na YouTube / w social mediach** (użycie komercyjne + montaż).

Gotowe cele: **pulsar-ns125** (domyślny), **pulsar-ns200**, **honda-ns125**. Commons jest przeszukiwany także po danych strukturalnych („przedstawia: Pulsar 200NS”), więc znajduje zdjęcia o nazwach typu `IMG_1234.jpg`; identyfikator Wikidata jest przy każdym przebiegu weryfikowany po etykiecie. Własny model dodasz w `targets.yml`.

## Źródła

| Źródło | Klucz API | Co przeszukuje |
|---|---|---|
| Wikimedia Commons | nie | całe drzewa kategorii (`Category:Bajaj Pulsar` i znalezione kategorie z „Pulsar NS”), pełnotekstowe wyszukiwanie plików, prawdziwe kategorie każdego pliku, wideo |
| Flickr | `FLICKR_API_KEY` (klucz wydaje Flickr tylko kontom Pro, po weryfikacji) | tylko licencje pozwalające na użycie komercyjne (CC BY, BY-SA, BY-ND, CC0, PD, gov) |
| Pexels | `PEXELS_API_KEY` (stan na 3.11.2026 Pexels wstrzymał wydawanie nowych kluczy) | zdjęcia i wideo |
| Pixabay | `PIXABAY_API_KEY` | zdjęcia i wideo |
| Unsplash | `UNSPLASH_ACCESS_KEY` | zdjęcia |
| GitHub | wbudowany `GITHUB_TOKEN` | pliki graficzne ze ścieżką zawierającą nazwę modelu (zawsze `CHECK`/`NO`, nigdy `OK`) |
| Openverse | opcjonalnie `OPENVERSE_CLIENT_ID` / `_SECRET` | agregator CC (Flickr, Wikimedia, muzea); bez kluczy działa w trybie anonimowym |

Źródło bez klucza jest **pomijane** i widać to w raporcie (nie psuje przebiegu).

## Uruchomienie

1. Utwórz repozytorium i wgraj te pliki.
2. Bez żadnych kluczy działają: Wikimedia Commons, GitHub i Openverse (anonimowo). Opcjonalnie dodaj w *Settings → Secrets and variables → Actions → New repository secret*:
   - `PIXABAY_API_KEY` - darmowe konto na pixabay.com; po zalogowaniu klucz widać na https://pixabay.com/api/docs/ przy parametrze `key`.
   - `UNSPLASH_ACCESS_KEY` - darmowe konto, https://unsplash.com/developers → nowa aplikacja → **Access Key** (nie Secret Key).
   - `FLICKR_API_KEY` - tylko konto Flickr Pro (płatne); zdjęcia z Flickra na licencjach CC częściowo pokrywa też Openverse.
   - `PEXELS_API_KEY` - dopóki Pexels nie wznowi wydawania kluczy, pomiń.
3. *Actions → Image hunt → Run workflow*. Parametry: cel, dodatkowe frazy (oddzielone `;`), limit wyników na zapytanie, wideo tak/nie, lista źródeł.
4. Wynik: tabela w *Summary* przebiegu oraz artefakt `image-hunt-results`:
   - `report.md` - ile trafień na jakiej stronie (dokładnie ten model / rodzina / sama marka × OK/CHECK/NO)
   - `gallery.html` - galeria z filtrami (otwórz po rozpakowaniu artefaktu)
   - `results.csv`, `results.json` - pełne dane (linki, autor, licencja)
   - `attribution.txt` - gotowe podpisy do opisu filmu dla trafień wymagających atrybucji

## Podglądy zdjęć i gałąź `results`

Po wyszukiwaniu workflow pobiera podglądy najlepszych trafień (do `max_images`, domyślnie 80; tylko zdjęcia z werdyktem OK lub CHECK, zmniejszone do 1280 px) i zapisuje wszystkie wyniki na osobnej gałęzi **`results-<cel>`**, np. `results-pulsar-ns200` (każdy cel ma własną gałąź, nadpisywaną przy kolejnym przebiegu tego celu; `main` zostaje czysta). Znajdziesz tam `report.md`, `results.csv`, `attribution.txt`, `gallery.html` oraz folder `images/` z `index.json` (autor, licencja, link do źródła dla każdego podglądu). Wyłączysz to parametrem `publish_results`.

Podglądy to kopie do przeglądania - przed użyciem w filmie pobierz oryginał ze strony źródła i podaj autora, jeśli licencja tego wymaga. W repozytorium publicznym gałąź `results` jest widoczna dla wszystkich; jeśli to nie ma być publiczne, ustaw repozytorium jako prywatne.

## Jak czytać werdykty

- **OK** - komercyjnie + montaż dozwolone (CC BY i BY-SA wymagają podpisu autora; BY-SA: przeróbka na tej samej licencji).
- **CHECK** - np. CC BY-ND (kadrowanie i cięcie w filmie może być „przeróbką”), GFDL, „no known copyright restrictions”, repozytoria GitHub.
- **NO** - NC, „all rights reserved”, brak licencji.

Poziom dopasowania: `exact` = model w tytule/opisie/kategorii/URL, `family` = inny Pulsar NS (160/200…), `brand` = sama marka. Dopasowanie to wyrażenia regularne z `targets.yml`, **nie rozpoznawanie obrazu** - sprawdź zdjęcie oczami.

## Co jest zweryfikowane, a co nie

Testy offline (`python -m unittest discover -s tests`, uruchamiane też w workflow) sprawdzają logikę licencji, klasyfikację, deduplikację, parsowanie odpowiedzi i raporty na atrapach API. **Atrapy odwzorowują format odpowiedzi tak, jak go opisałem, więc nie dowodzą, że prawdziwe API odpowiada identycznie.**

Potwierdzone w dokumentacji: endpointy i parametry Pexels (w tym `/v1/videos/search`), Pixabay (200/stronę, limit 500, wideo), identyfikatory licencji Flickra, `license_type=commercial` i przepływ tokenu w Openverse.
Niepotwierdzone w dokumentacji (z pamięci): dokładny kształt odpowiedzi Wikimedia `imageinfo/extmetadata`, nazwy części pól Openverse, nagłówek autoryzacji Unsplash, działanie wyszukiwania kodu GitHub z tokenem Actions. **Pierwszy przebieg jest właściwym testem** - źródło, które się nie zgadza, pokaże `błąd` z komunikatem w raporcie, a pozostałe i tak dadzą wyniki.

## Ograniczenia

- Pixabay: maks. 500 trafień na zapytanie, 100 zapytań/min, wyniki mają być cache'owane 24 h i nie wolno masowo pobierać - nie uruchamiaj przebiegu w pętli. Miniatury w galerii to tymczasowe podglądy; wybrane pliki pobierz.
- Flickr zwraca najwyżej ok. 4000 wyników na zapytanie; Unsplash (klucz demo) ma niski limit godzinowy; wyszukiwanie kodu GitHub ok. 10 zapytań/min (stąd wolniejszy przebieg).
- Licencję deklaruje uploader. Zdarza się błędna (np. cudze zdjęcie wrzucone jako CC). Przed publikacją otwórz stronę zdjęcia.
- Licencja zdjęcia nie obejmuje znaków towarowych ani rozpoznawalnych osób.

## Dodanie modelu

W `targets.yml` skopiuj blok `pulsar-ns125`, zmień `label`, wyrażenia (`exact`, `family`, `brand`, `exclude`), `queries`, kategorie Commons i `github_terms`, a następnie podaj nazwę bloku w polu `target` przy uruchomieniu.
