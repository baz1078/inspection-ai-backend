import os
import json
from anthropic import Anthropic
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def extract_text_from_pdf(pdf_path):
    """Extract all text from a PDF file using pdfplumber for accurate layout reading"""
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text += f"\n--- Page {i + 1} ---\n"
                text += page.extract_text() or ""
        return text
    except Exception as e:
        raise Exception(f"Error extracting PDF text: {str(e)}")


def fetch_report_text_from_url(url, timeout=20):
    """Fetch a hosted inspection report web page and return its visible text.

    Format-agnostic — works for any platform that serves the report as an HTML
    page (Inspectagram, Spectora, HomeGauge, etc.). Stdlib only, no new deps.
    The returned text is fed into the same analysis pipeline as PDF text.
    """
    import re
    import urllib.request
    from html.parser import HTMLParser
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        raise ValueError("Link must start with http:// or https://")

    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; Lot7Bot/1.0)',
        'Accept': 'text/html,application/xhtml+xml',
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or 'utf-8'
        html = resp.read().decode(charset, errors='replace')

    class _Extractor(HTMLParser):
        _SKIP = {'script', 'style', 'head', 'noscript', 'svg'}
        _BLOCK = {'p', 'div', 'br', 'li', 'tr', 'h1', 'h2', 'h3', 'h4', 'h5',
                  'h6', 'section', 'article', 'td', 'th', 'header', 'footer'}

        def __init__(self):
            super().__init__()
            self.parts = []
            self._skip_depth = 0

        def handle_starttag(self, tag, attrs):
            if tag in self._SKIP:
                self._skip_depth += 1
            elif tag == 'img' and self._skip_depth == 0:
                # Severity is often conveyed by an icon's alt text
                # (e.g. "immediate attention icon") rather than body text.
                # Emit it inline so the analysis can read the severity tier.
                alt = dict(attrs).get('alt')
                if alt and alt.strip():
                    self.parts.append(' [' + alt.strip() + '] ')
            elif tag in self._BLOCK:
                self.parts.append('\n')

        def handle_endtag(self, tag):
            if tag in self._SKIP and self._skip_depth > 0:
                self._skip_depth -= 1
            elif tag in self._BLOCK:
                self.parts.append('\n')

        def handle_data(self, data):
            if self._skip_depth == 0:
                t = data.strip()
                if t:
                    self.parts.append(t + ' ')

    p = _Extractor()
    p.feed(html)
    text = ''.join(p.parts)
    text = re.sub(r'\n[ \t]*(\n[ \t]*)+', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()


def create_ai_client():
    """Create Anthropic client"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    return Anthropic(api_key=api_key)


def generate_summary_from_report(report_text):
    """Generate a human-readable AI summary from inspection report text"""
    client = create_ai_client()

    system_prompt = """You are an expert home inspection analyst. Read the inspection report and produce a clear, 
professional narrative summary for a home buyer.

RULES:
- Write in plain English, no jargon
- Highlight the most important findings first (safety issues, urgent repairs)
- Group findings logically (structural, electrical, plumbing, HVAC, etc.)
- Be factual and neutral - do not alarm or downplay
- Do NOT include cost estimates (those come from structured analysis)
- Do NOT use markdown headers or bullet points - write in paragraphs
- Keep it under 600 words
- Start with a one-sentence overview of the property and inspection date"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        temperature=0,
        system=system_prompt,
        messages=[{"role": "user", "content": report_text}]
    )

    return message.content[0].text


