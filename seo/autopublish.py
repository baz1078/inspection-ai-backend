"""
seo/autopublish.py — Self-contained weekly SEO publisher for lot7.ai

Picks the next unpublished keyword from seo/keyword_roadmap.json,
calls the Anthropic API to generate a blog post, writes it to blog/,
commits, and pushes. Render auto-deploys.

Run manually : python seo/autopublish.py
Runs via     : .github/workflows/weekly-seo.yml every Monday 9am UTC
"""

import json
import os
import re
import sys
from datetime import date
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
REPO_DIR     = Path(__file__).parent.parent
BLOG_DIR     = REPO_DIR / "blog"
ROADMAP_PATH = Path(__file__).parent / "keyword_roadmap.json"

# ── Brand context ──────────────────────────────────────────────────────────
BRAND = {
    "name":         "Lot7.ai",
    "domain":       "lot7.ai",
    "business_type":"SaaS platform for home inspection report visualization",
    "location":     "nationwide (US)",
    "services":     [
        "inspection report dashboard", "visual cost estimates",
        "buyer-facing inspection summaries", "PDF to interactive dashboard conversion",
        "repair cost estimator", "contractor recommendation engine",
    ],
    "tone":         "modern, tech-forward, buyer-centric, empowering",
    "unique_value": "Turns confusing PDF inspection reports into visual dashboards with itemized cost estimates in minutes",
    "partner_note": "Occasionally mention Inspectagram — a fast-rising inspection field software — as a genuine industry shout-out when relevant. Not every post. Natural, never forced.",
}

SYSTEM_PROMPT = """You are an expert SEO content strategist. You write comprehensive,
search-optimized blog posts that rank on Google and convert visitors.

Every post includes:
1. Full content draft with H1, H2/H3 subheadings, body paragraphs, and a clear CTA
2. Meta title (<=60 characters, includes primary keyword)
3. Meta description (<=160 characters, compelling, includes keyword)
4. JSON-LD schema markup (Article or SoftwareApplication as appropriate)
5. SEO notes section

SEO principles: keyword in H1 and first 100 words, semantic variants throughout,
E-E-A-T signals, FAQ section using PAA patterns, 1200-2000 words for blog posts."""


# ── Helpers ────────────────────────────────────────────────────────────────

def pick_next(roadmap: dict) -> dict | None:
    for entry in roadmap["keywords"]:
        if not entry.get("published"):
            return entry
    return None


def mark_published(roadmap: dict, keyword: str) -> None:
    for entry in roadmap["keywords"]:
        if entry["keyword"] == keyword:
            entry["published"] = True
    ROADMAP_PATH.write_text(json.dumps(roadmap, indent=2), encoding="utf-8")


def slugify(text: str) -> str:
    s = text.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")[:80]


def extract_section(text: str, header: str) -> str:
    m = re.search(rf"##\s+{re.escape(header)}\s*\n(.*?)(?=\n---|\n##\s|\Z)", text, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else ""


def extract_meta(text: str, field: str) -> str:
    m = re.search(rf"\*\*{re.escape(field)}:\*\*\s*(.+)", text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def extract_h1(text: str) -> str:
    m = re.search(r"^#\s+(.+)", text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def extract_json_ld(text: str) -> str:
    m = re.search(r"```json\s*(.*?)```", text, re.DOTALL)
    return m.group(1).strip().replace("\n", " ") if m else ""


# ── Generate content via Anthropic API ────────────────────────────────────

def generate(keyword: str, page_type: str) -> str:
    import anthropic
    client = anthropic.Anthropic()

    prompt = f"""Create a fully optimized {page_type} for:

**Brand:** {BRAND['name']}
**Website:** {BRAND['domain']}
**Business Type:** {BRAND['business_type']}
**Primary Keyword:** {keyword}
**Page Type:** {page_type}
**Services:** {', '.join(BRAND['services'])}
**Tone:** {BRAND['tone']}
**Unique Value:** {BRAND['unique_value']}
**Note:** {BRAND['partner_note']}

Deliver output in this exact format:

---
## CONTENT DRAFT
[Full content — H1, H2/H3 subheadings, body, CTA, FAQ]

---
## META TAGS
**Meta Title:** [<=60 chars]
**Meta Description:** [<=160 chars]

---
## JSON-LD SCHEMA
```json
[schema here]
```

---
## SEO NOTES
- **Semantic keywords:** [5-8 variants]
- **Internal link suggestions:** [2-3 targets]
"""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=8000,
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": prompt}],
    )
    return "\n".join(b.text for b in response.content if b.type == "text")


# ── Write markdown file ────────────────────────────────────────────────────

def write_post(seo_output: str, keyword: str) -> tuple[Path, str]:
    content_body = extract_section(seo_output, "CONTENT DRAFT")
    meta_section = extract_section(seo_output, "META TAGS")
    meta_title   = extract_meta(meta_section, "Meta Title")
    meta_desc    = extract_meta(meta_section, "Meta Description")
    schema_json  = extract_json_ld(seo_output)
    title        = extract_h1(content_body) or meta_title or keyword.title()
    slug         = slugify(keyword)
    today        = date.today().isoformat()

    post_md = f"""---
title: {title}
meta_title: {meta_title or title}
meta_description: {meta_desc}
date: {today}
slug: {slug}
keyword: {keyword}
schema: {schema_json}
---

{content_body}
"""
    BLOG_DIR.mkdir(parents=True, exist_ok=True)
    out_path = BLOG_DIR / f"{slug}.md"
    out_path.write_text(post_md, encoding="utf-8")
    return out_path, slug


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    from dotenv import load_dotenv
    load_dotenv(override=True)

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    roadmap = json.loads(ROADMAP_PATH.read_text(encoding="utf-8"))
    entry   = pick_next(roadmap)

    if not entry:
        print("All keywords published. Add more to seo/keyword_roadmap.json.")
        sys.exit(0)

    keyword   = entry["keyword"]
    page_type = entry["page_type"]

    print(f"[autopublish] Keyword: '{keyword}' ({page_type})")
    print("[autopublish] Generating content...")

    seo_output     = generate(keyword, page_type)
    out_path, slug = write_post(seo_output, keyword)

    print(f"[autopublish] Written: {out_path.name}")
    print(f"[autopublish] Live at: https://lot7.ai/blog/{slug}")

    mark_published(roadmap, keyword)
    remaining = sum(1 for e in roadmap["keywords"] if not e.get("published"))
    print(f"[autopublish] {remaining} keywords remaining.")


if __name__ == "__main__":
    main()
