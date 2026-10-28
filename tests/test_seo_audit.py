import functools
import io
import json
import os
import threading
import unittest
from contextlib import redirect_stdout
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from helpers import ORIGIN, SITES

import seo_audit
from seo_lib import parse_html


def ids(report):
    return {i.id for p in report.pages for i in p.issues} | {i.id for i in report.site_issues}


class GoodSiteTest(unittest.TestCase):
    def test_clean_site_scores_a(self):
        report = seo_audit.audit(os.path.join(SITES, "good"), base_url=ORIGIN)
        self.assertEqual(report.mode, "dir")
        self.assertEqual(report.stats["pages"], 3, "404.html must not be audited as a page")
        self.assertGreaterEqual(report.score, 95)
        self.assertEqual(report.grade, "A")
        self.assertEqual(report.stats["errors"], 0)

    def test_works_without_base_url(self):
        report = seo_audit.audit(os.path.join(SITES, "good"))
        self.assertGreaterEqual(report.score, 90)


class BadSiteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = seo_audit.audit(os.path.join(SITES, "bad"))
        cls.ids = ids(cls.report)

    def test_flags_classic_mistakes(self):
        expected = {
            "title-multiple", "description-missing", "canonical-relative", "lang-missing", "viewport-missing",
            "charset-missing", "h1-missing", "heading-skip", "og-image-relative", "img-alt-missing",
            "jsonld-invalid", "links-not-crawlable", "meta-keywords", "render-blocking-script", "noindex",
            "broken-internal-link", "robots-blocks-all", "sitemap-missing", "page-blocked-by-robots", "h1-multiple",
        }
        self.assertTrue(expected <= self.ids, f"missing: {expected - self.ids}")

    def test_low_score(self):
        self.assertLess(self.report.score, 50)
        self.assertEqual(self.report.grade, "F")

    def test_existing_links_are_not_broken(self):
        broken = [i.message for p in self.report.pages for i in p.issues if i.id == "broken-internal-link"]
        self.assertEqual(len(broken), 1)
        self.assertIn("/missing-page/", broken[0])

    def test_every_issue_has_a_fix_hint(self):
        for p in self.report.pages:
            for i in p.issues:
                self.assertTrue(i.hint, f"no hint for {i.id}")
        for i in self.report.site_issues:
            self.assertTrue(i.hint, f"no hint for {i.id}")


class SpaShellTest(unittest.TestCase):
    def test_client_rendered_shell_is_an_error(self):
        report = seo_audit.audit(os.path.join(SITES, "spa"))
        found = ids(report)
        self.assertIn("spa-shell", found)
        self.assertNotIn("h1-missing", found, "spa-shell already explains the missing h1")
        self.assertIn("robots-missing", found)


class HtmlExtensionSiteTest(unittest.TestCase):
    def test_urls_keep_html_and_broken_images_are_found(self):
        report = seo_audit.audit(os.path.join(SITES, "html-ext"), base_url="https://rosas.example")
        self.assertEqual(sorted(p.url for p in report.pages),
                         ["https://rosas.example/", "https://rosas.example/contact.html", "https://rosas.example/menu.html"])
        broken_images = [i for p in report.pages for i in p.issues if i.id == "broken-image"]
        self.assertEqual([i.url for i in broken_images], ["https://rosas.example/menu.html"])
        self.assertNotIn("broken-internal-link", ids(report))

    def test_url_variants_are_one_page(self):
        from seo_lib import url_key
        keys = {url_key(u) for u in ("https://a.b/menu", "https://a.b/menu/", "/menu.html", "/menu/index.html")}
        self.assertEqual(keys, {"/menu"})
        self.assertEqual(url_key("https://a.b/"), "/")


class HreflangTest(unittest.TestCase):
    def test_reciprocity_and_codes(self):
        report = seo_audit.audit(os.path.join(SITES, "hreflang"), base_url=ORIGIN)
        found = ids(report)
        self.assertIn("hreflang-invalid", found)
        self.assertIn("hreflang-not-reciprocal", found)
        self.assertIn("hreflang-no-x-default", found)