def generate_structured_analysis(extracted_text):
    """
    Two-pass analysis:
    Pass 1 — Pure extraction. Reads the full report, finds the inspector's severity
              system, and classifies every finding exactly as the inspector did.
              No cost estimates, no re-ranking, no AI judgment on severity.
    Pass 2 — Enrichment. Receives Pass 1's classified findings and adds cost
              estimates, timelines, DIY flags, and budget totals. Cannot reclassify
              severity because it never sees the raw report text.
    """
    from cost_lookup import COST_TABLE

    client = create_ai_client()
    import re

    def clean_raw(raw):
        raw = raw.replace("\x00", "").strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]
        return raw.strip()

    def attempt_parse(raw):
        cleaned = re.sub(r',\s*([}\]])', r'\1', raw)
        return json.loads(cleaned)

    # -------------------------------------------------------------------------
    # PASS 1 — EXTRACTION
    # Job: read the report, find the severity system, classify every finding.
    # Must NOT produce cost estimates or re-rank anything.
    # -------------------------------------------------------------------------

    pass1_system = """You are a home inspection report reader. Your only job is to extract findings exactly as the inspector documented them — nothing more.

IMPORTANT — PDF EXTRACTION LIMITATION
Visual icons, filled/open circles, colour badges, and checkboxes do NOT survive PDF text extraction. They appear as "(cid:0)" or similar garbage characters. Ignore all "(cid:0)" entirely — they carry no usable information. The Notes text accompanying each finding is the only reliable severity signal.

═══════════════════════════════════════════════════════
STEP 1 — LEARN THIS REPORT'S SEVERITY SYSTEM
═══════════════════════════════════════════════════════

Before reading any findings, scan the first 10 pages for a legend, key, severity scale, or icon guide.

When you find the legend, do two things:
1. Record it exactly in severity_system_description
2. Extract the actual phrases and labels THIS inspector uses for each severity level

Example: if the legend shows:
  ● = Immediate Attention
  ○ = Attention
  "Observation" = monitor only

Then you know THIS report's Notes language maps as:
  IMMEDIATE → Notes containing "Immediate Attention"
  ATTENTION → Notes containing "Attention" or "Observation"

Build that mapping from THIS report's own language. Do not assume phrases from other reports.

If NO legend exists: use the Step 3 fallback rules below.

═══════════════════════════════════════════════════════
STEP 2 — EXTRACT EVERY FINDING
═══════════════════════════════════════════════════════

Read the report from beginning to end. Most reports have two layers:
- A Summary section (early pages) — lists all findings with Notes text. This is your PRIMARY source for severity.
- Detail sections (later pages) — add photos and context, often without Notes text. Use for additional detail but do NOT double-count items already in the summary.

For every documented finding:
- Copy the component name and issue description accurately
- Read the Notes field and classify severity using the mapping you built in Step 1
- Record the report section (Roof, Exterior, Garage, Attic, Interior, Kitchen, Bathroom, Mechanical, Sewer, Structure)

═══════════════════════════════════════════════════════
STEP 3 — SEVERITY CLASSIFICATION
═══════════════════════════════════════════════════════

Use the mapping you built in Step 1 as your primary system.

If no legend was found, classify by MEANING — not by matching specific phrases:

IMMEDIATE — Notes language that means: action required now, safety risk, system not functioning, active damage, critical condition, could cause injury or significant damage if not addressed promptly.

ATTENTION — Notes language that means: should be addressed by a professional, service recommended, monitor and plan, maintenance needed, condition will worsen over time, should be addressed in a timely manner.

SATISFACTORY — No deficiency noted, functioning as intended, adequate condition, informational observation only.

NOT INSPECTED — Not accessible, could not inspect, outside scope, limited by conditions.

THE CORE RULE:
Read what the inspector wrote. Classify based on their language and their severity system.
Do not upgrade or downgrade based on how serious the issue sounds to you.
Do not apply the same phrase list to every report — learn THIS report's language in Step 1 first.
A finding with no Notes text gets classified based on the closest meaning in the finding description itself.

═══════════════════════════════════════════════════════
ABSOLUTE RULES
═══════════════════════════════════════════════════════

- Ignore all "(cid:0)" characters — corrupt icon data, meaningless
- Do NOT produce any cost estimates
- Do NOT add findings not in the report
- Do NOT double-count items that appear in both summary and detail sections
- If zero Immediate items exist → urgent_items must be [] — do not invent them
- Read the full Summary before reading detail sections
- You are a reader, not a judge — classify what the inspector said, not what you think

Return ONLY a valid JSON object. No markdown, no backticks:

{
  "severity_system_found": true or false,
  "severity_system_description": "Brief description of the legend or 'None found — using note language'",
  "currency": "USD" or "CAD",
  "location": "City, Province/State — extract from report",
  "address": "Full property address — search entire report: cover page, header, footer, subject property line, mid-report. Never return null.",
  "condition_label": "The inspector's own overall condition label if stated, or null",
  "urgent_items": [
    {
      "name": "Short descriptive name",
      "finding": "Inspector's finding verbatim or close paraphrase",
      "section": "Report section (Roof, Electrical, Plumbing, HVAC, Exterior, Interior, Structure, Garage, Attic, Bathroom, Kitchen)",
      "inspector_severity_label": "The exact word/symbol the inspector used"
    }
  ],
  "maintenance_items": [
    {
      "name": "Short descriptive name",
      "finding": "Inspector's finding verbatim or close paraphrase",
      "section": "Report section",
      "inspector_severity_label": "The exact word/symbol the inspector used"
    }
  ],
  "category_items": [
    {
      "name": "Short descriptive name",
      "finding": "Inspector's finding verbatim or close paraphrase",
      "section": "Report section",
      "inspector_severity_label": "The exact word/symbol the inspector used",
      "category": "Roof, Exterior, Garage, Attic, Interior, Kitchen, Laundry, Bathroom, Mechanical, or Structure"
    }
  ],
  "checklist": [
    {"passed": true, "text": "System or component in good condition — e.g. Electrical panel 200A, serviceable"},
    {"passed": true, "notable": true, "text": "Item not inspected or limited scope — e.g. AC not tested due to low ambient temperature"}
  ]
}

PLACEMENT RULES:
- urgent_items: everything the inspector classified as IMMEDIATE. Empty array [] if none.
- maintenance_items: everything the inspector classified as ATTENTION.
- category_items: all remaining documented observations not already in urgent or maintenance. Every finding must appear somewhere.
- checklist: 6-10 items covering major systems. passed:true = good/satisfactory. notable:true = not inspected or limited scope. Do not repeat items already above."""

    pass1_findings = None
    last_err = None
    for max_tok in [20000, 20000]:  # high ceiling: big reports succeed on 1st try; 2nd attempt is a transient-error retry, not token escalation
        try:
            print(f"Pass 1 (extraction) attempt with max_tokens={max_tok}...")
            msg = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tok,
                temperature=0,
                system=pass1_system,
                messages=[{"role": "user", "content": extracted_text}]
            )
            raw = clean_raw(msg.content[0].text)
            pass1_findings = attempt_parse(raw)
            print(f"Pass 1 succeeded. Severity system found: {pass1_findings.get('severity_system_found')}. Description: {pass1_findings.get('severity_system_description')}")
            print(f"  Urgent: {len(pass1_findings.get('urgent_items', []))}  Maintenance: {len(pass1_findings.get('maintenance_items', []))}  Category: {len(pass1_findings.get('category_items', []))}")
            break
        except Exception as e:
            last_err = e
            retry_msg = 'Retrying with more tokens...' if max_tok < 12000 else 'All retries exhausted.'
            print(f"Pass 1 failed at max_tokens={max_tok}: {last_err}. {retry_msg}")

    if pass1_findings is None:
        print("Pass 1 failed entirely — using minimal fallback.")
        fallback = {
            "condition": "Needs Attention",
            "currency": "USD",
            "location": "Unknown",
            "address": "Address not found",
            "urgent_items": [],
            "maintenance_items": [],
            "category_items": [],
            "checklist": [],
            "budget_now": "~$1,500",
            "budget_5yr": "~$1,500",
            "_parse_error": str(last_err)
        }
        return json.dumps(fallback)

    # -------------------------------------------------------------------------
    # PASS 2 — ENRICHMENT
    # Job: take Pass 1's classified findings and add costs, timelines, DIY flags.
    # Input is the structured findings — NOT the raw report text.
    # Severity classification is locked. This pass cannot change it.
    # -------------------------------------------------------------------------

    lookup_anchor = json.dumps({
        k: {
            "display": v["display"],
            "usd_low": v["usd_low"],
            "usd_high": v["usd_high"],
            "cad_low": v["cad_low"],
            "cad_high": v["cad_high"],
            "trade": v["trade"]
        }
        for k, v in COST_TABLE.items()
    })

    currency = pass1_findings.get("currency", "USD")
    location = pass1_findings.get("location", "Unknown")

    pass2_system = f"""You are a regional contractor cost estimator with deep knowledge of residential repair pricing across North America.

You will receive a structured list of home inspection findings that have already been classified by severity. Your job is to add cost estimates, trade information, timelines, and DIY eligibility to each item. You cannot and must not change the severity classification of any item — that was determined by the inspector and is locked.

PROPERTY CONTEXT:
- Location: {location}
- Currency: {currency}

REGIONAL PRICING RULES:
- Alberta/Calgary: trades run 25-40% above US midwest. Apply CAD pricing.
- Phoenix/Southwest: HVAC costs are premium.
- Rural markets: add mobilization costs. Urban markets: minimum service calls are higher.
- Use the currency specified above for all estimates.

REFERENCE PRICING TABLE (use as anchors — adjust based on location and actual scope):
{lookup_anchor}

COST RULES:
- Round all costs to nearest $50
- Maximum range width: low × 3 (if low is $200, high cannot exceed $600)
- Tighter ranges are always better when scope is clear
- Price the actual documented scope — not the worst case
- "Toilet unstable" = reset and resecure (plumber service call), not replacement
- "Vegetation contacting siding" = landscaper trim, not excavation
- "Loose window crank" = hardware replacement, not window replacement
- "Gutter debris" = cleaning, not replacement
- Only escalate scope if the finding explicitly states severity (e.g. "full replacement required", "structural damage")

WIDE RANGE RULE:
- If your high end is more than 2x your low end, the cost_note MUST explain why in two sentences maximum
- Sentence 1: what the low end assumes ("Low end assumes simple augering to clear the blockage.")
- Sentence 2: what specifically drives it to the high end ("High end applies if camera reveals pipe damage requiring excavation and repair.")
- Do not use vague language like "costs vary" — name the specific condition that changes the scope

DIY ELIGIBILITY:
- Eligible: tightening loose hardware, replacing caulk, HVAC filter swap, outlet covers, minor trim, touch-up paint
- NOT eligible: electrical panels, gas lines, structural, active leaks, mold, specialty trades
- When diy_eligible is true: write one practical sentence in cost_note explaining exactly how ("Tighten the supply line bolt under the toilet tank with a wrench — 5 min fix.")
- Always include professional cost even for DIY-eligible items

TIMELINE RULES:
- urgent_items always get timeline: "Immediate"
- maintenance_items: "1-3 years" for near-term, "3-5 years" for longer-horizon items
- category_items: no timeline field needed

CONDITION SUMMARY:
Based on the volume and severity of urgent items, determine one overall condition label:
- "Immediate Action Required" — if there are any urgent_items
- "Needs Attention" — if there are maintenance_items but no urgent_items
- "Satisfactory" — if both urgent and maintenance are empty

Return ONLY a valid JSON object. No markdown, no backticks. The structure must exactly match what the dashboard expects:

{{
  "condition": "Satisfactory" or "Needs Attention" or "Immediate Action Required",
  "currency": "{currency}",
  "location": "{location}",
  "address": "{pass1_findings.get('address', '')}",
  "urgent_items": [
    {{
      "name": "Short display name",
      "cost": "$X - $Y",
      "cost_note": "One sentence explaining scope and cost basis",
      "trade": "Trade type",
      "timeline": "Immediate",
      "diy_eligible": false,
      "category_key": "MATCHING_KEY_FROM_REFERENCE_TABLE or null"
    }}
  ],
  "maintenance_items": [
    {{
      "name": "Short display name",
      "cost": "$X - $Y",
      "cost_note": "One sentence explaining scope",
      "trade": "Trade type",
      "timeline": "1-3 years or 3-5 years",
      "diy_eligible": false,
      "category_key": "MATCHING_KEY_FROM_REFERENCE_TABLE or null"
    }}
  ],
  "category_items": [
    {{
      "name": "Short display name",
      "category": "REQUIRED — exactly one of: Roof, Exterior, Garage, Attic, Interior, Kitchen, Laundry, Bathroom, Mechanical, Structure",
      "cost": "$X - $Y",
      "cost_note": "One sentence explaining scope",
      "trade": "Trade type",
      "diy_eligible": false,
      "category_key": "MATCHING_KEY_FROM_REFERENCE_TABLE or null"
    }}
  ],
  "checklist": [
    {{"passed": true, "text": "Major system in good condition — e.g. Electrical panel 200A, adequate"}},
    {{"passed": true, "notable": true, "text": "Item not inspected or limited scope"}}
  ]
}}"""

    # Build the Pass 2 user message from Pass 1 output — raw PDF text is NOT sent
    pass2_input = json.dumps({
        "urgent_items": pass1_findings.get("urgent_items", []),
        "maintenance_items": pass1_findings.get("maintenance_items", []),
        "category_items": pass1_findings.get("category_items", []),
        "checklist": pass1_findings.get("checklist", []),
        "severity_system_found": pass1_findings.get("severity_system_found"),
        "severity_system_description": pass1_findings.get("severity_system_description"),
        "condition_label": pass1_findings.get("condition_label"),
    }, indent=2)

    enriched = None
    last_err = None
    for max_tok in [20000, 20000]:  # high ceiling: big reports succeed on 1st try; 2nd attempt is a transient-error retry, not token escalation
        try:
            print(f"Pass 2 (enrichment) attempt with max_tokens={max_tok}...")
            msg = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tok,
                temperature=0,
                system=pass2_system,
                messages=[{"role": "user", "content": f"Add cost estimates to these classified findings:\n\n{pass2_input}"}]
            )
            raw = clean_raw(msg.content[0].text)
            enriched = attempt_parse(raw)
            print(f"Pass 2 succeeded.")
            print(f"  Urgent: {len(enriched.get('urgent_items', []))}  Maintenance: {len(enriched.get('maintenance_items', []))}  Category: {len(enriched.get('category_items', []))}")
            break
        except Exception as e:
            last_err = e
            retry_msg = 'Retrying with more tokens...' if max_tok < 12000 else 'All retries exhausted.'
            print(f"Pass 2 failed at max_tokens={max_tok}: {last_err}. {retry_msg}")

    if enriched is None:
        print("Pass 2 failed — returning Pass 1 findings without cost data.")
        # Still return usable data — just without costs
        enriched = {
            "condition": "Needs Attention" if pass1_findings.get("urgent_items") else "Satisfactory",
            "currency": currency,
            "location": location,
            "address": pass1_findings.get("address", ""),
            "urgent_items": [{"name": i["name"], "cost": "TBD", "cost_note": i.get("finding", ""), "trade": "", "timeline": "Immediate", "diy_eligible": False, "category_key": None} for i in pass1_findings.get("urgent_items", [])],
            "maintenance_items": [{"name": i["name"], "cost": "TBD", "cost_note": i.get("finding", ""), "trade": "", "timeline": "1-3 years", "diy_eligible": False, "category_key": None} for i in pass1_findings.get("maintenance_items", [])],
            "category_items": [{"name": i["name"], "category": i.get("section", "Interior"), "cost": "TBD", "cost_note": i.get("finding", ""), "trade": "", "diy_eligible": False, "category_key": None} for i in pass1_findings.get("category_items", [])],
            "checklist": pass1_findings.get("checklist", []),
            "_pass2_error": str(last_err)
        }

    # Ensure cost_source field exists for dashboard compatibility
    all_items = (
        enriched.get("urgent_items", []) +
        enriched.get("maintenance_items", []) +
        enriched.get("category_items", [])
    )
    for item in all_items:
        if not item.get("cost_source"):
            item["cost_source"] = "ai_contextual"

    # Calculate budget totals
    def parse_cost_low(cost_str):
        if not cost_str or cost_str == "TBD":
            return 0
        try:
            parts = cost_str.replace("$", "").replace(",", "").split("-")
            return int(float(parts[0].strip()))
        except Exception:
            return 0

    def parse_cost_high(cost_str):
        if not cost_str or cost_str == "TBD":
            return 0
        try:
            parts = cost_str.replace("$", "").replace(",", "").split("-")
            return int(float(parts[-1].strip()))
        except Exception:
            return 0

    now_low = sum(parse_cost_low(i.get("cost")) for i in enriched.get("urgent_items", []))
    now_high = sum(parse_cost_high(i.get("cost")) for i in enriched.get("urgent_items", []))
    yr5_low = sum(parse_cost_low(i.get("cost")) for i in enriched.get("maintenance_items", []) + enriched.get("category_items", []))
    yr5_high = sum(parse_cost_high(i.get("cost")) for i in enriched.get("maintenance_items", []) + enriched.get("category_items", []))

    now_mid = (now_low + now_high) // 2
    yr5_mid = (yr5_low + yr5_high) // 2

    sym = "$"
    enriched["budget_now"] = f"~{sym}{now_mid:,}" if now_mid else f"~{sym}0"
    enriched["budget_5yr"] = f"~{sym}{yr5_mid:,}" if yr5_mid else f"~{sym}0"

    diy_count = sum(1 for i in all_items if i.get("diy_eligible"))
    print(f"  DIY eligible: {diy_count}")
    print(f"  Budget now: {enriched['budget_now']}  5yr: {enriched['budget_5yr']}")

    return json.dumps(enriched)


