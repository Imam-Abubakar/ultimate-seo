# Contributing to Ultimate SEO

Thanks for helping make this the best SEO skill there is. This guide covers how the project is organized, what makes a good contribution, and how to get a PR merged quickly.

## Contents

- [Ground rules](#ground-rules)
- [Setup](#setup)
- [How the skill is structured](#how-the-skill-is-structured)
- [Common contributions](#common-contributions)
- [Writing style for skill content](#writing-style-for-skill-content)
- [Testing your change](#testing-your-change)
- [Pull request checklist](#pull-request-checklist)
- [Releasing](#releasing)

## Ground rules

- **Accuracy beats volume.** Every claim in `references/` should be true today and traceable to a primary source (Google Search Central, schema.org, framework docs, web.dev, the crawler operator's docs). Mark time-sensitive facts with *"verify against current docs"* and the source URL.
- **No fabricated data, ever.** Examples and templates use obvious placeholders (`example.com`, `Example Brand`). The skill must never invent ratings, reviews, addresses or social profiles for a user's site.
- **Zero runtime dependencies.** Scripts are Python 3.9+ standard library only, so they run anywhere Claude can run Python.
- **Idiomatic over generic.** Framework guides show the way an experienced developer in that framework would do it, using current APIs, and note version differences.
- Be kind. This project follows our [Code of Conduct](CODE_OF_CONDUCT.md).

## Setup

```bash
git clone https://github.com/Imam-Abubakar/ultimate-seo.git
```

```bash
cd ultimate-seo && make test
```

That's it: there's nothing to install. To try the skill live in Claude Code, symlink it into your skills directory so edits take effect immediately:

```bash
ln -s "$PWD/skills/ultimate-seo" ~/.claude/skills/ultimate-seo
```

## How the skill is structured

Skills load in three layers, and keeping each layer lean is what makes the skill fast and reliable:

| Layer | File | Loaded | Budget |
|---|---|---|---|
| 1. Metadata | `description` in `SKILL.md` frontmatter | Always | ≤ 1024 chars, no angle brackets |
| 2. Workflow | `SKILL.md` body | When the skill triggers | < 500 lines |
| 3. Detail | `references/**`, `assets/**`, `scripts/**` | Only when needed | Unlimited, but use a **Contents** section above 300 lines |

`SKILL.md` holds the workflow and guardrails. It tells Claude *which* reference to read, and `detect_stack.py` returns the right framework guide path. If you add a file that `SKILL.md` never mentions, Claude will never read it, and the package linter will fail.

## Common contributions

### Add or improve a framework guide

1. Create `skills/ultimate-seo/references/frameworks/<stack>.md` with these sections, in order: **Contents, Detect, Where things go, Site config**, implementation sections, **Structured data, Verify, Pitfalls**. Copy the shape of an existing guide such as `astro.md`.
2. Implement all 12 baseline items from `SKILL.md` idiomatically, with complete, copy-pasteable code.
3. Add detection to `scripts/detect_stack.py` in `detect_framework()`. Order matters: meta-frameworks come before the libraries they wrap (Next.js before React).
4. Add a fixture project under `tests/fixtures/projects/<stack>/` with the minimal files that identify it, and add a row to `FrameworkDetectionTest.CASES`.
5. List the file in the **Reference map** in `SKILL.md` and in the README's supported-stacks table.

### Add an audit check

1. Add the check in `check_page()` (per page) or `site_checks()` (site-wide) in `scripts/seo_audit.py`, with an `id`, a severity and a clear message.
2. Add a one-line fix in `FIX_HINTS`. A test fails if any issue lacks a hint.
3. Choose severity carefully. `error` means it actively harms indexing or rich results. `warning` means a likely problem. `info` means nice to have.
4. Add a fixture case (usually in `tests/fixtures/sites/bad/`) and a test.

### Update structured-data rules

Edit `RULES`, `ALIASES` or `RETIRED` in `scripts/validate_jsonld.py`, and update `references/structured-data.md` to match. Link the Google doc that changed in your PR.

### Add an eval case

Eval cases live in `skills/ultimate-seo/evals/<case-name>/` in the [`claude plugin eval`](https://code.claude.com/docs) layout:

```text
<case-name>/
├── prompt.md        # settings block, then the user's prompt exactly as they'd type it
├── case.yaml        # schema_version "1.1", name, expected_outcome, scaffold_script
├── place-files.sh   # copies files/ into the run directory
├── graders/NN-*.md  # one verifiable statement per file
└── files/           # the input project
```

Good prompts are messy and realistic: casual phrasing, real-looking domains, and business details. Good graders are objectively checkable statements about the result, such as "app/sitemap.ts includes a URL for every post in lib/posts.ts", not "the SEO is good".

## Writing style for skill content

- Write instructions in the imperative and **explain why**. Claude follows reasons better than rigid MUSTs, and reasons generalize to cases the rule didn't anticipate.
- Be dense. Each paragraph should change what Claude does, so cut anything that would be true of any website.
- Keep code examples complete and current. Note version splits inline, for example *"Next 15+: params is a Promise; on 14 drop the await"*.
- Mark uncertainty honestly instead of guessing.

## Testing your change

```bash
make lint   # tools/validate_skill.py: frontmatter, links, manifests, eval layout
make test   # lint + all unit tests
```

For changes to `SKILL.md` or the references, also run at least one eval case end to end (`make eval`, or ask Claude to run a case with the skill) and describe the outcome in your PR. Behavioural changes without an eval run are hard to review.

## Pull request checklist

- [ ] `make test` passes
- [ ] New facts cite a primary source; time-sensitive ones say "verify against current docs"
- [ ] New reference files are linked from `SKILL.md`
- [ ] Scripts still have zero dependencies and support `--help`
- [ ] `CHANGELOG.md` has an entry under **Unreleased**
- [ ] For behavioural changes: which eval(s) you ran and what changed

## Releasing

1. Bump `metadata.version` in `SKILL.md`, `version` in `.claude-plugin/plugin.json`, and the plugin entry in `.claude-plugin/marketplace.json`. The linter checks that they match.
2. Move **Unreleased** entries in `CHANGELOG.md` under the new version.
3. Tag `vX.Y.Z` and attach `dist/ultimate-seo.zip` (`make package`) to the GitHub release.
