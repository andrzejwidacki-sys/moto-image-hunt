import unittest

from image_hunt.models import CHECK, NO, OK, Item, classify, dedupe_keys, judge_license

NS125 = {
    "exact": [r"\bns ?125\b", r"\b125 ?ns\b"], "require_any": ["pulsar", "bajaj"],
    "exclude": ["honda", "nsr ?125", "neutron", "millisecond", "astronom"],
    "family": [r"\bns ?(125|150|160|180|200)\b", r"\b(125|150|160|180|200) ?ns\b", "rouser"],
    "brand": ["pulsar", "bajaj"],
}


def item(title="", **kw):
    base = dict(source="x", kind="image", id="1", title=title, page_url="", file_url="", thumb_url="", creator="",
                license="", license_url="", verdict=OK, attribution_required=False)
    base.update(kw)
    return Item(**base)


class LicenseTests(unittest.TestCase):
    def check(self, raw, verdict, attr=None, label=None, unknown=NO):
        lab, ver, att, _ = judge_license(raw, unknown)
        self.assertEqual(ver, verdict, f"{raw!r} -> {lab} {ver}")
        if attr is not None:
            self.assertEqual(att, attr, raw)
        if label is not None:
            self.assertEqual(lab, label, raw)

    def test_free_ok(self):
        self.check("CC BY 2.0", OK, True, "CC BY 2.0")
        self.check("CC BY-SA 4.0", OK, True, "CC BY-SA 4.0")
        self.check("CC BY 4.0 International", OK, True, "CC BY 4.0")
        self.check("Attribution License", OK, True)
        self.check("Attribution-ShareAlike License", OK, True, "CC BY-SA")
        self.check("CC0", OK, False, "CC0 1.0")
        self.check("CC0 1.0", OK, False)
        self.check("CC-0", OK, False)
        self.check("Public domain", OK, False)
        self.check("Public Domain Mark", OK, False)
        self.check("Public Domain Dedication (CC0)", OK, False)
        self.check("PD-self", OK, False)
        self.check("United States Government Work", OK, False)
        self.check("Pexels License", OK, False)

    def test_needs_check(self):
        self.check("CC BY-ND 2.0", CHECK, True, "CC BY-ND 2.0")
        self.check("Attribution-NoDerivs License", CHECK, True)
        self.check("No known copyright restrictions", CHECK)
        self.check("GFDL 1.2 or later", CHECK)
        self.check("Copyrighted free use", CHECK)
        self.check("FAL", CHECK)

    def test_not_allowed(self):
        self.check("CC BY-NC 2.0", NO)
        self.check("CC BY-NC-SA 4.0", NO)
        self.check("CC BY-NC-ND 2.0", NO)
        self.check("Attribution-NonCommercial License", NO)
        self.check("Attribution Non-Commercial", NO)
        self.check("All rights reserved", NO)
        self.check("", NO)
        self.check("something weird", NO)

    def test_unknown_policy(self):
        self.check("", CHECK, unknown=CHECK)  # Commons: unknown name -> CHECK, not NO
        self.check("Standard licence by Foo", NO)  # 'by' alone must not become CC BY


class ClassifyTests(unittest.TestCase):
    def test_levels(self):
        cases = [
            ("Bajaj Pulsar NS125 red", "exact"), ("pulsar-ns-125.jpg", "exact"), ("Pulsar 125NS", "exact"),
            ("Bajaj Pulsar NS200", "family"), ("Pulsar 200 NS grey", "family"), ("Bajaj Pulsar 150", "brand"),
            ("Honda NS125R", "other"), ("Honda NS125R Pulsar comparison", "other"),
            ("Millisecond pulsar NASA", "other"), ("Pulsar astronomical object NS125", "other"),
            ("Random bike", "other"), ("NS125 scooter", "family"),
        ]
        for title, expect in cases:
            self.assertEqual(classify(item(title), NS125), expect, title)

    def test_category_and_url_text_count(self):
        self.assertEqual(classify(item("IMG_0042.jpg", categories=["Bajaj Pulsar NS125"]), NS125), "exact")
        self.assertEqual(classify(item("", page_url="https://pexels.com/photo/bajaj-pulsar-ns125-red-123/"), NS125), "exact")


class DedupeTests(unittest.TestCase):
    def test_same_flickr_photo_two_hosts(self):
        a = item(page_url="https://www.flickr.com/photos/someone/123456/")
        b = item(page_url="http://flickr.com/photos/12345@N01/123456")
        self.assertTrue(dedupe_keys(a) & dedupe_keys(b))

    def test_commons_url_encoding(self):
        a = item(page_url="https://commons.wikimedia.org/wiki/File:Pulsar_NS125.jpg")
        b = item(page_url="https://commons.wikimedia.org/wiki/File:Pulsar%20NS125.jpg")
        self.assertTrue(dedupe_keys(a) & dedupe_keys(b))

    def test_different_photos(self):
        a = item(page_url="https://www.flickr.com/photos/x/1")
        b = item(page_url="https://www.flickr.com/photos/x/2")
        self.assertFalse(dedupe_keys(a) & dedupe_keys(b))


if __name__ == "__main__":
    unittest.main()


class CrossSourceDedupeTests(unittest.TestCase):
    def test_commons_file_and_openverse_copy_collapse(self):
        commons = item("Bajaj pulsar NS 125.jpg", creator="Kolomoiskii",
                       page_url="https://commons.wikimedia.org/wiki/File:Bajaj_pulsar_NS_125.jpg",
                       file_url="https://upload.wikimedia.org/wikipedia/commons/a/ab/Bajaj_pulsar_NS_125.jpg")
        openverse = item("Bajaj pulsar NS 125", creator="Kolomoiskii",
                         page_url="https://commons.wikimedia.org/w/index.php?curid=177459220",
                         file_url="https://upload.wikimedia.org/wikipedia/commons/thumb/x.jpg")
        self.assertTrue(dedupe_keys(commons) & dedupe_keys(openverse))
        prefixed = item("File:Bajaj Pulsar 200 NS.jpg", creator="25 Cents FC", page_url="https://a/1")
        plain = item("Bajaj Pulsar 200 NS.jpg", creator="25 Cents FC", page_url="https://b/2")
        self.assertTrue(dedupe_keys(prefixed) & dedupe_keys(plain))

    def test_same_title_different_author_is_not_merged(self):
        a = item("Pulsar NS125", creator="Ann", page_url="https://a/1")
        b = item("Pulsar NS125", creator="Bob", page_url="https://b/2")
        self.assertFalse(dedupe_keys(a) & dedupe_keys(b))
        c = item("Pulsar NS125", creator="", page_url="https://c/3")
        d = item("Pulsar NS125", creator="", page_url="https://d/4")
        self.assertFalse(dedupe_keys(c) & dedupe_keys(d))  # no author -> never merge on title alone
