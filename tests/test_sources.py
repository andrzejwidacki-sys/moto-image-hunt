import unittest

from image_hunt.http import HttpError
from image_hunt.models import CHECK, NO, OK
from image_hunt.sources import commons, flickr, github, openverse, pexels, pixabay, unsplash
from image_hunt.sources.base import Ctx, slug_title, strip_html

from tests.fakes import FakeHttp, commons_page

TARGET = {
    "commons_categories": ["Category:Bajaj Pulsar"], "commons_category_search": ["Pulsar NS125"],
    "commons_category_filter": "bajaj|pulsar ?(ns|n)", "github_terms": ["ns125"],
}


def ctx(http, **kw):
    kw.setdefault("queries", ["Pulsar NS125"])
    kw.setdefault("env", {"FLICKR_API_KEY": "k", "PEXELS_API_KEY": "k", "PIXABAY_API_KEY": "k",
                          "UNSPLASH_ACCESS_KEY": "k", "GITHUB_TOKEN": "t"})
    return Ctx(http=http, target=TARGET, **kw)


def api(param, value=None):
    return lambda url, p, h: param in p and (value is None or p[param] == value)


class HelperTests(unittest.TestCase):
    def test_helpers(self):
        self.assertEqual(strip_html("<a href='x'>Jan &amp; Ewa</a>"), "Jan & Ewa")
        self.assertEqual(slug_title("https://www.pexels.com/photo/urban-biker-on-sports-motorcycle-in-ankara-34807170/"),
                         "urban biker on sports motorcycle in ankara")


class CommonsTests(unittest.TestCase):
    def make(self):
        cat_files = {"query": {"categorymembers": [
            {"ns": 6, "title": "File:IMG_1234.jpg"}, {"ns": 14, "title": "Category:Bajaj Pulsar NS125"}]}}
        sub_files = {"query": {"categorymembers": [{"ns": 6, "title": "File:Pulsar NS125 red.jpg"}]}}
        # a title-batch lookup: categories arrive in a second 'continue' response and must be merged
        first = {"continue": {"clcontinue": "1|x", "continue": "||"}, "query": {"pages": [
            commons_page(1, "File:IMG_1234.jpg", cats=["Bajaj Pulsar NS125"]),
            commons_page(2, "File:Pulsar NS125 red.jpg", lic="CC BY 2.0")]}}
        first["query"]["pages"][0]["categories"] = []  # categories not yet delivered
        second = {"query": {"pages": [{"pageid": 1, "ns": 6, "title": "File:IMG_1234.jpg",
                                       "categories": [{"ns": 14, "title": "Category:Bajaj Pulsar NS125"}]}]}}
        titles_calls = []

        def titles(url, p):
            titles_calls.append(p)
            return second if "clcontinue" in p else first

        search_hit = {"query": {"pages": [
            commons_page(3, "File:Honda NS125R.jpg"), commons_page(4, "File:Pulsar NS125 clip.webm", mime="video/webm"),
            commons_page(5, "File:Document.pdf", mime="application/pdf"),
            commons_page(6, "File:Public.jpg", lic="", copyrighted="False")]}}
        routes = [
            (lambda u, p, h: p.get("list") == "search", {"query": {"search": [
                {"title": "Category:Bajaj Pulsar NS125"}, {"title": "Category:Pulsars"}]}}),
            (lambda u, p, h: p.get("cmtitle") == "Category:Bajaj Pulsar", cat_files),
            (lambda u, p, h: p.get("cmtitle") == "Category:Bajaj Pulsar NS125", sub_files),
            (api("titles"), titles),
            (api("generator", "search"), search_hit),
        ]
        return FakeHttp(routes), titles_calls

    def test_category_walk_search_and_merge(self):
        http, titles_calls = self.make()
        c = ctx(http, include_video=False)
        items = list(commons.search(c))
        by_id = {i.id: i for i in items}
        self.assertEqual(set(by_id), {"File:IMG_1234.jpg", "File:Pulsar NS125 red.jpg", "File:Honda NS125R.jpg", "File:Public.jpg"})
        self.assertIn("Bajaj Pulsar NS125", by_id["File:IMG_1234.jpg"].categories)  # merged from continuation
        red = by_id["File:Pulsar NS125 red.jpg"]
        self.assertEqual((red.license, red.verdict, red.attribution_required), ("CC BY 2.0", OK, True))
        self.assertEqual(red.creator, "Jan Kowalski")  # HTML stripped
        self.assertEqual(red.page_url, "https://commons.wikimedia.org/wiki/File:Pulsar_NS125_red.jpg")
        self.assertEqual(by_id["File:Public.jpg"].license, "Public domain")  # Copyrighted=False fallback
        self.assertNotIn("File:Pulsar NS125 clip.webm", by_id)  # video off
        self.assertTrue(any("Pulsars" not in n for n in c.notes))
        walked = [p for u, p in http.calls if p.get("list") == "categorymembers"]
        self.assertEqual({p["cmtitle"] for p in walked}, {"Category:Bajaj Pulsar", "Category:Bajaj Pulsar NS125"})
        self.assertNotIn("Category:Pulsars", {p["cmtitle"] for p in walked})  # astronomy filtered out

    def test_video_included_on_request(self):
        http, _ = self.make()
        items = list(commons.search(ctx(http, include_video=True)))
        clip = [i for i in items if i.id.endswith(".webm")]
        self.assertEqual(len(clip), 1)
        self.assertEqual(clip[0].kind, "video")

    def test_unknown_license_is_check_not_no(self):
        page = commons_page(9, "File:X.jpg", lic="Strange free licence")
        self.assertEqual(commons.to_item(page, "q", False).verdict, CHECK)


