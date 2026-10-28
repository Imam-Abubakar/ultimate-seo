#!/usr/bin/env python3
"""Validate JSON-LD structured data against Google's rich-result requirements.

Examples:
  validate_jsonld.py dist                      # every HTML file in a build
  validate_jsonld.py https://example.com/post  # a live page
  validate_jsonld.py page.html schema.json     # files (.html or raw .json)
  validate_jsonld.py dist --json --strict      # CI: warnings fail too

This is a fast offline linter, not a replacement for Google's Rich Results
Test (https://search.google.com/test/rich-results). It catches the mistakes
that most often cost rich results: syntax errors, missing required
properties, relative URLs, placeholder values and retired types.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seo_lib import extract_jsonld_blocks, fetch, is_url, iter_html_files, load_json_lenient  # noqa: E402

# type -> (required, recommended). "a|b" means at least one of them.
# Based on Google Search Central structured data docs; re-check
# https://developers.google.com/search/docs/appearance/structured-data/search-gallery when updating.
RULES: Dict[str, Tuple[List[str], List[str]]] = {
    "Organization": ([], ["name", "url", "logo", "sameAs"]),
    "WebSite": ([], ["name", "url"]),
    "BreadcrumbList": (["itemListElement"], []),
    "ListItem": (["position", "name|item"], []),
    "Article": ([], ["headline", "image", "datePublished", "dateModified", "author"]),
    "Product": (["name", "offers|review|aggregateRating"], ["image", "description", "sku", "brand"]),
    "Offer": (["price|priceSpecification"], ["priceCurrency", "availability", "url"]),
    "AggregateOffer": (["lowPrice"], ["priceCurrency", "offerCount", "highPrice"]),
    "AggregateRating": (["ratingValue", "ratingCount|reviewCount"], ["bestRating"]),
    "Review": (["author", "reviewRating|reviewBody"], ["datePublished"]),
    "Rating": (["ratingValue"], ["bestRating"]),
    "LocalBusiness": (["name", "address"], ["telephone", "url", "openingHoursSpecification", "geo", "image", "priceRange"]),
    "PostalAddress": ([], ["streetAddress", "addressLocality", "postalCode", "addressCountry"]),
    "Event": (["name", "startDate", "location"], ["endDate", "eventStatus", "eventAttendanceMode", "image", "description", "offers", "organizer"]),
    "FAQPage": (["mainEntity"], []),
    "Question": (["name", "acceptedAnswer"], []),
    "Answer": (["text"], []),
    "SoftwareApplication": (["name"], ["offers", "aggregateRating|review", "applicationCategory", "operatingSystem"]),
    "Recipe": (["name", "image"], ["author", "datePublished", "description", "recipeIngredient", "recipeInstructions", "totalTime"]),
    "JobPosting": (["title", "description", "datePublished", "hiringOrganization", "jobLocation|applicantLocationRequirements"],
                   ["validThrough", "employmentType", "baseSalary", "identifier"]),
    "VideoObject": (["name", "thumbnailUrl", "uploadDate"], ["description", "duration", "contentUrl|embedUrl"]),
    "Person": (["name"], ["url", "sameAs"]),
    "ProfilePage": (["mainEntity"], []),
    "Course": (["name", "description"], ["provider"]),
    "Dataset": (["name", "description"], ["license", "creator"]),
    "ImageObject": (["contentUrl|url"], []),
}

ALIASES = {
    "BlogPosting": "Article", "NewsArticle": "Article", "TechArticle": "Article", "Report": "Article",
    "MobileApplication": "SoftwareApplication", "WebApplication": "SoftwareApplication", "VideoGame": "SoftwareApplication",
    "Corporation": "Organization", "NGO": "Organization", "OnlineStore": "Organization", "EducationalOrganization": "Organization",
    "NewsMediaOrganization": "Organization", "OnlineBusiness": "Organization",
    "Restaurant": "LocalBusiness", "Store": "LocalBusiness", "Dentist": "LocalBusiness", "MedicalClinic": "LocalBusiness",
    "ProfessionalService": "LocalBusiness", "HomeAndConstructionBusiness": "LocalBusiness", "AutoRepair": "LocalBusiness",
    "LegalService": "LocalBusiness", "FinancialService": "LocalBusiness", "HealthAndBeautyBusiness": "LocalBusiness",
    "FoodEstablishment": "LocalBusiness", "LodgingBusiness": "LocalBusiness", "Hotel": "LocalBusiness", "CafeOrCoffeeShop": "LocalBusiness",
    "ProductGroup": "Product", "MusicEvent": "Event", "BusinessEvent": "Event", "EducationEvent": "Event",
}

RETIRED = {
    "HowTo": "HowTo rich results were removed by Google in 2023; the markup is harmless but earns nothing in Google Search.",
    "SpecialAnnouncement": "SpecialAnnouncement rich results were retired by Google.",
    "ClaimReview": "ClaimReview (fact check) rich results were phased out by Google in 2025.",
    "EstimatedSalary": "Estimated salary rich results were retired by Google in 2025.",
    "Vehicle": "Vehicle listing rich results were retired by Google in 2025.",
}

URL_KEYS = {"url", "logo", "image", "item", "thumbnailUrl", "contentUrl", "embedUrl", "sameAs", "@id", "mainEntityOfPage"}
DATE_KEYS = {"datePublished", "dateModified", "dateCreated", "uploadDate", "startDate", "endDate", "validThrough", "priceValidUntil", "validFrom"}
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?$")
PLACEHOLDER = re.compile(r"(example\.(com|org)|\bTODO\b|\bTBD\b|YOUR[_ -]|REPLACE[_ -]?ME|lorem ipsum|\{\{.*\}\}|__[A-Z_]+__)", re.I)
AVAILABILITY = re.compile(r"^(https?://schema\.org/)?(InStock|OutOfStock|PreOrder|BackOrder|Discontinued|InStoreOnly|LimitedAvailability|OnlineOnly|PreSale|SoldOut|Reserved|MadeToOrder)$")


@dataclass
class Finding:
    severity: str  # error | warning | info
    source: str
    path: str
    message: str


def types_of(node: Dict[str, Any]) -> List[str]:
    t = node.get("@type")
    if isinstance(t, str):
        return [t]
    if isinstance(t, list):
        return [x for x in t if isinstance(x, str)]
    return []


def has(node: Dict[str, Any], spec: str) -> bool:
    for key in spec.split("|"):
        v = node.get(key)
        if v not in (None, "", [], {}):
            return True
    return False


def validate_node(node: Any, source: str, path: str, out: List[Finding], top_level: bool = False,
                  primary: bool = False) -> None:
    """primary: a page-level entity (top level, @graph member or mainEntity) that gets
    recommended-property checks; nested helpers (an author, an organizer) only get required ones."""
    if isinstance(node, list):
        for i, item in enumerate(node):
            validate_node(item, source, f"{path}[{i}]", out, top_level, primary)
        return
    if not isinstance(node, dict):
        return

    if top_level:
        ctx = node.get("@context")
        if ctx is None:
            out.append(Finding("error", source, path, "Missing @context (use \"https://schema.org\")"))
        elif isinstance(ctx, str) and "schema.org" not in ctx:
            out.append(Finding("warning", source, path, f"Unexpected @context {ctx!r}"))

    if "@graph" in node:
        validate_node(node["@graph"], source, f"{path}.@graph", out, primary=True)

    types = types_of(node)
    if not types and "@graph" not in node and top_level:
        out.append(Finding("error", source, path, "Missing @type"))
    label = "/".join(types) or "node"
    here = f"{path}<{label}>"

    for t in types:
        if t in RETIRED:
            out.append(Finding("info", source, here, RETIRED[t]))
        if t == "FAQPage":
            out.append(Finding("info", source, here, "FAQ rich results only show for authoritative government/health sites; "
                                                      "keep FAQPage only where the Q&A is visible on the page."))
        rule = RULES.get(ALIASES.get(t, t))
        # Only nodes that stand on their own need the full rule set; a reference
        # like {"@id": "..."} is a pointer to a node defined elsewhere in the graph.
        is_reference = set(node.keys()) <= {"@id", "@type"}
        if rule and not is_reference:
            required, recommended = rule
            for spec in required:
                if not has(node, spec):
                    out.append(Finding("error", source, here, f"Missing required property {spec.replace('|', ' or ')}"))
            for spec in (recommended if primary or top_level else []):
                if not has(node, spec):
                    out.append(Finding("warning", source, here, f"Missing recommended property {spec.replace('|', ' or ')}"))

        canon = ALIASES.get(t, t)
        if canon == "Article":
            headline = node.get("headline")
            if isinstance(headline, str) and len(headline) > 110:
                out.append(Finding("warning", source, here, f"headline is {len(headline)} chars; keep it ≤110"))
            author = node.get("author")
            for a in author if isinstance(author, list) else [author]:
                if isinstance(a, str):
                    out.append(Finding("warning", source, here, "author should be a Person/Organization object, not a string"))
        if canon in ("Offer", "AggregateOffer"):
            price = node.get("price", node.get("lowPrice"))
            if isinstance(price, str) and re.search(r"[^\d.]", price):
                out.append(Finding("error", source, here, f"price must be a number like \"19.99\" (no currency symbols): {price!r}"))
            avail = node.get("availability")
            if isinstance(avail, str) and not AVAILABILITY.match(avail):
                out.append(Finding("warning", source, here, f"availability should be a schema.org URL like https://schema.org/InStock: {avail!r}"))
        if canon == "BreadcrumbList":
            items = node.get("itemListElement")
            if isinstance(items, list):
                positions = [i.get("position") for i in items if isinstance(i, dict)]
                if positions and positions != list(range(1, len(positions) + 1)):
                    out.append(Finding("error", source, here, f"breadcrumb positions should be 1..n in order, got {positions}"))
        if canon in ("AggregateRating", "Review") and top_level:
            out.append(Finding("warning", source, here, "Ratings/reviews must be nested in the item they review, and must be real."))

    for key, value in node.items():
        if key in ("@context", "@graph"):
            continue
        child_path = f"{here}.{key}"
        if key.startswith("_"):
            out.append(Finding("warning", source, child_path, "Template comment key left in; delete it"))
            continue
        if key in URL_KEYS:
            for v in value if isinstance(value, list) else [value]:
                if isinstance(v, str) and v and not v.startswith(("http://", "https://", "#", "_:")):
                    sev = "warning" if key == "@id" else "error"
                    out.append(Finding(sev, source, child_path, f"URL should be absolute: {v!r}"))
        if key in DATE_KEYS and isinstance(value, str) and not ISO_DATE.match(value.strip()):
            out.append(Finding("error", source, child_path, f"Date must be ISO 8601 (e.g. 2026-01-31T09:00:00+00:00): {value!r}"))
        if isinstance(value, str) and PLACEHOLDER.search(value):
            out.append(Finding("warning", source, child_path, f"Looks like a placeholder value: {value[:80]!r}"))
        if isinstance(value, (dict, list)):
            validate_node(value, source, child_path, out, primary=(key == "mainEntity" and isinstance(value, dict)))


def validate_text(text: str, source: str) -> Tuple[int, List[Finding]]:
    out: List[Finding] = []
    try:
        data = load_json_lenient(text)
    except ValueError as e:
        return 0, [Finding("error", source, "$", f"Invalid JSON: {e}")]
    validate_node(data, source, "$", out, top_level=True)
    return 1, out


def collect(targets: List[str]) -> List[Tuple[str, str]]:
    """Return (source, jsonld_text) pairs."""
    blocks: List[Tuple[str, str]] = []
    for t in targets:
        if is_url(t):
            res = fetch(t)
            if res.error or res.status >= 400:
                raise SystemExit(f"error: could not fetch {t}: {res.error or res.status}")
            blocks += [(t, b) for b in extract_jsonld_blocks(res.body)]
        elif os.path.isdir(t):
            for path in iter_html_files(t):
                with open(path, encoding="utf-8", errors="replace") as fh:
                    blocks += [(path, b) for b in extract_jsonld_blocks(fh.read())]
        elif os.path.isfile(t):
            with open(t, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            if t.endswith((".json", ".jsonld")):
                blocks.append((t, text))
            else:
                blocks += [(t, b) for b in extract_jsonld_blocks(text)]
        else:
            raise SystemExit(f"error: {t!r} is not a URL, directory or file")
    return blocks


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets", nargs="+", help="URLs, build directories, HTML files or .json files")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--strict", action="store_true", help="exit 1 on warnings too")
    ap.add_argument("--allow-placeholders", action="store_true", help="ignore placeholder warnings (for templates)")
    args = ap.parse_args(argv)

    blocks = collect(args.targets)
    findings: List[Finding] = []
    valid = 0
    for source, text in blocks:
        ok, f = validate_text(text, source)
        valid += ok
        findings += f
    if args.allow_placeholders:
        findings = [f for f in findings if not f.message.startswith("Looks like a placeholder")]

    errors = sum(f.severity == "error" for f in findings)
    warnings = sum(f.severity == "warning" for f in findings)
    if args.json:
        print(json.dumps({"blocks": len(blocks), "parsed": valid, "errors": errors, "warnings": warnings,
                          "findings": [asdict(f) for f in findings]}, indent=2))
    else:
        print(f"JSON-LD: {len(blocks)} block(s), {valid} parsed, {errors} error(s), {warnings} warning(s)")
        if not blocks:
            print("No JSON-LD found. See references/structured-data.md for what each page type should carry.")
        for f in sorted(findings, key=lambda f: ("error", "warning", "info").index(f.severity)):
            print(f"  {f.severity.upper():7} {f.source} {f.path}: {f.message}")
    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
