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
    """Returns structured JSON analysis - separate from summary to protect existing flow"""
    client = create_ai_client()
    
    system_prompt = """You are an expert home inspection analyst. Analyze this inspection report 
and return ONLY a valid JSON object, no markdown, no backticks, no explanation:
{
  "condition": "Good" or "Fair" or "Poor",
  "budget_now": "$X,XXX - $X,XXX",
  "budget_5yr": "$XX,XXX - $XX,XXX",
  "currency": "USD" or "CAD",
  "location": "City, State/Province detected from report",
  "urgent_items": [
    {"name": "Issue", "cost": "$X,XXX", "timeline": "Immediate", "trade": "Electrician"}
  ],
  "maintenance_items": [
    {"name": "Issue", "cost": "$X,XXX", "timeline": "1-3 years", "trade": "Roofer"}
  ],
  "checklist": [
    {"passed": true, "text": "Roof in acceptable condition"},
    {"passed": false, "text": "GFCI outlets missing in kitchen and bathroom"}
  ]
}

PRICING RULES:
- Detect the property address from the report
- If US property: use USD and local metro contractor rates
- If Canadian property: use CAD and local provincial contractor rates  
- Be specific to the metro area (Chicagoland vs rural IL, Edmonton vs Calgary, etc.)
- Base estimates on current contractor rates for that market
- Be conservative - give ranges, not single numbers"""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": extracted_text}]
    )
    
    raw = message.content[0].text.replace('\x00', '')
    
    raw = raw.strip()
    if raw.startswith('```'):
        raw = raw.split('\n', 1)[1]
    if raw.endswith('```'):
        raw = raw.rsplit('```', 1)[0]
    raw = raw.strip()
    
    return raw



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