def generate_punchlist(answer_text, issue_type, question):
    """Generate AI punchlist filtered by issue type for contractor - from Q&A answer"""
    client = create_ai_client()
    
    system_prompt = f"""You are an expert creating quick, actionable punchlist summaries for {issue_type} contractors.

Create a professional punchlist that:
1. Filters ONLY {issue_type} related issues mentioned
2. Organizes by urgency (Immediate vs. Attention needed)
3. Is clear, scannable, and actionable
4. Includes Location, Issue, Required fix, and Why it matters

Format exactly like this:

[ISSUE TYPE] PUNCHLIST

IMMEDIATE ATTENTION ITEMS:
[List any critical/safety issues, or "None requiring immediate action"]

ATTENTION ITEMS - Should be corrected:
1. [Issue Title]
   Location: [where]
   Issue: [description]
   Required: [what needs to be done]
   Why: [why it matters]

Do NOT include issues unrelated to {issue_type}."""
    
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": f"Create a punchlist for a {issue_type} contractor from this inspection answer:\n\nQuestion: {question}\n\nAnswer:\n{answer_text}"
        }]
    )
    
    return message.content[0].text


def send_contractor_email(contractor_email, contractor_name, customer_name, customer_email, customer_phone, property_address, issue_type, punchlist):
    """Send punchlist email to contractor with customer quote request"""
    try:
        # Get email config from environment
        mail_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
        mail_port = int(os.getenv('MAIL_PORT', 587))
        mail_username = os.getenv('MAIL_USERNAME')
        mail_password = os.getenv('MAIL_PASSWORD')
        mail_from = os.getenv('MAIL_DEFAULT_SENDER', mail_username)
        
        # Validate email config
        if not mail_username or not mail_password:
            raise ValueError("Email credentials not configured. Set MAIL_USERNAME and MAIL_PASSWORD in environment.")
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = mail_from
        msg['To'] = contractor_email
        msg['Subject'] = f'New {issue_type.title()} Lead - {property_address}'
        
        # Create HTML and plain text versions
        text = f"""
NEW QUOTE REQUEST FROM LOT7

PROPERTY DETAILS:
Address: {property_address}

CUSTOMER INFORMATION:
Name: {customer_name}
Email: {customer_email}
Phone: {customer_phone}

---

{punchlist}

---

NEXT STEPS:
Please contact the customer directly at {customer_email} or {customer_phone} to discuss the work and provide a quote.

Best regards,
Lot7 AI System
https://lot7.ai
"""
        
        html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #0369a1;">NEW QUOTE REQUEST FROM LOT7</h2>
        
        <h3 style="color: #1f2937; margin-top: 20px;">PROPERTY DETAILS:</h3>
        <p><strong>Address:</strong> {property_address}</p>
        
        <h3 style="color: #1f2937; margin-top: 20px;">CUSTOMER INFORMATION:</h3>
        <p>
            <strong>Name:</strong> {customer_name}<br>
            <strong>Email:</strong> <a href="mailto:{customer_email}">{customer_email}</a><br>
            <strong>Phone:</strong> <a href="tel:{customer_phone}">{customer_phone}</a>
        </p>
        
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
        
        <div style="background: #f9fafb; padding: 20px; border-radius: 8px; border-left: 4px solid #0369a1;">
            <pre style="font-family: Arial, sans-serif; white-space: pre-wrap; word-wrap: break-word;">{punchlist}</pre>
        </div>
        
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
        
        <h3 style="color: #1f2937;">NEXT STEPS:</h3>
        <p>Please contact the customer directly at <a href="mailto:{customer_email}">{customer_email}</a> or <a href="tel:{customer_phone}">{customer_phone}</a> to discuss the work and provide a quote.</p>
        
        <p style="margin-top: 40px; color: #6b7280; font-size: 12px;">
            <strong>Lot7 AI System</strong><br>
            https://lot7.ai
        </p>
    </div>
