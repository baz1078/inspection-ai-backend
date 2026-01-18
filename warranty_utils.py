"""
WARRANTY UTILITIES
Handles warranty document parsing, coverage rule extraction, and claims analysis
"""

import PyPDF2
import json
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


def parse_warranty_coverage(warranty_text, builder_name, warranty_type):
    """
    Parse warranty document into structured coverage rules
    Returns JSON structure like warranty_config.json
    Uses Claude to intelligently extract coverage information
    """
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    system_prompt = f"""You are an expert at parsing warranty documents and extracting coverage rules.

Your job is to analyze a warranty document for {builder_name} ({warranty_type}) and extract:
1. Coverage periods (1-year, 2-year, 5-year, 10-year, etc.)
2. What IS covered (materials, labor, systems, components)
3. What is NOT covered (exclusions, limitations)
4. Coverage amounts/limits
5. How to file claims

Return ONLY valid JSON with this structure:
{{
  "builder_name": "{builder_name}",
  "warranty_type": "{warranty_type}",
  "coverage_periods": {{
    "materials_labor_1yr": {{"duration": "1 year", "items": ["list of covered items"]}},
    "materials_labor_2yr": {{"duration": "2 years", "items": ["electrical", "plumbing", "hvac", ...]}},
    "building_envelope_5yr": {{"duration": "5 years", "items": [...]}},
    "structural_10yr": {{"duration": "10 years", "items": [...]}}
  }},
  "covered_items": {{
    "electrical": ["description of coverage"],
    "plumbing": ["description of coverage"],
    "hvac": ["description of coverage"],
    "structural": ["description of coverage"],
    "roofing": ["description of coverage"],
    "exterior": ["description of coverage"]
  }},
  "exclusions": ["list of what is NOT covered"],
  "limits": {{"coverage_limit": "amount", "per_claim": "amount"}},
  "claim_process": ["step 1", "step 2", "step 3"],
  "key_definitions": {{
    "covered_defect": "definition",
    "readily_accessible": "definition"
  }}
}}"""
    
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2000,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": f"Parse this warranty document and extract coverage rules:\n\n{warranty_text}"
        }]
    )
    
    try:
        response_text = message.content[0].text
        # Extract JSON from response (handle code blocks if present)
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0]
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0]
        
        coverage_rules = json.loads(response_text)
        return json.dumps(coverage_rules, indent=2)
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse warranty coverage from Claude response: {str(e)}")


class WarrantyCoverageAnalyzer:
    """
    Analyzes whether inspection findings are covered under warranty
    Compares inspection findings with warranty coverage rules
    """
    
    def __init__(self, coverage_rules_json):
        """
        coverage_rules_json: JSON string or dict of parsed warranty coverage
        """
        if isinstance(coverage_rules_json, str):
            self.coverage_rules = json.loads(coverage_rules_json)
        else:
            self.coverage_rules = coverage_rules_json
        
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    def analyze_claim(self, inspection_finding, issue_description):
        """
        Determine if an inspection finding is covered by warranty
        
        Args:
            inspection_finding: The exact finding from inspection report
            issue_description: Category/type of issue (electrical, plumbing, etc.)
        
        Returns:
            {
                'claimability': 'COVERED' | 'NOT_COVERED' | 'PARTIAL' | 'REQUIRES_SPECIALIST',
                'reasoning': 'explanation',
                'warranty_section': 'which section applies',
                'coverage_period': '2 years' or '5 years' etc,
                'next_steps': ['step 1', 'step 2']
            }
        """
        
        coverage_text = json.dumps(self.coverage_rules, indent=2)
        
        system_prompt = f"""You are an expert analyzing home warranty coverage claims.

WARRANTY COVERAGE RULES:
{coverage_text}

Your job is to determine if an inspection finding IS or IS NOT covered by this warranty.

IMPORTANT RULES:
1. Only mark as COVERED if the finding explicitly matches warranty coverage
2. If not explicitly covered, it's NOT_COVERED
3. PARTIAL = part of finding is covered, part is not
4. REQUIRES_SPECIALIST = needs professional evaluation to determine coverage
5. Always cite the specific warranty section
6. Be conservative - when in doubt, say NOT_COVERED

Return ONLY valid JSON:
{{
  "claimability": "COVERED|NOT_COVERED|PARTIAL|REQUIRES_SPECIALIST",
  "warranty_section": "Section name from warranty",
  "coverage_period": "e.g., 2 years, 5 years, 10 years",
  "reasoning": "Clear explanation citing warranty language",
  "is_covered_under": "What specific part of warranty applies",
  "exclusions_apply": "If any exclusions prevent coverage",
  "next_steps": ["Step 1 to file claim", "Step 2", etc],
  "recommended_specialist": "If professional eval needed"
}}"""
        
        message = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1000,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"""Inspection Finding: {inspection_finding}

Issue Category: {issue_description}

Is this covered by the warranty? Analyze and respond with JSON only."""
            }]
        )
        
        try:
            response_text = message.content[0].text
            # Extract JSON
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0]
            
            analysis = json.loads(response_text)
            return analysis
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse warranty analysis: {str(e)}")


class WarrantyQASystem:
    """
    Enhanced Q&A system that includes warranty context
    Answers questions about whether issues are covered under warranty
    """
    
    def __init__(self, inspection_text, warranty_coverage_rules, builder_name, warranty_type):
        """
        inspection_text: Full extracted inspection report text
        warranty_coverage_rules: Parsed warranty rules (JSON string or dict)
        builder_name: "Travelers", "National Home Warranty", etc.
        warranty_type: "2-5-10", "10-year", etc.
        """
        self.inspection_text = inspection_text
        self.warranty_type = warranty_type
        self.builder_name = builder_name
        
        if isinstance(warranty_coverage_rules, str):
            self.coverage_rules = json.loads(warranty_coverage_rules)
        else:
            self.coverage_rules = warranty_coverage_rules
        
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.conversation_history = []
        self.question_count = 0
    
    def answer_warranty_question(self, question):
        """
        Answer customer question about warranty coverage
        Example: "Is the electrical issue covered?"
        """
        
        coverage_text = json.dumps(self.coverage_rules, indent=2)
        
        system_prompt = f"""You are helping homeowners understand their {self.builder_name} {self.warranty_type} warranty.

WARRANTY COVERAGE:
{coverage_text}

INSPECTION REPORT:
{self.inspection_text}

YOUR JOB:
1. Answer questions about what IS or IS NOT covered
2. Cite specific warranty sections
3. Explain coverage periods (1yr, 2yr, 5yr, 10yr)
4. Provide clear claim process steps
5. Be honest - some issues just aren't covered
6. Recommend professional evaluation when needed

RESPONSE FORMAT:
Use **bold** ONLY for:
- Issue:
- Coverage Status:
- Warranty Section:
- Reasoning:
- Next Steps:

NO other markdown. Plain text for explanations.

TONE:
- Professional, clear, honest
- Conservative about coverage (when in doubt, say NOT covered)
- Empathetic to homeowner concerns
- Cite exact warranty language"""
        
        if self.question_count == 0:
            context_message = f"""Here is the inspection report:

<INSPECTION_REPORT>
{self.inspection_text}
</INSPECTION_REPORT>

Customer Question about warranty coverage: {question}"""
        else:
            context_message = question
        
        self.conversation_history.append({"role": "user", "content": context_message})
        
        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1000,
            system=system_prompt,
            messages=self.conversation_history
        )
        
        assistant_message = response.content[0].text
        self.conversation_history.append({"role": "assistant", "content": assistant_message})
        self.question_count += 1
        
        return assistant_message
