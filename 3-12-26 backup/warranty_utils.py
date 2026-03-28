"""
WARRANTY UTILITIES
Handles warranty document parsing and Q&A
Simplified to match home inspection pattern exactly
"""

import PyPDF2
import os
from anthropic import Anthropic


def extract_warranty_text(pdf_path):
    """
    Extract all text from warranty PDF document
    Same as inspection report extraction
    """
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
        raise Exception(f"Error extracting warranty PDF text: {str(e)}")


def create_ai_client():
    """Create Anthropic client"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    return Anthropic(api_key=api_key)


def parse_warranty_coverage(warranty_text, builder_name, warranty_type):
    """
    Parse warranty document into coverage summary
    Returns plain text summary (not JSON) - matches inspection pattern
    """
    client = create_ai_client()
    
    system_prompt = f"""You are an expert at summarizing home warranty documents.

Create a clear, organized summary of warranty coverage for {builder_name} ({warranty_type}) that includes:
1. Coverage periods (1-year, 2-year, 5-year, 10-year, etc.)
2. What IS covered (systems, components, materials)
3. What is NOT covered (exclusions)
4. How to file claims
5. Key terms and conditions

Be concise and factual. Only include what's actually in the document."""
    
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=800,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": f"Please summarize this warranty document:\n\n{warranty_text}"
        }]
    )
    
    return message.content[0].text


class WarrantyCoverageQA:
    """
    Q&A system for warranty coverage
    Handles warranty questions same way as inspection Q&A
    """
    
    def __init__(self, warranty_text, builder_name, warranty_type):
        """
        warranty_text: Full extracted warranty document text
        builder_name: "Travelers", "National Home Warranty", etc.
        warranty_type: "2-5-10", "10-year", etc.
        """
        self.warranty_text = warranty_text
        self.builder_name = builder_name
        self.warranty_type = warranty_type
        self.client = create_ai_client()
        self.conversation_history = []
        self.question_count = 0
    
    def answer_question(self, question):
        """
        Answer customer question about warranty coverage
        Example: "Is the electrical issue covered?"
        
        Returns: Answer text with formatting
        """
        
        system_prompt = f"""You are helping homeowners understand their {self.builder_name} {self.warranty_type} warranty coverage.

Your job is to answer questions about what IS or IS NOT covered, based on the warranty document provided.

RESPONSE FORMAT - Use **bold** ONLY for:
- **Coverage Status:**
- **What this means:**
- **Next Steps:**
- **Important:**

NO other markdown. Plain text for explanations.

TONE:
- Professional, clear, factual
- Conservative about coverage (when in doubt, say NOT covered)
- Empathetic to homeowner concerns
- Cite specific warranty sections when relevant
- If you don't know from the warranty document, say so

RULES:
1. Base answer ONLY on the warranty document provided
2. If not mentioned in warranty, say "This isn't addressed in your warranty"
3. Be honest about coverage limits
4. Recommend contacting warranty company for claims
5. Never make up coverage information"""
        
        if self.question_count == 0:
            # First question - include full warranty text as context
            context_message = f"""Here is your warranty document:

<WARRANTY_DOCUMENT>
{self.warranty_text}
</WARRANTY_DOCUMENT>

Customer Question about coverage: {question}"""
        else:
            # Follow-up question - just the question (context already in history)
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