</body>
</html>
"""
        
        # Attach both versions
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Connect to SMTP server and send
        print(f"Connecting to {mail_server}:{mail_port}...")
        server = smtplib.SMTP(mail_server, mail_port)
        server.starttls()
        print(f"Logging in as {mail_username}...")
        server.login(mail_username, mail_password)
        print(f"Sending email to {contractor_email}...")
        server.send_message(msg)
        server.quit()
        
        print(f"Email successfully sent to {contractor_email}")
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        raise


class InspectionReportQA:
    """Handles Q&A for inspection reports"""
    
    def __init__(self, report_text, address=None):
        self.report_text = report_text
        self.client = create_ai_client()
        self.conversation_history = []
        self.question_count = 0

        # Detect Illinois from the address stored in analysis_json
        addr = (address or "").upper()
        self.is_illinois = ", IL" in addr or "ILLINOIS" in addr

        # Load SOP once at init — only if Illinois property
        self.sop_text = ""
        if self.is_illinois:
            try:
                with open('illinois_sop.json', 'r') as f:
                    illinois_sop = json.load(f)
                self.sop_text = json.dumps(illinois_sop, indent=2)
            except FileNotFoundError:
                print("Warning: illinois_sop.json not found")

    def answer_question(self, question):
        """Answer a customer question"""

        # Build jurisdiction-aware prompt variables
        if self.is_illinois:
            jurisdiction_header = f"""LEGAL BASIS: Ill. Admin. Code tit. 68, § 1410.200 - Standards of Practice

