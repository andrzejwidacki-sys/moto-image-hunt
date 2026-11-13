# Wgrywanie dużych plików (filmy)

Czat przyjmuje pliki do 30 MiB, a sandbox ma dostęp tylko do GitHub. Darmowy hosting dużych plików:
**GitHub Releases** (do 2 GiB na plik, bez limitu łącznego, stałe linki bezpośrednie).
Sesja Claude nie może tworzyć wydań przez API, więc robi to workflow `release-publish.yml`.

```bash
# 1) pliki na osobną gałąź (orphan); pojedynczy plik < 100 MB, bo tyle przyjmuje git
git init -q -b film1-upload up && cp film1_*.mp4 CREDITS.md up/ && cd up
git add . && git commit -qm "film1 files" && git push -f <remote> film1-upload
# 2) workflow tworzy wydanie i wgrywa pliki
gh api -X POST repos/<owner>/<repo>/actions/workflows/release-publish.yml/dispatches --input body.json
# body.json: {"ref":"main","inputs":{"branch":"film1-upload","tag":"film1-commentary-v1","title":"...","notes":"..."}}
```

Linki: `https://github.com/<owner>/<repo>/releases/download/<tag>/<plik>`.
Pliki większe niż 100 MB: wgraj je z lokalnego komputera (`gh release upload <tag> plik`), bez gałęzi pośredniej.
