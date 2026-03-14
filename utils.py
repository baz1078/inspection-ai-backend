import PyPDF2
import os
import json
from anthropic import Anthropic
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def extract_text_from_pdf(pdf_path):
    """Extract all text from a PDF file"""
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text += f"\n--- Page {page_num + 1} ---\n"
                text += page.extract_text()
        
        return text
    except Exception as e:
        raise Exception(f"Error extracting PDF text: {str(e)}")


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
        model="claude-sonnet-4-5-20250929",
        max_tokens=1000,
        system=system_prompt,
        messages=[{"role": "user", "content": report_text}]
    )

    return message.content[0].text


def generate_structured_analysis(extracted_text):
    """
    Two-step analysis:
    Step 1 - AI identifies findings and maps them to category keys.
    Step 2 - Python prices known categories from lookup table.
             AI prices only unmatched items, with tighter, buyer-friendly ballpark ranges.
    """
    from cost_lookup import COST_TABLE, get_cost, format_cost_range, get_all_categories
    import re

    client = create_ai_client()
    categories_list = get_all_categories()
    categories_json = json.dumps(categories_list)

    step1_prompt = f"""You are a home inspection analyst. Read this inspection report and return ONLY a valid JSON object.
Do NOT include dollar amounts -- only identify and categorise findings.

CATEGORY KEYS (use exact key strings from this list):
{categories_json}

Return this exact structure:
{{
  "condition": "Satisfactory" or "Maintenance" or "Immediate",
  "currency": "USD" or "CAD",
  "location": "City, Province/State detected from report",
  "address": "Full street address detected from report, e.g. 687 Cranston Avenue SE, Calgary, Alberta or null if not found",
  "urgent_items": [
    {{
      "name": "Short display name",
      "category_key": "EXACT_KEY_FROM_LIST or null if not in list",
      "custom_description": "Full description only if category_key is null",
      "timeline": "Immediate",
      "trade": "Trade type"
    }}
  ],
  "maintenance_items": [
    {{
      "name": "Short display name",
      "category_key": "EXACT_KEY_FROM_LIST or null if not in list",
      "custom_description": "Full description only if category_key is null",
      "timeline": "1-3 years or 3-5 years",
      "trade": "Trade type"
    }}
  ],
  "category_items": [
    {{
      "name": "Short display name",
      "category": "Roof or Exterior or Garage or Attic or Interior or Kitchen or Laundry or Bathroom or Mechanical or Structure",
      "category_key": "EXACT_KEY_FROM_LIST or null if not in list",
      "custom_description": "Full description only if category_key is null",
      "trade": "Trade type"
    }}
  ],
  "checklist": [
    {{"passed": true, "text": "Major system in good condition — e.g. Electrical panel 200A, adequate"}},
    {{"passed": true, "notable": true, "text": "Item not inspected or limited scope — e.g. AC not tested due to temperature"}}
  ]
}}

RULES:
- urgent_items: Items that are deficient, defective, or meet any of these conditions regardless of how the inspector framed them: (1) a system cannot perform its core function right now, (2) involves mold, suspected asbestos, absent CO/smoke detectors, or standing water, (3) is a fire or life safety code issue, (4) involves electrical hazards near water, reversed polarity, fuse panel, or ungrounded outlets, (5) inspector states insurance companies may not cover it. Do not be anchored by words like "recommendation," "maintenance issue," or "for your information" — route based on the physical condition described, not the inspector's disclaimer language
- maintenance_items: Only items the inspector flagged for future attention or planned replacement
- category_items: ALL other deficiencies and observations documented in the report that are NOT already in urgent_items or maintenance_items. Assign each to the closest category: Roof, Exterior, Garage, Attic, Interior, Kitchen, Laundry, Bathroom, Mechanical (covers HVAC/furnace/water heater/electrical panel), or Structure (covers foundation/basement/framing). Do not leave findings out — if it was documented, it belongs here.
- Do NOT duplicate items across urgent_items, maintenance_items, and category_items
- Do NOT add speculative items not documented in the report
- If a finding matches a category key exactly, use it. If not, set category_key to null and fill custom_description
- checklist: 6-10 items summarizing major system status. passed:true for systems in good condition, notable:true for items not inspected or with limited scope. Do NOT repeat items already in urgent_items, maintenance_items, or category_items
- Return ONLY the JSON object, no markdown, no backticks"""

    def clean_raw(raw):
        raw = raw.replace("\x00", "").strip()
        if raw.startswith("```"):
            parts = raw.split("\n", 1)
            raw = parts[1] if len(parts) > 1 else ""
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]
        return raw.strip()

    def attempt_parse(raw):
        cleaned = re.sub(r',\s*([}\]])', r'\1', raw)
        return json.loads(cleaned)

    findings = None
    last_err = None
    for max_tok in [8000, 16000]:
        try:
            print(f"Step 1 attempt with max_tokens={max_tok}...")
            step1_msg = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=max_tok,
                temperature=0,
                system=step1_prompt,
                messages=[{"role": "user", "content": extracted_text}]
            )
            raw1 = clean_raw(step1_msg.content[0].text)
            findings = attempt_parse(raw1)
            print(f"Step 1 succeeded at max_tokens={max_tok}.")
            break
        except Exception as e:
            last_err = e
            retry_msg = 'Retrying with more tokens...' if max_tok < 16000 else 'All retries exhausted.'
            print(f"Step 1 failed at max_tokens={max_tok}: {last_err}. {retry_msg}")

    if findings is None:
        print("Using minimal fallback after all retries failed.")
        findings = {
            "condition": "Maintenance",
            "currency": "USD",
            "location": "Unknown",
            "address": None,
            "urgent_items": [],
            "maintenance_items": [],
            "category_items": [],
            "checklist": [],
            "_parse_error": str(last_err)
        }
        return json.dumps(findings)

    currency = findings.get("currency", "USD")

    def normalize_text(value):
        value = (value or "").lower().strip()
        value = re.sub(r"[^a-z0-9\s/&-]", " ", value)
        value = re.sub(r"\s+", " ", value)
        return value

    def get_item_text(item):
        return normalize_text(" ".join([
            item.get("name", ""),
            item.get("custom_description", ""),
            item.get("trade", "")
        ]))

    def compress_range(low, high):
        if not low or not high or high <= low:
            return low, high
        width = high - low
        if width > low * 2.2:
            high = int(round(low * 4.0 / 50.0) * 50)
        if high - low > 2500 and low < 3000:
            high = int(round((low + 2500) / 50.0) * 50)
        if high <= low:
            high = low + 150
        return int(low), int(high)

    def adjust_range_for_text(text, low, high):
        if not low or not high:
            return low, high

        factor_low = 1.0
        factor_high = 1.0

        if any(word in text for word in ["minor", "small", "hairline", "touch up", "touch-up", "sealant", "caulk", "nail pop", "discoloration"]):
            factor_high *= 0.75
        if any(word in text for word in ["localized", "single area", "single", "one area", "limited area"]):
            factor_high *= 0.85
        if any(word in text for word in ["extensive", "multiple", "several", "widespread", "active leak", "unsupported", "inadequate", "moisture intrusion"]):
            factor_high *= 1.20
        if any(word in text for word in ["replace", "replacement"]):
            factor_low *= 1.05
            factor_high *= 1.10

        low = int(round(low * factor_low / 50.0) * 50)
        high = int(round(high * factor_high / 50.0) * 50)

        if high <= low:
            high = low + 150

        return compress_range(low, high)

    heuristic_bands = {
        "minor_service": {
            "USD": (150, 450),
            "CAD": (200, 550),
            "note": "Typical small repair or service visit"
        },
        "minor_plumbing": {
            "USD": (200, 600),
            "CAD": (250, 750),
            "note": "Typical localized plumbing repair"
        },
        "minor_roof_exterior": {
            "USD": (200, 900),
            "CAD": (250, 1100),
            "note": "Typical localized exterior or roof repair"
        },
        "minor_landscape": {
            "USD": (150, 600),
            "CAD": (200, 750),
            "note": "Typical trimming or basic landscaping service"
        },
        "minor_drywall_trim": {
            "USD": (150, 700),
            "CAD": (200, 850),
            "note": "Typical patching or finish repair"
        },
        "concrete_moderate": {
            "USD": (400, 1800),
            "CAD": (500, 2200),
            "note": "Typical localized concrete or leveling repair"
        },
        "handrail_install": {
            "USD": (350, 1200),
            "CAD": (450, 1500),
            "note": "Typical residential handrail installation"
        },
        "deck_moderate": {
            "USD": (400, 1800),
            "CAD": (500, 2200),
            "note": "Typical localized deck repair"
        },
        "stucco_patch": {
            "USD": (250, 900),
            "CAD": (300, 1100),
            "note": "Typical localized stucco patch or crack repair"
        },
        "siding_patch": {
            "USD": (350, 1500),
            "CAD": (450, 1800),
            "note": "Typical localized siding or trim repair"
        },
        "sealant_repair": {
            "USD": (150, 450),
            "CAD": (200, 550),
            "note": "Typical removal and replacement of sealant"
        },
    }

    keyword_to_band = [
        (["shower sealant", "caulk", "sealant", "tub caulk", "shower caulk"], "sealant_repair"),
        (["toilet", "faucet", "leak", "plumbing", "shower fixture", "sewer penetration", "capping"], "minor_plumbing"),
        (["vent cover", "roof boot", "flashing", "penetration", "roof", "gutter", "downspout"], "minor_roof_exterior"),
        (["vegetation", "shrub", "tree", "overgrowth", "landscap"], "minor_landscape"),
        (["drywall", "nail pop", "settlement crack", "trim", "baseboard", "casing"], "minor_drywall_trim"),
        (["driveway", "slab", "concrete", "undermining", "walkway"], "concrete_moderate"),
        (["handrail", "railing", "guardrail"], "handrail_install"),
        (["deck", "landing", "stairs", "step"], "deck_moderate"),
        (["stucco"], "stucco_patch"),
        (["woodpecker", "siding", "cladding", "trim board"], "siding_patch"),
    ]

    alias_key_map = [
        (["gfci", "ungrounded outlet", "reverse polarity", "outlet", "switch"], "ELEC_OUTLETS_MINOR"),
        (["smoke detector", "co detector", "carbon monoxide detector"], "ELEC_SMOKE_DETECTORS"),
        (["toilet"], "PLUMB_TOILET_REPAIR"),
        (["faucet"], "PLUMB_FAUCET_REPAIR"),
        (["leak", "drip"], "PLUMB_LEAK_MINOR"),
        (["water heater"], "PLUMB_WATER_HEATER"),
        (["sump pump"], "PLUMB_SUMP_PUMP"),
        (["furnace", "boiler", "hvac service"], "HVAC_SERVICE_TUNE"),
        (["ac", "air conditioner", "condenser"], "HVAC_AC_REPLACE"),
        (["duct"], "HVAC_DUCT_REPAIR"),
        (["flashing", "boot", "shingle", "roof repair", "chimney flashing", "roof penetration"], "ROOF_MINOR_REPAIR"),
        (["gutter"], "ROOF_MINOR_REPAIR"),
    ]

    def infer_lookup_key(item):
        text = get_item_text(item)
        for phrases, key in alias_key_map:
            if key in COST_TABLE and any(phrase in text for phrase in phrases):
                return key
        return None

    def infer_heuristic_band(item):
        text = get_item_text(item)
        for phrases, band_name in keyword_to_band:
            if any(phrase in text for phrase in phrases):
                return heuristic_bands.get(band_name)
        trade = normalize_text(item.get("trade", ""))
        if "plumb" in trade:
            return heuristic_bands["minor_plumbing"]
        if "roof" in trade or "exterior" in trade:
            return heuristic_bands["minor_roof_exterior"]
        if "drywall" in trade or "carpenter" in trade or "handyman" in trade:
            return heuristic_bands["minor_drywall_trim"]
        if "landsc" in trade:
            return heuristic_bands["minor_landscape"]
        return heuristic_bands["minor_service"]

    unknown_items = []

    def price_item(item):
        text = get_item_text(item)
        key = item.get("category_key")

        if key and key in COST_TABLE:
            cost_data = get_cost(key, currency)
            low, high = adjust_range_for_text(text, cost_data["low"], cost_data["high"])
            item["cost"] = format_cost_range(low, high, currency)
            item["cost_note"] = cost_data.get("note", "")
            item["cost_source"] = "lookup_table"
            return item

        inferred_key = infer_lookup_key(item)
        if inferred_key:
            cost_data = get_cost(inferred_key, currency)
            low, high = adjust_range_for_text(text, cost_data["low"], cost_data["high"])
            item["cost"] = format_cost_range(low, high, currency)
            item["cost_note"] = cost_data.get("note", "")
            item["cost_source"] = "lookup_inferred"
            item["category_key"] = inferred_key
            return item

        item["cost"] = None
        item["cost_source"] = "pending_ai"
        unknown_items.append(item)
        return item

    findings["urgent_items"] = [price_item(i) for i in findings.get("urgent_items", [])]
    findings["maintenance_items"] = [price_item(i) for i in findings.get("maintenance_items", [])]
    findings["category_items"] = [price_item(i) for i in findings.get("category_items", [])]

    if unknown_items:
        numbered_items = []
        for idx, item in enumerate(unknown_items):
            desc = item.get("custom_description") or item.get("name")
            numbered_items.append(
                f"""{idx}.
NAME: {item.get('name')}
DESCRIPTION: {desc}
TRADE: {item.get('trade', '')}"""
            )
        unknown_text = "\n\n".join(numbered_items)

        step2_prompt = f"""You are a home repair cost estimator with deep knowledge of North American contractor pricing.
Currency: {currency}
Location: {findings.get('location', 'Unknown')}

Goal:
Return realistic, buyer-friendly ballpark repair ranges for common home inspection findings.
These ranges should help buyers feel informed, not alarmed.

Rules:
- Prefer typical localized repair scenarios, not worst-case failures.
- Prefer tighter ranges when possible.
- Do not use a generic fallback range.
- Use the issue name, description, and trade.
- If a finding sounds like a minor repair, keep the range modest.
- If a finding clearly suggests broader work, widen the range only as needed.
- Return every item by index.
- If truly uncertain, set cost to null.

Return ONLY valid JSON array in this exact format:
[
  {{
    "index": 0,
    "cost": "$X - $Y" or null,
    "cost_note": "brief short explanation"
  }}
]

Items:
{unknown_text}"""

        try:
            step2_msg = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1200,
                temperature=0,
                messages=[{"role": "user", "content": step2_prompt}]
            )
            raw2 = clean_raw(step2_msg.content[0].text)
            ai_prices = attempt_parse(raw2)
            price_map = {p["index"]: p for p in ai_prices if isinstance(p, dict) and "index" in p}

            for idx, item in enumerate(unknown_items):
                match = price_map.get(idx)
                if match and match.get("cost"):
                    item["cost"] = match["cost"]
                    item["cost_note"] = match.get("cost_note", "")
                    item["cost_source"] = "ai_estimate"
                else:
                    band = infer_heuristic_band(item)
                    low, high = band[currency]
                    low, high = adjust_range_for_text(get_item_text(item), low, high)
                    item["cost"] = format_cost_range(low, high, currency)
                    item["cost_note"] = band.get("note", "")
                    item["cost_source"] = "heuristic_fallback"
        except Exception as e:
            print(f"Step 2b parse error: {e}")
            for item in unknown_items:
                band = infer_heuristic_band(item)
                low, high = band[currency]
                low, high = adjust_range_for_text(get_item_text(item), low, high)
                item["cost"] = format_cost_range(low, high, currency)
                item["cost_note"] = band.get("note", "")
                item["cost_source"] = "heuristic_fallback"

    def parse_cost_low(cost_str):
        if not cost_str:
            return 0
        try:
            parts = cost_str.replace("$", "").replace(",", "").split("-")
            return int(float(parts[0].strip()))
        except Exception:
            return 0

    def parse_cost_high(cost_str):
        if not cost_str:
            return 0
        try:
            parts = cost_str.replace("$", "").replace(",", "").split("-")
            return int(float(parts[-1].strip()))
        except Exception:
            return 0

    now_low = sum(parse_cost_low(i.get("cost")) for i in findings.get("urgent_items", []))
    now_high = sum(parse_cost_high(i.get("cost")) for i in findings.get("urgent_items", []))
    yr5_low = sum(parse_cost_low(i.get("cost")) for i in findings.get("maintenance_items", []))
    yr5_high = sum(parse_cost_high(i.get("cost")) for i in findings.get("maintenance_items", []))

    now_mid = (now_low + now_high) // 2
    yr5_mid = (yr5_low + yr5_high) // 2

    sym = "$"
    findings["budget_now"] = f"~{sym}{now_mid:,}" if now_mid else f"~{sym}1,500"
    findings["budget_5yr"] = f"~{sym}{yr5_mid:,}" if yr5_mid else f"~{sym}1,500"

    return json.dumps(findings)

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
        model="claude-sonnet-4-5-20250929",
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
NEW QUOTE REQUEST FROM ASSURE INSPECTIONS

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
Assure Inspections AI System
https://www.assureinspections.com
"""
        
        html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #0369a1;">NEW QUOTE REQUEST FROM ASSURE INSPECTIONS</h2>
        
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
            <strong>Assure Inspections AI System</strong><br>
            https://www.assureinspections.com
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
    
    def __init__(self, report_text):
        self.report_text = report_text
        self.client = create_ai_client()
        self.conversation_history = []
        self.question_count = 0
        
    def answer_question(self, question):
        """Answer a customer question"""
        
        # Load Illinois SOP
        try:
            with open('illinois_sop.json', 'r') as f:
                illinois_sop = json.load(f)
            sop_text = json.dumps(illinois_sop, indent=2)
        except FileNotFoundError:
            sop_text = ""
            print("Warning: illinois_sop.json not found")
        
        system_prompt = f"""You are a helpful assistant answering questions about Illinois home inspections.