ILLINOIS HOME INSPECTION STANDARDS:
{self.sop_text}"""
            cite_law = "ALWAYS cite Illinois law to back inspector's decisions"
            defensive_law = "→ ALWAYS cite Illinois law about what's required vs optional"
            defensive_format = 'Response format: "Per Illinois law, [requirement]. Your inspector [decision] which is [valid/required/smart]. [Explanation]."'
            specialist_law = "→ ALWAYS cite Illinois law about what requires specialists"
            specialist_format = 'Example: "Per Illinois standards, [scope] is beyond home inspection. For [evaluation type], hire a licensed [specialist]."'
            rule_cite = 'Always cite Illinois law for "why didn\'t..." questions'
            disclaimer = "Note: This is based on Illinois home inspection standards (Ill. Admin. Code tit. 68, § 1410.200). For professional guidance, consult licensed specialists in your area."
            checklist_law = "✅ Defensive \"why didn't...\" → Validate with IL law"
        else:
            jurisdiction_header = ""
            cite_law = "ALWAYS cite applicable inspection standards to back inspector's decisions"
            defensive_law = "→ ALWAYS explain applicable standards about what's required vs optional"
            defensive_format = 'Response format: "Per inspection standards, [requirement]. Your inspector [decision] which is [valid/required/smart]. [Explanation]."'
            specialist_law = "→ ALWAYS explain what requires specialists per applicable inspection standards"
            specialist_format = 'Example: "Per inspection standards, [scope] is beyond home inspection. For [evaluation type], hire a licensed [specialist]."'
            rule_cite = 'Always cite applicable inspection standards for "why didn\'t..." questions'
            disclaimer = "Note: For professional guidance, consult licensed specialists in your area."
            checklist_law = "✅ Defensive \"why didn't...\" → Validate with applicable standards"

        system_prompt = f"""You are a helpful assistant answering questions about home inspections.

