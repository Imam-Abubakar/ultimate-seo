import os
import unittest

from helpers import PROJECTS, SKILL

import detect_stack


def detect(name):
    return detect_stack.detect(os.path.join(PROJECTS, name))


class FrameworkDetectionTest(unittest.TestCase):
    CASES = {
        "nextjs-app": ("nextjs", "nextjs-app-router.md"),
        "nextjs-pages": ("nextjs", "nextjs-pages-router.md"),
        "vite-react": ("react-spa", "react-spa.md"),
        "cra": ("react-spa", "react-spa.md"),
        "vue-spa": ("vue-spa", "react-spa.md"),
        "astro": ("astro", "astro.md"),
        "nuxt": ("nuxt", "nuxt-vue.md"),
        "sveltekit": ("sveltekit", "sveltekit.md"),
        "gatsby": ("gatsby", "gatsby.md"),
        "angular": ("angular", "angular.md"),
        "remix": ("remix", "react-router-remix.md"),
        "react-router": ("react-router-framework", "react-router-remix.md"),
        "hugo": ("hugo", "static-site-generators.md"),
        "jekyll": ("jekyll", "static-site-generators.md"),
        "django": ("django", "server-rendered.md"),
        "rails": ("rails", "server-rendered.md"),
        "laravel": ("laravel", "server-rendered.md"),
        "wordpress": ("wordpress", "cms-platforms.md"),
        "shopify": ("shopify-theme", "cms-platforms.md"),
        "static-html": ("static-html", "static-html.md"),
        "empty": ("unknown", "static-html.md"),
    }

    def test_frameworks_and_references(self):
        for project, (framework, reference) in self.CASES.items():
            with self.subTest(project=project):
                r = detect(project)
                self.assertEqual(r["framework"], framework)
                self.assertTrue(r["reference"].endswith(reference), r["reference"])

    def test_every_reported_reference_exists(self):
        for project in self.CASES:
            with self.subTest(project=project):
                self.assertTrue(os.path.isfile(os.path.join(SKILL, detect(project)["reference"])))

    def test_next_router_and_rendering(self):
        self.assertEqual(detect("nextjs-app")["router"], "app")
        pages = detect("nextjs-pages")
        self.assertEqual(pages["router"], "pages")
        self.assertEqual(pages["rendering"], "static-export")
        self.assertEqual(pages["build_output"], "out")

    def test_versions_and_language(self):
        r = detect("nextjs-app")
        self.assertEqual(r["version"], "16.0.1")
        self.assertEqual(r["language"], "typescript")

    def test_rendering_modes(self):
        self.assertIn("spa", detect("vite-react")["rendering"])
        self.assertEqual(detect("sveltekit")["rendering"], "ssg")
        self.assertEqual(detect("angular")["rendering"], "ssr")


class ArtifactAndConfigTest(unittest.TestCase):
    def test_existing_seo_artifacts(self):
        r = detect("nextjs-app")
        self.assertIn("app/robots.ts", r["existing_seo"]["robots"])
        self.assertIn("app/layout.tsx", r["existing_seo"]["meta_description_in_source"])
        self.assertIn("public/favicon.svg", detect("vite-react")["existing_seo"]["favicon"])

    def test_seo_libraries_and_i18n(self):
        self.assertIn("next-seo", detect("nextjs-pages")["seo_libraries"])
        nuxt = detect("nuxt")
        self.assertIn("@nuxtjs/seo", nuxt["seo_libraries"])
        self.assertIn("@nuxtjs/i18n", nuxt["i18n"])

    def test_site_url_candidates(self):
        expected = {
            "nextjs-app": "https://www.acme.dev",
            "astro": "https://astro-site.dev",
            "hugo": "https://hugo-site.org",
            "jekyll": "https://jekyll-site.org",
            "static-html": "https://static-site.net",
            "cra": "https://cra.example.org",
        }
        for project, url in expected.items():
            with self.subTest(project=project):
                self.assertIn(url, [c["url"] for c in detect(project)["site_url_candidates"]])

    def test_env_files_only_yield_url_values(self):
        sources = detect("nextjs-app")["site_url_candidates"]
        self.assertTrue(all(c["url"].startswith("https://") for c in sources))
        self.assertNotIn("do-not-read", str(sources))

    def test_monorepo_lists_apps(self):
        r = detect("monorepo")
        self.assertEqual(r["framework"], "monorepo")
        apps = {a["path"]: a["framework"] for a in r["monorepo_apps"]}
        self.assertEqual(apps, {"apps/web": "nextjs", "apps/docs": "astro"})

    def test_cli_text_and_json(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            detect_stack.main([os.path.join(PROJECTS, "astro")])
        self.assertIn("Read next:", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
