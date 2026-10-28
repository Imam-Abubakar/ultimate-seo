import os
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET

from helpers import ORIGIN, SITES

import generate_sitemap

NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


class GenerateSitemapTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        for site in ("good", "bad"):
            shutil.copytree(os.path.join(SITES, site), os.path.join(self.tmp, site))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def locs(self, path):
        return [el.text for el in ET.parse(path).getroot().iter(NS + "loc")]

    def test_writes_canonical_indexable_urls(self):
        root = os.path.join(self.tmp, "good")
        os.remove(os.path.join(root, "sitemap.xml"))
        self.assertEqual(generate_sitemap.main([root, "--base-url", ORIGIN]), 0)
        locs = self.locs(os.path.join(root, "sitemap.xml"))
        self.assertEqual(locs, [f"{ORIGIN}/", f"{ORIGIN}/about/", f"{ORIGIN}/blog/hello-world/"])

    def test_no_trailing_slash_and_no_fake_lastmod(self):
        root = os.path.join(self.tmp, "plain")
        os.makedirs(os.path.join(root, "about"))
        with open(os.path.join(root, "about", "index.html"), "w") as fh:
            fh.write("<html><head><title>About</title></head><body><h1>About</h1></body></html>")
        generate_sitemap.main([root, "--base-url", ORIGIN + "/", "--no-trailing-slash"])
        path = os.path.join(root, "sitemap.xml")
        self.assertEqual(self.locs(path), [f"{ORIGIN}/about"])
        with open(path) as fh:
            self.assertNotIn("lastmod", fh.read())

    def test_page_canonical_decides_the_url_form(self):
        root = os.path.join(self.tmp, "good")
        generate_sitemap.main([root, "--base-url", ORIGIN, "--no-trailing-slash"])
        self.assertIn(f"{ORIGIN}/about/", self.locs(os.path.join(root, "sitemap.xml")))

    def test_html_extension_sites_keep_their_urls(self):
        shutil.copytree(os.path.join(SITES, "html-ext"), os.path.join(self.tmp, "html-ext"))
        urls, skipped = generate_sitemap.collect_urls(os.path.join(self.tmp, "html-ext"), "https://rosas.example", True, "none")
        self.assertEqual([u for u, _ in urls], ["https://rosas.example/", "https://rosas.example/contact.html",
                                                 "https://rosas.example/menu.html"])
        self.assertEqual(skipped, [])
        urls, _ = generate_sitemap.collect_urls(os.path.join(self.tmp, "good"), ORIGIN, True, "none", keep_extension=True)
        self.assertIn(f"{ORIGIN}/about/", [u for u, _ in urls])

    def test_skips_noindex_and_foreign_canonicals(self):
        urls, skipped = generate_sitemap.collect_urls(os.path.join(self.tmp, "bad"), ORIGIN, True, "none")
        self.assertEqual([u for u, _ in urls], [f"{ORIGIN}/"])
        self.assertTrue(any("noindex" in s for s in skipped))

    def test_mtime_lastmod_is_iso(self):
        urls, _ = generate_sitemap.collect_urls(os.path.join(self.tmp, "good"), ORIGIN, True, "mtime")
        self.assertRegex(urls[0][1], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00$")

    def test_splits_into_index_over_limit(self):
        root = os.path.join(self.tmp, "good")
        old = generate_sitemap.MAX_URLS
        generate_sitemap.MAX_URLS = 2
        try:
            generate_sitemap.main([root, "--base-url", ORIGIN])
        finally:
            generate_sitemap.MAX_URLS = old
        index = ET.parse(os.path.join(root, "sitemap.xml")).getroot()
        self.assertEqual(index.tag, NS + "sitemapindex")
        self.assertEqual(self.locs(os.path.join(root, "sitemap.xml")), [f"{ORIGIN}/sitemap-0.xml", f"{ORIGIN}/sitemap-1.xml"])

    def test_rejects_relative_base_url(self):
        with self.assertRaises(SystemExit):
            generate_sitemap.main([self.tmp, "--base-url", "example.com"])


if __name__ == "__main__":
    unittest.main()