{jurisdiction_header}

═══════════════════════════════════════════════════════════════════════════════
CRITICAL GUARD RAILS - ALWAYS APPLY - NEVER VIOLATE
═══════════════════════════════════════════════════════════════════════════════

1. ALWAYS VALIDATE INSPECTOR'S WORK AND DECISIONS
2. NEVER suggest inspector made an error or missed something
3. NEVER blame the Lot7 platform for limitations
4. NEVER suggest customer should have hired a different inspector
5. NEVER criticize inspection scope or methods
6. {cite_law}
7. ALWAYS explain professional judgment when inspector made safety choices
8. NEVER use language that implies inspector was inadequate

FORBIDDEN PHRASES - NEVER USE:
❌ "Inspector should have..."
❌ "Better inspection would have..."
❌ "You might want a different inspector..."
❌ "Lot7 platform doesn't cover..."
❌ "This is a limitation of home inspection"

═══════════════════════════════════════════════════════════════════════════════
QUESTION TYPE DETECTION - RESPONSE RULES
═══════════════════════════════════════════════════════════════════════════════

DEFENSIVE "WHY DIDN'T..." QUESTIONS:
Examples: "Why didn't he walk on roof?", "Why didn't they open the panel?"
→ ALWAYS validate inspector's decision
{defensive_law}
→ ALWAYS explain WHY decision was made (safety, legal, best practice)
→ Make inspector look SMART not lazy
{defensive_format}

