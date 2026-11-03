import csv
import io
import tempfile
import unittest
from pathlib import Path

import yaml

from image_hunt import report
from image_hunt.http import HttpError
from image_hunt.runner import run
from image_hunt.sources import commons, flickr, github, openverse, pexels, pixabay, unsplash
from image_hunt.sources.base import Ctx

from tests.fakes import FakeHttp, commons_page

ROOT = Path(__file__).resolve().parent.parent
TARGETS = yaml.safe_load((ROOT / "targets.yml").read_text(encoding="utf-8"))["targets"]


class DocumentedEndpoints(unittest.TestCase):
    """Literal URLs copied from the providers' documentation (guards against typos in constants)."""

    def test_urls(self):
        self.assertEqual(pexels.PHOTOS, "https://api.pexels.com/v1/search")
        self.assertEqual(pexels.VIDEOS, "https://api.pexels.com/v1/videos/search")
        self.assertEqual(pixabay.IMAGES, "https://pixabay.com/api/")
        self.assertEqual(pixabay.VIDEOS, "https://pixabay.com/api/videos/")
        self.assertEqual(unsplash.API, "https://api.unsplash.com/search/photos")
        self.assertEqual(flickr.API, "https://www.flickr.com/services/rest/")
        self.assertEqual(openverse.API, "https://api.openverse.org/v1")
        self.assertEqual(commons.API, "https://commons.wikimedia.org/w/api.php")
        self.assertEqual(github.API, "https://api.github.com")

    def test_targets_file_is_complete(self):
        for name, t in TARGETS.items():
            for key in ("label", "exact", "family", "brand", "queries", "commons_categories", "github_terms"):
                self.assertIn(key, t, f"{name} missing {key}")
            for field in ("exact", "family", "brand", "exclude", "require_any"):
                for pattern in t.get(field, []):
                    __import__("re").compile(pattern)


class WorkflowTests(unittest.TestCase):
    def test_workflow_is_consistent(self):
        wf = yaml.safe_load((ROOT / ".github/workflows/image-hunt.yml").read_text(encoding="utf-8"))
        text = (ROOT / ".github/workflows/image-hunt.yml").read_text(encoding="utf-8")
        trigger = wf.get("on") or wf.get(True)  # PyYAML parses a bare `on` as True
        inputs = trigger["workflow_dispatch"]["inputs"]
        for name in inputs:
            self.assertIn(f"inputs.{name}", text, f"input {name} never used")
        import re
        for used in set(re.findall(r"inputs\.(\w+)", text)):
            self.assertIn(used, inputs)
        # no user input interpolated directly into a shell script
        for step in wf["jobs"]["hunt"]["steps"]:
            self.assertNotIn("${{ inputs", step.get("run", ""))
        self.assertEqual(wf["permissions"], {"contents": "read"})
        # every secret the code can use is passed to the search step
        from image_hunt.sources import ALL
        env = next(s for s in wf["jobs"]["hunt"]["steps"] if s.get("name") == "Search")["env"]
        for mod in ALL:
            for var in mod.ENV:
                self.assertIn(var, env, f"{var} not passed to workflow")
        self.assertIn("OPENVERSE_CLIENT_ID", env)


