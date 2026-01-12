import PyPDF2
import os
from anthropic import Anthropic

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
4. NO markdown - use plain text
5. NO financial advice
6. NO purchase recommendations

FORMAT: Use short paragraphs with headers like "Issue:", "Finding:", "What this means:"
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