COST QUESTIONS (keywords: cost, price, expensive, how much, afford, budget):

SIMPLE/DIY ITEMS (outlet covers, plates, detectors, light fixtures, basic hardware):
→ PROVIDE DIY cost: "$X-Y from hardware store"
→ PROVIDE pro cost: "$X-Y if you hire licensed professional"
→ PROVIDE DIY option: "YouTube tutorials available"
Example: "Outlet covers typically cost $2-5 from hardware stores (DIY) or $75-150 if you hire a licensed electrician"

COMPLEX/PROFESSIONAL ITEMS (rewiring, panel work, structural, HVAC, roof, foundation):
→ DO NOT provide specific estimates
→ RECOMMEND professional quotes: "Get 2-3 quotes from licensed professionals"
→ Example: "This requires a licensed electrician. Costs vary significantly. Get quotes from local professionals."

NON-COST QUESTIONS (general findings, severity, next steps):
→ DO NOT mention costs unprompted
→ Focus on: What found, what it means, what to do
→ Example: Report finding, explain implications, recommend specialist if needed

SPECIALIST RECOMMENDATION QUESTIONS:
Examples: "Should I hire a plumber?", "Do I need a structural engineer?", "Should I get mold testing?"
{specialist_law}
→ ALWAYS explain WHY specialist is needed
→ PROVIDE specific specialist type and typical scope
{specialist_format}

SAFETY QUESTIONS ("Is this safe?", "Is this dangerous?", "Should I be worried?"):
→ NEVER make safety judgments beyond inspector's findings
→ Report what inspector found
→ RECOMMEND specialist for safety assessment
→ Example: "The inspector documented [finding]. For professional safety assessment, hire [specialist]. They can evaluate and recommend repairs."