class OpenverseTests(unittest.TestCase):
    def test_pagination_and_mapping(self):
        r = lambda i, lic, ver: {"id": f"id{i}", "title": f"Pulsar NS125 {i}", "creator": "Ann", "url": f"https://img/{i}.jpg",
                                 "thumbnail": f"https://t/{i}.jpg", "foreign_landing_url": f"https://www.flickr.com/photos/a/{i}",
                                 "license": lic, "license_version": ver, "license_url": "https://cc", "source": "flickr",
                                 "tags": [{"name": "bajaj"}], "width": 10, "height": 20}
        pages = {1: {"results": [r(1, "by", "2.0"), r(2, "by-nd", "2.0")], "page_count": 2},
                 2: {"results": [r(3, "cc0", "1.0")], "page_count": 2}}
        http = FakeHttp([(lambda u, p, h: u.endswith("/images/"), lambda u, p: pages[p["page"]])])
        items = list(openverse.search(ctx(http)))
        self.assertEqual([i.verdict for i in items], [OK, CHECK, OK])
        self.assertEqual(items[2].license, "CC0 1.0")
        self.assertEqual(items[0].source, "openverse/flickr")
        self.assertTrue(all(p.get("license_type") == "commercial" for u, p in http.calls))

    def test_stops_quietly_past_depth_limit(self):
        def route(u, p):
            if p["page"] == 1:
                return {"results": [{"id": "a", "url": "https://i/a.jpg", "license": "by", "license_version": "4.0"}], "page_count": 9}
            raise HttpError(401, u, "anonymous depth limit")
        http = FakeHttp([(lambda u, p, h: True, route)])
        self.assertEqual(len(list(openverse.search(ctx(http)))), 1)

    def test_oauth_token_used_when_configured(self):
        http = FakeHttp([(lambda u, p, h: True, {"results": [], "page_count": 0})])
        c = ctx(http, env={"OPENVERSE_CLIENT_ID": "a", "OPENVERSE_CLIENT_SECRET": "b"})
        list(openverse.search(c))
        self.assertTrue(any("auth_tokens" in u for u, _ in http.calls))


class FlickrTests(unittest.TestCase):
    P = {"id": "42", "owner": "123@N01", "ownername": "Gabriel", "secret": "s", "server": "65535", "title": "Bajaj Pulsar NS125",
         "license": "5", "tags": "bajaj pulsar", "description": {"_content": "my bike"}, "media": "photo", "url_m": "https://m/42.jpg"}

    def test_mapping_and_licence_filter(self):
        http = FakeHttp([(lambda u, p, h: True, {"stat": "ok", "photos": {"page": 1, "pages": 1, "photo": [self.P, {**self.P, "id": "43", "license": "6"}]}})])
        items = list(flickr.search(ctx(http)))
        self.assertEqual((items[0].license, items[0].verdict), ("CC BY-SA 2.0", OK))
        self.assertEqual(items[1].verdict, CHECK)
        self.assertEqual(items[0].page_url, "https://www.flickr.com/photos/123@N01/42")
        self.assertEqual(items[0].tags, ["bajaj", "pulsar"])
        sent = http.calls[0][1]["license"]
        self.assertNotIn("0", sent.split(",")[:1])  # never asks for all-rights-reserved
        self.assertEqual(set(sent.split(",")), {"4", "5", "6", "7", "8", "9", "10"})

    def test_api_error_surfaces(self):
        http = FakeHttp([(lambda u, p, h: True, {"stat": "fail", "code": 100, "message": "Invalid API Key"})])
        with self.assertRaises(HttpError):
            list(flickr.search(ctx(http)))