class RobotsTest(unittest.TestCase):
    def test_longest_match_wins_and_allow_breaks_ties(self):
        groups = seo_audit.parse_robots("User-agent: *\nDisallow: /private/\nAllow: /private/press/\nDisallow: /*.pdf$\n")
        self.assertTrue(seo_audit.robots_disallows(groups, "/private/x"))
        self.assertFalse(seo_audit.robots_disallows(groups, "/private/press/kit"))
        self.assertTrue(seo_audit.robots_disallows(groups, "/files/a.pdf"))
        self.assertFalse(seo_audit.robots_disallows(groups, "/files/a.pdf?x=1"))
        self.assertFalse(seo_audit.robots_disallows(groups, "/"))

    def test_grouped_user_agents_share_rules(self):
        groups = seo_audit.parse_robots("User-agent: GPTBot\nUser-agent: CCBot\nDisallow: /\n\nUser-agent: *\nAllow: /\n")
        self.assertTrue(seo_audit.robots_disallows(groups, "/", "GPTBot"))
        self.assertTrue(seo_audit.robots_disallows(groups, "/", "ccbot"))
        self.assertFalse(seo_audit.robots_disallows(groups, "/", "Googlebot"))

    def test_robots_checks(self):
        issues, _ = seo_audit.check_robots("User-agent: *\nDisallow: /\n", "x")
        self.assertEqual({i.id for i in issues}, {"robots-blocks-all", "robots-no-sitemap"})
        issues, _ = seo_audit.check_robots("User-agent: *\nDisallow: /_next/\nSitemap: https://a.b/s.xml\n", "x")
        self.assertEqual({i.id for i in issues}, {"robots-blocks-assets"})
        self.assertEqual(seo_audit.check_robots(None, "x")[0][0].id, "robots-missing")


class PageCheckTest(unittest.TestCase):
    def check(self, html, url="https://www.example.com/page", home=False):
        return {i.id for i in seo_audit.check_page(parse_html(html, url), ORIGIN, home)}

    def test_noindex_with_foreign_canonical_conflicts(self):
        found = self.check('<html lang=en><head><meta name=robots content="noindex,follow">'
                           '<link rel=canonical href="https://www.example.com/other"></head><body></body></html>')
        self.assertIn("canonical-noindex-conflict", found)

    def test_mixed_content(self):
        found = self.check('<html><body><img src="http://cdn.example.com/a.png" alt="a"></body></html>')
        self.assertIn("mixed-content", found)

    def test_x_robots_tag_header_counts_as_noindex(self):
        page = parse_html("<html><body><h1>x</h1></body></html>", "https://www.example.com/", x_robots_tag="noindex")
        self.assertTrue(page.is_noindex)

    def test_svg_title_is_not_the_page_title(self):
        page = parse_html("<html><head><title>Real</title></head><body><svg><title>icon</title></svg></body></html>", "/")
        self.assertEqual(page.titles, ["Real"])

    def test_page_score_counts_each_issue_once(self):
        issues = [seo_audit.Issue("img-alt-missing", "warning", "x")] * 10
        self.assertEqual(seo_audit.page_score(issues), 95)


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class UrlModeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = functools.partial(_QuietHandler, directory=os.path.join(SITES, "good"))
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}/"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_crawls_same_origin_links(self):
        report = seo_audit.audit(self.base, crawl=10)
        self.assertEqual(report.mode, "url")
        self.assertEqual(len(report.pages), 3)
        site_ids = {i.id for i in report.site_issues}
        self.assertNotIn("robots-missing", site_ids)
        self.assertNotIn("sitemap-missing", site_ids)
        self.assertNotIn("llms-txt-missing", site_ids)

    def test_crawl_limit(self):
        self.assertEqual(len(seo_audit.audit(self.base, crawl=1).pages), 1)

    def test_404_is_reported(self):
        report = seo_audit.audit(self.base + "nope/", crawl=1)
        self.assertIn("http-error", ids(report))

    def test_cli_json_and_fail_under(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = seo_audit.main([os.path.join(SITES, "bad"), "--json", "--fail-under", "90"])
        self.assertEqual(code, 1)
        data = json.loads(buf.getvalue())
        self.assertIn("score", data)
        self.assertTrue(all("hint" in i for p in data["pages"] for i in p["issues"]))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(seo_audit.main([os.path.join(SITES, "good"), "--fail-under", "90"]), 0)


if __name__ == "__main__":
    unittest.main()
