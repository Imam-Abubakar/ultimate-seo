"""Shared paths and imports for the test suite."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "ultimate-seo")
SCRIPTS = os.path.join(SKILL, "scripts")
FIXTURES = os.path.join(ROOT, "tests", "fixtures")
SITES = os.path.join(FIXTURES, "sites")
PROJECTS = os.path.join(FIXTURES, "projects")
ORIGIN = "https://www.example.com"

if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