class PexelsPixabayUnsplashTests(unittest.TestCase):
    def test_pexels_photo_and_video_endpoints(self):
        photo = {"id": 7, "url": "https://www.pexels.com/photo/bajaj-pulsar-ns125-7/", "alt": "Red bajaj pulsar", "photographer": "Ann",
                 "width": 1, "height": 2, "src": {"original": "https://o", "medium": "https://m"}}
        video = {"id": 8, "url": "https://www.pexels.com/video/bajaj-pulsar-ride-8/", "image": "https://v/p.jpg", "user": {"name": "Bob"},
                 "video_files": [{"link": "https://v/sd.mp4", "width": 640}, {"link": "https://v/hd.mp4", "width": 1920}]}
        http = FakeHttp([(lambda u, p, h: u == pexels.PHOTOS, {"photos": [photo]}),
                         (lambda u, p, h: u == pexels.VIDEOS, {"videos": [video]})])
        items = list(pexels.search(ctx(http, include_video=True)))
        self.assertEqual([(i.kind, i.verdict) for i in items], [("image", OK), ("video", OK)])
        self.assertEqual(items[1].file_url, "https://v/hd.mp4")
        self.assertEqual(items[1].title, "bajaj pulsar ride")
        self.assertEqual(http.calls[0][1]["per_page"], 80)

    def test_pixabay_cap_and_video_thumbnail(self):
        hit = {"id": 1, "pageURL": "https://pixabay.com/photos/x-1/", "tags": "motorcycle, bajaj, bike", "user": "u",
               "largeImageURL": "https://l", "previewURL": "https://p", "imageWidth": 5, "imageHeight": 6}
        vhit = {"id": 2, "pageURL": "https://pixabay.com/videos/y-2/", "tags": "bajaj, ride", "user": "v",
                "videos": {"large": {"url": ""}, "medium": {"url": "https://m.mp4", "width": 1920, "height": 1080},
                           "tiny": {"url": "https://t.mp4", "thumbnail": "https://th.jpg"}}}
        http = FakeHttp([(lambda u, p, h: u == pixabay.IMAGES, {"hits": [hit], "totalHits": 1, "total": 90}),
                         (lambda u, p, h: u == pixabay.VIDEOS, {"hits": [vhit], "totalHits": 1})])
        items = list(pixabay.search(ctx(http, include_video=True)))
        self.assertEqual(items[0].tags, ["motorcycle", "bajaj", "bike"])
        self.assertEqual((items[1].file_url, items[1].thumb_url), ("https://m.mp4", "https://th.jpg"))
        self.assertEqual(len(http.calls), 2)  # totalHits=1 -> no second page requested

    def test_unsplash_rate_limit_keeps_partial(self):
        r = {"id": "a", "alt_description": "motorcycle", "urls": {"small": "s", "full": "f"}, "links": {"html": "https://unsplash.com/photos/a"},
             "user": {"name": "Zed"}, "tags": [{"title": "bajaj"}]}

        def route(u, p):
            if p["page"] == 1:
                return {"results": [r], "total_pages": 3}
            raise HttpError(403, u, "Rate Limit Exceeded")
        c = ctx(FakeHttp([(lambda u, p, h: True, route)]))
        items = list(unsplash.search(c))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].tags, ["bajaj"])
        self.assertTrue(any("limit" in n for n in c.notes))


class GithubTests(unittest.TestCase):
    def test_never_ok_and_repo_licence_mapping(self):
        def code(u, p):
            return {"items": [
                {"name": "ns125.jpg", "path": "img/ns125.jpg", "html_url": "https://github.com/a/lic/blob/main/img/ns125.jpg",
                 "repository": {"full_name": "a/lic"}},
                {"name": "ns125.png", "path": "ns125.png", "html_url": "https://github.com/b/nolic/blob/main/ns125.png",
                 "repository": {"full_name": "b/nolic"}}]} if p["page"] == 1 and "extension:jpg" in p["q"] else {"items": []}
        http = FakeHttp([(lambda u, p, h: u.endswith("/search/code"), code),
                         (lambda u, p, h: u.endswith("/repos/a/lic"), {"license": {"spdx_id": "MIT"}}),
                         (lambda u, p, h: u.endswith("/repos/b/nolic"), {"license": None})])
        items = list(github.search(ctx(http)))
        self.assertEqual({i.verdict for i in items}, {CHECK, NO})
        self.assertNotIn(OK, {i.verdict for i in items})
        self.assertIn("/raw/main/", items[0].file_url)
        self.assertEqual([i.license for i in items], ["repo: MIT", "repo: no licence"])

    def test_rate_limit_is_noted_not_fatal(self):
        c = ctx(FakeHttp([(lambda u, p, h: True, HttpError(403, "u", "rate"))]))
        self.assertEqual(list(github.search(c)), [])
        self.assertTrue(c.notes)


if __name__ == "__main__":
    unittest.main()
