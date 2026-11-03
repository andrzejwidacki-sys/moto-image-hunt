import io
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from image_hunt import fetch_images
from image_hunt.http import HttpError
from image_hunt.models import Item


def png(w=200, h=100, color=(200, 30, 30)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, "PNG")
    return buf.getvalue()


def make(id, match="exact", verdict="OK", kind="image", title="Bajaj Pulsar NS125", thumb="https://t/{}.jpg", file="https://f/{}.jpg"):
    return Item(source="commons", kind=kind, id=str(id), title=title, page_url=f"https://p/{id}", file_url=file.format(id),
                thumb_url=thumb.format(id), creator="Ann <b>", license="CC0 1.0", license_url="", verdict=verdict,
                attribution_required=False, match=match)


class FakeBytes:
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def get_bytes(self, url, max_bytes=8_000_000, timeout=60):
        self.calls.append(url)
        r = self.routes[url]
        if isinstance(r, Exception):
            raise r
        return r


class PickTests(unittest.TestCase):
    def test_filters_order_and_limit(self):
        items = [make(1, "brand"), make(2, "exact", "CHECK"), make(3, "exact", "NO"), make(4, "family"),
                 make(5, "exact", kind="video"), make(6, "exact"), make(7, "other")]
        got = [i.id for i in fetch_images.pick(items, {"exact", "family", "brand"}, 10)]
        self.assertEqual(got, ["6", "2", "4", "1"])          # exact OK, exact CHECK, family, brand; NO/video/other gone
        self.assertEqual([i.id for i in fetch_images.pick(items, {"exact"}, 1)], ["6"])


class ShrinkTests(unittest.TestCase):
    def test_big_png_becomes_small_jpeg(self):
        out = fetch_images.shrink(png(4000, 3000))
        im = Image.open(io.BytesIO(out))
        self.assertEqual(im.format, "JPEG")
        self.assertLessEqual(max(im.size), 1280)

    def test_non_image_raises(self):
        with self.assertRaises(Exception):
            fetch_images.shrink(b"<html>not an image</html>")


class RunTests(unittest.TestCase):
    def test_download_fallback_index_and_local_gallery(self):
        items = [make(1), make(2), make(3), make(4), make(5, verdict="NO")]
        routes = {
            "https://t/1.jpg": (png(), "image/png"),                       # fine
            "https://t/2.jpg": HttpError(429, "https://t/2.jpg", "slow down"),  # preview refused -> full file
            "https://f/2.jpg": (png(300, 300), "image/png"),
            "https://t/3.jpg": (b"<html>captcha</html>", "text/html"),    # not an image
            "https://f/3.jpg": HttpError(404, "https://f/3.jpg", "gone"),
            "https://t/4.jpg": (b"garbage", "image/jpeg"),                  # claims image, is not
            "https://f/4.jpg": (b"garbage", "image/jpeg"),
        }
        http = FakeBytes(routes)
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "results.json").write_text(json.dumps({"target": "Bajaj Pulsar NS125", "items": [i.as_dict() for i in items]}))
            ok, failed = fetch_images.run(d, http, {"exact"}, 80)
            self.assertEqual((ok, failed), (2, 2))
            self.assertNotIn("https://t/5.jpg", http.calls)                 # NO-licence item never downloaded
            index = json.loads((d / "images/index.json").read_text())
            self.assertEqual([bool(e["file"]) for e in index], [True, True, False, False])
            self.assertEqual(index[1]["error"], "")                         # fallback to the full file worked
            self.assertIn("text/html", index[2]["error"])                   # failures are recorded, not raised
            self.assertIn("404", index[2]["error"])
            self.assertTrue(index[3]["error"])
            for e in index[:2]:
                self.assertTrue((d / e["file"]).is_file())
                with Image.open(d / e["file"]) as im:
                    self.assertEqual(im.format, "JPEG")
            page = (d / "gallery.html").read_text()
            self.assertIn(f'src="{index[0]["file"]}"', page)                # local copy used instead of hot-link
            self.assertNotIn("https://t/1.jpg", page)
            self.assertNotIn("Ann <b>", page)                               # still escaped


if __name__ == "__main__":
    unittest.main()
