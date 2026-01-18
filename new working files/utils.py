import PyPDF2
import os
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
    """Generate AI summary"""
    client = create_ai_client()
    
    system_prompt = """You are an expert at summarizing home inspection reports in a professional, balanced way.
Your job is to create a brief summary (2-3 paragraphs) that:
1. Clearly explains what was inspected
2. Highlights findings in order of priority
3. Uses calm, professional language - not alarmist
4. Presents issues factually without exaggeration

Do NOT make up information. Only summarize what's in the report."""
    
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=500,
        system=system_prompt,
        messages=[{"role": "user", "content": f"Please summarize this inspection report:\n\n{report_text}"}]
    )
    
    return message.content[0].text


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
        
        system_prompt = """You are a helpful assistant answering questions about a home inspection report.

TONE: Professional, balanced, factual, conversational
RULES:
1. ONLY answer from the inspection report
2. If info not in report: "This wasn't covered in the inspection"
3. For costs: "Get quotes from licensed professionals"
4. Use **bold** ONLY for these headers: Issue:, Finding:, What this means:, Action recommended:
5. NO other markdown - use plain text
6. NO financial advice
7. NO purchase recommendations

FORMAT: Use short paragraphs with headers like:
**Issue:** [description]
**Finding:** [what was found]
**What this means:** [explanation]
**Action recommended:** [what to do]
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