class EndToEnd(unittest.TestCase):
    def build(self):
        pexels_photo = {"id": 1, "url": "https://www.pexels.com/photo/bajaj-pulsar-ns125-red-1/", "alt": "Pulsar NS125 | red <b>bike</b>",
                        "photographer": "Ann <script>", "src": {"original": "https://o/1.jpg", "medium": "javascript:alert(1)"}}
        pexels_other = {"id": 2, "url": "https://www.pexels.com/photo/sunset-2/", "alt": "sunset", "photographer": "Z", "src": {}}
        pexels_family = {"id": 3, "url": "https://www.pexels.com/photo/pulsar-ns200-3/", "alt": "Pulsar NS200", "photographer": "Y", "src": {}}
        routes = [
            (lambda u, p, h: u == pexels.PHOTOS, {"photos": [pexels_photo, pexels_other, pexels_family]}),
            (lambda u, p, h: u == pixabay.IMAGES, HttpError(500, "u", "boom")),
            (lambda u, p, h: u == commons.API and p.get("list") == "search", {"query": {"search": []}}),
            (lambda u, p, h: u == commons.API and p.get("list") == "categorymembers", {"query": {"categorymembers": []}}),
            (lambda u, p, h: u == commons.API and p.get("generator") == "search", {"query": {"pages": [
                commons_page(1, "File:Bajaj Pulsar NS125 front.jpg", lic="CC BY-SA 4.0"),
                commons_page(2, "File:Pulsar NS125 duplicate.jpg")]}}),
            (lambda u, p, h: u == openverse.API + "/images/", {"results": [
                {"id": "o1", "title": "Pulsar NS125 front", "url": "https://x/a.jpg", "license": "by", "license_version": "2.0",
                 "foreign_landing_url": "https://commons.wikimedia.org/wiki/File:Bajaj_Pulsar_NS125_front.jpg", "source": "wikimedia"},
                {"id": "o2", "title": "Pulsar NS125 night", "url": "https://x/b.jpg", "license": "by-nc", "license_version": "2.0",
                 "foreign_landing_url": "https://www.flickr.com/photos/a/99", "source": "flickr"}], "page_count": 1}),
        ]
        ctx = Ctx(http=FakeHttp(routes), queries=["Pulsar NS125"], target=TARGETS["pulsar-ns125"],
                  env={"PEXELS_API_KEY": "k", "PIXABAY_API_KEY": "k"})  # flickr/unsplash/github keys absent
        return run(ctx)

    def test_run(self):
        items, statuses = self.build()
        st = {s.name: s for s in statuses}
        self.assertEqual(st["flickr"].status, "skipped")
        self.assertIn("FLICKR_API_KEY", st["flickr"].message)
        self.assertEqual(st["pixabay"].status, "error")           # failure isolated
        self.assertEqual(st["pexels"].status, "ok")
        self.assertEqual(st["pexels"].dropped_other, 1)           # sunset dropped
        self.assertEqual(st["openverse"].duplicates, 1)           # commons file seen twice
        self.assertEqual(st["commons"].fetched, 2)
        titles = [(i.match, i.verdict, i.source.split("/")[0]) for i in items]
        self.assertEqual(titles[0][0], "exact")
        self.assertEqual([m for m, _, _ in titles], sorted([m for m, _, _ in titles], key={"exact": 0, "family": 1, "brand": 2}.get))
        self.assertIn(("exact", "NO", "openverse"), titles)       # NC licence flagged, not dropped
        self.assertEqual(sum(1 for i in items if i.source == "commons"), 2)

    def test_reports(self):
        items, statuses = self.build()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            report.write_all(out, items, statuses, "Bajaj Pulsar NS125", ["Pulsar NS125"])
            self.assertEqual(sorted(p.name for p in out.iterdir()),
                             ["attribution.txt", "gallery.html", "report.md", "results.csv", "results.json"])
            rows = list(csv.DictReader(io.StringIO((out / "results.csv").read_text(encoding="utf-8-sig"))))
            self.assertEqual(len(rows), len(items))
            md = (out / "report.md").read_text(encoding="utf-8")
            self.assertIn("pominięte", md)                         # skipped sources are visible
            self.assertIn("brak klucza: FLICKR_API_KEY", md)
            self.assertNotIn("<b>", md)                             # untrusted markup escaped in Markdown too
            self.assertNotIn("<script>", md)
            self.assertIn("Ann &lt;script&gt;", md)
            self.assertIn("Pulsar NS125 \\| red", md)               # pipe escaped inside table cell
            self.assertIn("brak klucza: FLICKR_API_KEY", md)
            self.assertIn("- **flickr**: pominięte", md)            # status wording consistent with the table
            page = (out / "gallery.html").read_text(encoding="utf-8")
            self.assertNotIn("<script>", page.split("<script>")[0])  # nothing injected before our own script
            self.assertNotIn("Ann <script>", page)
            self.assertNotIn('src="javascript:', page)             # unsafe thumbnail URL dropped
            self.assertIn("Ann &lt;script&gt;", page)
            credit = (out / "attribution.txt").read_text(encoding="utf-8")
            self.assertIn("CC BY-SA 4.0", credit)
            self.assertNotIn("by-nc", credit.lower())               # NC never lands in the attribution list

    def test_empty_run_still_writes_valid_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            report.write_all(Path(tmp), [], [], "X", [])
            self.assertIn("Brak trafień", (Path(tmp) / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
