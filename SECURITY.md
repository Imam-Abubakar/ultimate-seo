# Security Policy

## Supported versions

Only the latest release receives fixes.

## Scope

The bundled scripts read local files and, when given a URL, make HTTP GET requests to that URL and same-origin links. They never execute fetched content, send data elsewhere, or write outside the directory you point them at (`generate_sitemap.py` writes `sitemap.xml` into the target directory only).

Relevant reports include: path traversal or unexpected writes, crawling outside the given origin, parsing bugs that hang or crash on hostile HTML or XML, and skill instructions that could lead Claude to take unsafe actions (for example leaking secrets from `.env` files into output).

## Reporting a vulnerability

Please **don't open a public issue**. Use GitHub's [private vulnerability reporting](../../security/advisories/new) instead. Expect an acknowledgement within 72 hours and a fix or mitigation plan within 14 days for confirmed issues.
