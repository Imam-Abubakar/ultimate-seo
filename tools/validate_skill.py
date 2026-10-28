#!/usr/bin/env python3
"""Lint the ultimate-seo skill package. Run before every PR:

    python3 tools/validate_skill.py

Checks the SKILL.md frontmatter against the Agent Skills spec, that every file
SKILL.md points to exists (and every reference is reachable from SKILL.md),
that long references have a table of contents, that the plugin manifests
agree on the version, and that eval cases have the layout `claude plugin eval`
expects. Standard library only.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from typing import List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "ultimate-seo")
ALLOWED_KEYS = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}


def parse_frontmatter(text: str):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, text
    data, parent = {}, None
    for line in m.group(1).splitlines():
        if not line.strip():
            continue
        if line.startswith("  ") and parent:
            k, _, v = line.strip().partition(":")
            data[parent][k.strip()] = v.strip()
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        if v == "":
            data[k], parent = {}, k
        else:
            data[k], parent = v, None
    return data, text[m.end():]


def check() -> List[str]:
    errors: List[str] = []
    skill_md = os.path.join(SKILL, "SKILL.md")
    text = open(skill_md, encoding="utf-8").read()
    fm, body = parse_frontmatter(text)
    if fm is None:
        return ["SKILL.md: missing YAML frontmatter"]

    unexpected = set(fm) - ALLOWED_KEYS
    if unexpected:
        errors.append(f"SKILL.md: unexpected frontmatter keys {sorted(unexpected)}")
    name = fm.get("name", "")
    if name != "ultimate-seo" or not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64:
        errors.append(f"SKILL.md: bad name {name!r}")
    desc = fm.get("description", "")
    if not desc:
        errors.append("SKILL.md: missing description")
    if len(desc) > 1024:
        errors.append(f"SKILL.md: description is {len(desc)} chars (max 1024)")
    if "<" in desc or ">" in desc:
        errors.append("SKILL.md: description must not contain angle brackets")
    lines = text.count("\n")
    if lines > 500:
        errors.append(f"SKILL.md: {lines} lines; keep it under 500 and move detail to references/")

    # Every referenced path exists.
    for rel in sorted(set(re.findall(r"`((?:references|scripts|assets)/[\w./-]+)`", text))):
        if "*" in rel:
            continue
        if not os.path.exists(os.path.join(SKILL, rel)):
            errors.append(f"SKILL.md: references missing path {rel}")
    mentioned = set(re.findall(r"`([\w.-]+\.(?:md|py|json|txt))`", text))
    for sub in ("references", "references/frameworks", "scripts"):
        for f in sorted(os.listdir(os.path.join(SKILL, sub))):
            path = os.path.join(SKILL, sub, f)
            if not os.path.isfile(path) or f.startswith(("_", ".")) or f == "seo_lib.py":
                continue
            if f not in mentioned and f"{sub}/{f}" not in text:
                errors.append(f"{sub}/{f}: not mentioned in SKILL.md, so Claude will never load it")
    for f in mentioned:
        if f.endswith(".md") and f not in ("SKILL.md", "ULTIMATE-SEO.md") and not any(
                os.path.exists(os.path.join(SKILL, d, f)) for d in ("references", "references/frameworks", "assets")):
            errors.append(f"SKILL.md: mentions {f} but no such file exists")

    # Long references need a table of contents; relative links must resolve.
    for d in ("references", "references/frameworks"):
        for f in sorted(os.listdir(os.path.join(SKILL, d))):
            if not f.endswith(".md"):
                continue
            path = os.path.join(SKILL, d, f)
            content = open(path, encoding="utf-8").read()
            if content.count("\n") > 300 and not re.search(r"^#+\s*Contents", content, re.M):
                errors.append(f"{d}/{f}: over 300 lines without a 'Contents' section")
            if not content.startswith("# "):
                errors.append(f"{d}/{f}: should start with a '# Title'")
            for link in re.findall(r"\]\((?!https?://|#|mailto:)([^)\s]+\.md)(?:#[^)]*)?\)", content):
                if not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(path), link))):
                    errors.append(f"{d}/{f}: broken link {link}")

    # Scripts run and document themselves.
    for f in sorted(os.listdir(os.path.join(SKILL, "scripts"))):
        if f.endswith(".py") and f != "seo_lib.py":
            res = subprocess.run([sys.executable, os.path.join(SKILL, "scripts", f), "--help"],
                                 capture_output=True, text=True, timeout=30)
            if res.returncode != 0 or "usage" not in res.stdout.lower():
                errors.append(f"scripts/{f}: --help failed: {res.stderr.strip()[:200]}")

    # JSON assets parse.
    jdir = os.path.join(SKILL, "assets", "jsonld")
    for f in sorted(os.listdir(jdir)):
        try:
            json.load(open(os.path.join(jdir, f), encoding="utf-8"))
        except ValueError as e:
            errors.append(f"assets/jsonld/{f}: invalid JSON: {e}")

    # Plugin manifests agree with SKILL.md.
    version = (fm.get("metadata") or {}).get("version")
    for manifest in (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"):
        path = os.path.join(ROOT, manifest)
        try:
            data = json.load(open(path, encoding="utf-8"))
        except (OSError, ValueError) as e:
            errors.append(f"{manifest}: {e}")
            continue
        versions = [data.get("version")] if "plugins" not in data else [p.get("version") for p in data["plugins"]]
        for v in versions:
            if v and v != version:
                errors.append(f"{manifest}: version {v} != SKILL.md metadata.version {version}")

    # Eval cases follow the `claude plugin eval` layout.
    edir = os.path.join(SKILL, "evals")
    cases = [c for c in sorted(os.listdir(edir)) if os.path.isdir(os.path.join(edir, c))] if os.path.isdir(edir) else []
    if not cases:
        errors.append("evals/: no eval cases")
    for case in cases:
        cdir = os.path.join(edir, case)
        if not re.fullmatch(r"[a-z][a-z0-9-]*", case):
            errors.append(f"evals/{case}: case names are lowercase-with-hyphens")
        prompt = os.path.join(cdir, "prompt.md")
        if not os.path.isfile(prompt) or not open(prompt, encoding="utf-8").read().startswith("---\n"):
            errors.append(f"evals/{case}/prompt.md: missing or has no settings block")
        case_yaml = os.path.join(cdir, "case.yaml")
        cy = open(case_yaml, encoding="utf-8").read() if os.path.isfile(case_yaml) else ""
        if 'schema_version: "' not in cy or f"name: {case}\n" not in cy:
            errors.append(f"evals/{case}/case.yaml: needs quoted schema_version and name: {case}")
        if "scaffold_script" in cy and not os.path.isfile(os.path.join(cdir, "place-files.sh")):
            errors.append(f"evals/{case}: case.yaml names a scaffold script that doesn't exist")
        gdir = os.path.join(cdir, "graders")
        graders = sorted(os.listdir(gdir)) if os.path.isdir(gdir) else []
        if not graders:
            errors.append(f"evals/{case}: no graders")
        for g in graders:
            if not open(os.path.join(gdir, g), encoding="utf-8").read().startswith("---\ntype:"):
                errors.append(f"evals/{case}/graders/{g}: missing grader frontmatter")
    return errors


def main() -> int:
    errors = check()
    for e in errors:
        print(f"✗ {e}")
    if errors:
        print(f"\n{len(errors)} problem(s) found.")
        return 1
    print("✓ Skill package is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
