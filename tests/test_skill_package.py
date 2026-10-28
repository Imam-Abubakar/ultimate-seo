import os
import re
import sys
import unittest

from helpers import ROOT, SKILL

sys.path.insert(0, os.path.join(ROOT, "tools"))
import validate_skill  # noqa: E402


class SkillPackageTest(unittest.TestCase):
    def test_package_is_valid(self):
        self.assertEqual(validate_skill.check(), [])

    def test_playbook_template_has_required_sections(self):
        text = open(os.path.join(SKILL, "assets", "ULTIMATE-SEO.template.md"), encoding="utf-8").read()
        for heading in ("## Scorecard", "## What was implemented", "## Configuration you must fill in",
                        "## Launch checklist", "## Roadmap", "## Every time you add a page", "## Monitoring"):
            self.assertIn(heading, text)

    def test_skill_md_names_every_playbook_section(self):
        skill = open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8").read()
        for phrase in ("Scorecard", "What was implemented", "Configuration you must fill in",
                       "Launch checklist", "Prioritized roadmap", "Per-page checklist", "Monitoring"):
            self.assertIn(phrase, skill)

    def test_robots_template_never_blocks_everything(self):
        text = open(os.path.join(SKILL, "assets", "robots.txt"), encoding="utf-8").read()
        active = [l for l in text.splitlines() if l and not l.startswith("#")]
        self.assertIn("User-agent: *", active)
        self.assertNotIn("Disallow: /", active)
        self.assertTrue(any(l.startswith("Sitemap: https://") for l in active))

    def test_llms_txt_template_follows_spec_shape(self):
        text = open(os.path.join(SKILL, "assets", "llms.txt"), encoding="utf-8").read()
        self.assertTrue(text.startswith("# "))
        self.assertRegex(text, r"\n> .+")
        self.assertRegex(text, r"\n## .+\n\n- \[.+\]\(https://")

    def test_references_avoid_deprecated_advice(self):
        """Guard against regressions like recommending FID or meta keywords."""
        rules = [
            (r"\bFID\b", r"replac|retire|deprecat|former|old|no longer|instead"),
            (r'(?i)<meta name="keywords"', r"ignore|don't|do not|\bno\b|remove|avoid|never"),
        ]
        refs = os.path.join(SKILL, "references")
        for dirpath, _, files in os.walk(refs):
            for f in files:
                text = open(os.path.join(dirpath, f), encoding="utf-8").read()
                for pattern, caveat in rules:
                    for m in re.finditer(pattern, text):
                        window = text[max(0, m.start() - 150): m.end() + 150]
                        with self.subTest(file=f, match=m.group(0)):
                            self.assertRegex(window.lower(), caveat,
                                             f"{f}: {m.group(0)!r} mentioned without a deprecation caveat")


if __name__ == "__main__":
    unittest.main()