LEGAL BASIS: Ill. Admin. Code tit. 68, § 1410.200 - Standards of Practice

ILLINOIS HOME INSPECTION STANDARDS:
{sop_text}

═══════════════════════════════════════════════════════════════════════════════
CRITICAL GUARD RAILS - ALWAYS APPLY - NEVER VIOLATE
═══════════════════════════════════════════════════════════════════════════════

1. ALWAYS VALIDATE INSPECTOR'S WORK AND DECISIONS
2. NEVER suggest inspector made an error or missed something
3. NEVER blame the Assure platform for limitations
4. NEVER suggest customer should have hired a different inspector
5. NEVER criticize inspection scope or methods
6. ALWAYS cite Illinois law to back inspector's decisions
7. ALWAYS explain professional judgment when inspector made safety choices
8. NEVER use language that implies inspector was inadequate

FORBIDDEN PHRASES - NEVER USE:
❌ "Inspector should have..."
❌ "Better inspection would have..."
❌ "You might want a different inspector..."
❌ "Assure platform doesn't cover..."
❌ "This is a limitation of home inspection"

═══════════════════════════════════════════════════════════════════════════════
QUESTION TYPE DETECTION - RESPONSE RULES
═══════════════════════════════════════════════════════════════════════════════

DEFENSIVE "WHY DIDN'T..." QUESTIONS:
Examples: "Why didn't he walk on roof?", "Why didn't they open the panel?"
→ ALWAYS validate inspector's decision
→ ALWAYS cite Illinois law about what's required vs optional
→ ALWAYS explain WHY decision was made (safety, legal, best practice)
→ Make inspector look SMART not lazy
Response format: "Per Illinois law, [requirement]. Your inspector [decision] which is [valid/required/smart]. [Explanation]."

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
→ ALWAYS cite Illinois law about what requires specialists
→ ALWAYS explain WHY specialist is needed
→ PROVIDE specific specialist type and typical scope
Example: "Per Illinois standards, [scope] is beyond home inspection. For [evaluation type], hire a licensed [specialist]."

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
7. Always cite Illinois law for "why didn't..." questions
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
"Note: This is based on Illinois home inspection standards (Ill. Admin. Code tit. 68, § 1410.200). For professional guidance, consult licensed specialists in your area."

═══════════════════════════════════════════════════════════════════════════════
THIS PROMPT HANDLES ALL SCENARIOS - NO FURTHER UPDATES NEEDED
═══════════════════════════════════════════════════════════════════════════════

✅ Defensive "why didn't..." → Validate with IL law
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
            model="claude-sonnet-4-5-20250929",
            max_tokens=800,
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