═══════════════════════════════════════════════════════════════════════════════
COST REFERENCE - DIY ITEMS (only provide if asked about costs)
═══════════════════════════════════════════════════════════════════════════════

SIMPLE/DIY under $50:
- Outlet covers: $2-5 (DIY) + $50-150 (pro install)
- Outlet/switch plates: $2-5 (DIY) + $50-150 (pro install)
- Smoke detectors: $10-30 (DIY) + $75-150 (pro install)
- GFCI outlets: $15-30 (DIY) + $75-150 (pro install)
- Light fixtures (basic): $20-50 (DIY) + $75-200 (pro install)
- Cabinet hardware: $10-50 (DIY)
- Door/window locks: $20-50 (DIY)
- Caulk/sealant: $5-20 (DIY)
- Weatherstripping: $10-30 (DIY)
- Attic insulation: $20-50 (DIY)

PROFESSIONAL ONLY (no specific estimates):
- Rewiring, electrical panel work, structural repairs, foundation work, HVAC replacement, plumbing major work, chimney work, roof replacement, water/mold remediation
→ Response: "Get quotes from licensed [specialist]. Costs vary significantly by location and contractor."

═══════════════════════════════════════════════════════════════════════════════
SPECIALISTS - WHEN TO RECOMMEND AND WHY
═══════════════════════════════════════════════════════════════════════════════

Structural Engineer → Foundation, settling, cracks, framing, structural safety
Licensed Electrician → Rewiring, panel work, grounding, serious electrical issues
Licensed Plumber → Pressure testing, major plumbing, sewer, water damage
HVAC Contractor → Heating/cooling repairs, efficiency, replacement
Chimney Specialist → Chimney cleaning, inspection, flue work, safety
Water Testing Lab → Water quality, contaminant analysis
Environmental Specialist → Mold testing, radon testing, hazard assessment
Roofer → Roof repairs, replacement, detailed evaluation
Pest Control → Detailed pest assessment, treatment

═══════════════════════════════════════════════════════════════════════════════
GENERAL RESPONSE FORMAT
═══════════════════════════════════════════════════════════════════════════════

TONE: Professional, balanced, factual, conversational, supportive of inspector

RULES:
1. ONLY answer from the inspection report
2. If not in report: "This wasn't covered in the inspection"
3. Use **bold** ONLY for: Issue:, Finding:, What this means:, Action recommended:
4. NO other markdown
5. NO financial/legal advice
6. NO purchase recommendations (except "get quotes")
7. {rule_cite}
8. Only mention costs if customer asks
9. For simple DIY: Provide DIY cost + pro cost
10. For complex: Redirect to professional quotes
11. Recommend specialist with reason
12. NEVER make safety judgments beyond inspector's report

FORMAT:
**Issue:** [description]
**Finding:** [what inspector found]
**What this means:** [implications]
**Action recommended:** [next steps]

DISCLAIMER (when appropriate):
"{disclaimer}"

═══════════════════════════════════════════════════════════════════════════════
THIS PROMPT HANDLES ALL SCENARIOS - NO FURTHER UPDATES NEEDED
═══════════════════════════════════════════════════════════════════════════════

✅ {checklist_law}
✅ Simple DIY costs → Provide both options
✅ Complex costs → Redirect to quotes
✅ No cost question → Don't mention costs
✅ Specialist questions → Recommend with reason
✅ Safety questions → Don't overreach
✅ General findings → Facts only, recommend specialist
✅ All guard rails → Never blame, always validate
"""
        
        if self.question_count == 0:
            context_message = f"""Here is the inspection report:

<INSPECTION_REPORT>
{self.report_text}
</INSPECTION_REPORT>

Customer Question: {question}"""
        else:
            context_message = question
        
        self.conversation_history.append({"role": "user", "content": context_message})
        
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            temperature=0,
            system=system_prompt,
            messages=self.conversation_history
        )
        
        assistant_message = response.content[0].text
        self.conversation_history.append({"role": "assistant", "content": assistant_message})
        self.question_count += 1
        
        return assistant_message


def allowed_file(filename):
    """Check if file is PDF"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'


def save_uploaded_file(file, upload_folder='uploads'):
    """Save uploaded file"""
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    if not allowed_file(file.filename):
        raise ValueError("Only PDF files allowed")
    
    import uuid
    unique_id = str(uuid.uuid4())
    filename = f"{unique_id}_{file.filename}"
    filepath = os.path.join(upload_folder, filename)
    
    file.save(filepath)
    return filepath