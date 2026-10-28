import io
import json
import os
import unittest
from contextlib import redirect_stdout

from helpers import SITES, SKILL

import validate_jsonld


def findings(obj):
    text = obj if isinstance(obj, str) else json.dumps(obj)
    return validate_jsonld.validate_text(text, "test")[1]


def messages(obj, severity=None):
    return [f.message for f in findings(obj) if severity in (None, f.severity)]


class SyntaxTest(unittest.TestCase):
    def test_invalid_json(self):
        self.assertTrue(any("Invalid JSON" in m for m in messages('{"@type": "Thing",}', "error")))

    def test_missing_context_and_type(self):
        errs = messages({"name": "x"}, "error")
        self.assertTrue(any("@context" in m for m in errs))
        self.assertTrue(any("@type" in m for m in errs))

    def test_html_comment_wrapper_is_tolerated(self):
        self.assertEqual(messages('<!-- {"@context":"https://schema.org","@type":"WebSite","name":"a","url":"https://a.b/"} -->', "error"), [])


class RequiredPropertiesTest(unittest.TestCase):
    def test_product_needs_offer_review_or_rating(self):
        errs = messages({"@context": "https://schema.org", "@type": "Product", "name": "Mug"}, "error")
        self.assertTrue(any("offers or review or aggregateRating" in m for m in errs))

    def test_alias_types_use_parent_rules(self):
        errs = messages({"@context": "https://schema.org", "@type": "Restaurant", "name": "Diner"}, "error")
        self.assertTrue(any("address" in m for m in errs))

    def test_graph_nodes_are_validated(self):
        doc = {"@context": "https://schema.org", "@graph": [{"@type": "Event", "name": "Launch"}]}
        errs = messages(doc, "error")
        self.assertTrue(any("startDate" in m for m in errs))
        self.assertTrue(any("location" in m for m in errs))

    def test_id_references_are_not_validated_as_full_nodes(self):
        doc = {"@context": "https://schema.org", "@type": "WebSite", "name": "a", "url": "https://a.b/",
               "publisher": {"@id": "https://a.b/#org", "@type": "Organization"}}
        self.assertEqual(messages(doc, "error"), [])

    def test_breadcrumb_positions(self):
        doc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 2, "name": "A", "item": "https://a.b/"},
            {"@type": "ListItem", "position": 1, "name": "B"}]}
        self.assertTrue(any("positions" in m for m in messages(doc, "error")))


class ValueChecksTest(unittest.TestCase):
    def test_relative_urls(self):
        doc = {"@context": "https://schema.org", "@type": "Organization", "name": "A", "url": "/", "logo": "/logo.png"}
        self.assertEqual(sum("absolute" in m for m in messages(doc, "error")), 2)

    def test_bad_dates_and_prices(self):
        doc = {"@context": "https://schema.org", "@type": "Product", "name": "Mug",
               "offers": {"@type": "Offer", "price": "$19.99", "priceCurrency": "USD",
                          "availability": "in stock", "priceValidUntil": "next week"}}
        errs = messages(doc, "error")
        self.assertTrue(any("price must be a number" in m for m in errs))
        self.assertTrue(any("ISO 8601" in m for m in errs))
        self.assertTrue(any("availability" in m for m in messages(doc, "warning")))

    def test_placeholders_are_flagged(self):
        doc = {"@context": "https://schema.org", "@type": "WebSite", "name": "TODO", "url": "https://www.example.com/"}
        self.assertTrue(any("placeholder" in m for m in messages(doc, "warning")))

    def test_string_author_warns(self):
        doc = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": "x", "author": "Jane"}
        self.assertTrue(any("author should be" in m for m in messages(doc, "warning")))

    def test_retired_and_restricted_types_are_explained(self):
        self.assertTrue(messages({"@context": "https://schema.org", "@type": "HowTo", "name": "x"}, "info"))
        faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": "Q?", "acceptedAnswer": {"@type": "Answer", "text": "A."}}]}
        self.assertEqual(messages(faq, "error"), [])
        self.assertTrue(any("government/health" in m for m in messages(faq, "info")))


class TemplatesAndCliTest(unittest.TestCase):
    def test_bundled_templates_have_no_errors(self):
        jdir = os.path.join(SKILL, "assets", "jsonld")
        for name in sorted(os.listdir(jdir)):
            with self.subTest(template=name):
                with open(os.path.join(jdir, name)) as fh:
                    errors = [f for f in findings(fh.read()) if f.severity == "error"]
                self.assertEqual(errors, [])

    def test_cli_over_a_build_dir(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = validate_jsonld.main([os.path.join(SITES, "good"), "--json"])
        data = json.loads(buf.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(data["blocks"], 3)
        self.assertEqual(data["errors"], 0)

    def test_cli_fails_on_errors(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(validate_jsonld.main([os.path.join(SITES, "bad")]), 1)


if __name__ == "__main__":
    unittest.main()
