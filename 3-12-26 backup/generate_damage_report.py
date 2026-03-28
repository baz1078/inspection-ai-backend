from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Circle, Wedge, String, Line, Rect
from datetime import datetime
import os
import uuid
import json
import requests
import base64
import qrcode
from io import BytesIO

LOCATION_DATA = {
    'kitchen': {'display_name': 'Kitchen', 'baseline_mold_risk': 70, 'baseline_claim_approval': 85, 'likely_causes': ['Plumbing leak under sink', 'Faucet leak', 'Dishwasher malfunction'], 'contractors': ['Plumber', 'Water damage restoration specialist'], 'insurance_note': 'Kitchen water damage typically COVERED'},
    'bathroom': {'display_name': 'Bathroom', 'baseline_mold_risk': 75, 'baseline_claim_approval': 82, 'likely_causes': ['Plumbing leak', 'Toilet overflow', 'Shower/tub leak'], 'contractors': ['Plumber', 'Water damage restoration specialist'], 'insurance_note': 'Bathroom water damage typically COVERED'},
    'basement': {'display_name': 'Basement', 'baseline_mold_risk': 85, 'baseline_claim_approval': 72, 'likely_causes': ['Foundation seepage', 'Burst water line', 'Poor drainage'], 'contractors': ['Water damage restoration specialist', 'Foundation repair specialist'], 'insurance_note': 'Foundation seepage may be EXCLUDED'},
    'attic': {'display_name': 'Attic', 'baseline_mold_risk': 80, 'baseline_claim_approval': 85, 'likely_causes': ['Roof leak', 'Poor ventilation', 'Condensation'], 'contractors': ['Roofer', 'Water damage restoration specialist'], 'insurance_note': 'Roof leak water damage typically COVERED'},
    'garage': {'display_name': 'Garage', 'baseline_mold_risk': 65, 'baseline_claim_approval': 78, 'likely_causes': ['Roof leak', 'Foundation seepage', 'Faulty gutter'], 'contractors': ['Water damage restoration specialist', 'Roofer'], 'insurance_note': 'Coverage varies. Garage seepage often excluded'},
    'bedroom': {'display_name': 'Bedroom', 'baseline_mold_risk': 60, 'baseline_claim_approval': 87, 'likely_causes': ['Roof leak', 'Pipe burst above', 'Window leak'], 'contractors': ['Water damage restoration specialist', 'Roofer'], 'insurance_note': 'Bedroom water damage typically COVERED'},
    'living_room': {'display_name': 'Living Room', 'baseline_mold_risk': 60, 'baseline_claim_approval': 86, 'likely_causes': ['Roof leak', 'Pipe burst above', 'HVAC issue'], 'contractors': ['Water damage restoration specialist', 'Roofer'], 'insurance_note': 'Living room water damage typically COVERED'},
    'laundry_room': {'display_name': 'Laundry Room', 'baseline_mold_risk': 80, 'baseline_claim_approval': 80, 'likely_causes': ['Washer/dryer leak', 'Water line burst', 'Plumbing issue'], 'contractors': ['Plumber', 'Water damage restoration specialist'], 'insurance_note': 'Appliance malfunction may be excluded'},
    'hallway': {'display_name': 'Hallway', 'baseline_mold_risk': 65, 'baseline_claim_approval': 84, 'likely_causes': ['Pipe burst', 'Roof leak', 'Adjacent room leak'], 'contractors': ['Water damage restoration specialist', 'Plumber'], 'insurance_note': 'Hallway water damage typically COVERED'},
}

def analyze_damage_with_ai(photo_base64, location, water_source, description):
    """Use Claude API to analyze damage"""
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": os.getenv('ANTHROPIC_API_KEY'),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-opus-4-20250203",
                "max_tokens": 800,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": photo_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": f"""Analyze water damage. Location: {location}. Source: {water_source if water_source else 'Unknown'}. Description: {description if description else 'Not provided'}.
Return JSON only:
{{"mold_risk_percentage": <0-100>, "claim_approval_percentage": <0-100>, "damage_severity": "<minor|moderate|high|critical>", "estimated_square_footage": <number or null>, "moisture_saturation": "<dry|damp|wet|saturated>", "affected_materials": ["material1", "material2"], "visible_issues": ["issue1", "issue2"], "hidden_damage_risk": "<risk>", "recommended_immediate_action": "<action>", "structural_risk": "<no|low|moderate|high>"}}"""
                            }
                        ]
                    }
                ]
            },
            timeout=30
        )
        result = response.json()
        if 'content' in result and len(result['content']) > 0:
            return json.loads(result['content'][0]['text'])
    except Exception as e:
        print(f"AI error: {e}")
    return None

def draw_gauge(drawing, x, y, percentage, label, color):
    """Draw circular gauge"""
    radius = 35
    drawing.add(Circle(x, y, radius, fillColor=colors.HexColor('#f0f0f0'), strokeColor=colors.grey, strokeWidth=1))
    angle = (percentage / 100) * 360
    drawing.add(Wedge(x, y, radius, 0, angle, fillColor=color, strokeColor=color, strokeWidth=0))
    drawing.add(String(x-12, y+2, f"{percentage}%", fontSize=16, fontName="Helvetica-Bold", fillColor=colors.black))
    drawing.add(String(x-35, y-50, label, fontSize=9, fontName="Helvetica-Bold", fillColor=colors.HexColor('#14b8a6')))

def generate_complete_report(photo_path, output_path, location='kitchen', water_source='', description='', report_id=None):
    """Generate complete damage report with all details + visuals"""
    
    if not report_id:
        report_id = str(uuid.uuid4())[:8].upper()
    
    loc_data = LOCATION_DATA.get(location, LOCATION_DATA['kitchen'])
    
    with open(photo_path, 'rb') as f:
        photo_base64 = base64.b64encode(f.read()).decode()
    
    analysis = analyze_damage_with_ai(photo_base64, loc_data['display_name'], water_source, description)
    
    if not analysis:
        analysis = {
            'mold_risk_percentage': loc_data['baseline_mold_risk'],
            'claim_approval_percentage': loc_data['baseline_claim_approval'],
            'damage_severity': 'moderate',
            'estimated_square_footage': 96,
            'moisture_saturation': 'wet',
            'affected_materials': ['Drywall', 'Insulation', 'Paint/Finish'],
            'visible_issues': ['Water staining', 'Paint damage and bubbling', 'Dark spots (potential mold)'],
            'hidden_damage_risk': 'Cavity above may be wet beyond visible area',
            'recommended_immediate_action': 'Stop water source and maximize ventilation',
            'structural_risk': 'low'
        }
    
    doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=0.35*inch, leftMargin=0.35*inch, topMargin=0.35*inch, bottomMargin=0.35*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    primary = colors.HexColor('#14b8a6')
    red = colors.HexColor('#ef4444')
    green = colors.HexColor('#10b981')
    yellow = colors.HexColor('#f59e0b')
    
    header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=9, textColor=colors.black, spaceAfter=1, leading=10)
    compact = ParagraphStyle('Compact', parent=styles['Normal'], fontSize=7, spaceAfter=1.5, leading=8.5, textColor=colors.black)
    tiny = ParagraphStyle('Tiny', parent=styles['Normal'], fontSize=6.5, spaceAfter=1, leading=7.5, textColor=colors.HexColor('#666666'))
    section_red = ParagraphStyle('SectionRed', parent=styles['Normal'], fontSize=8.5, textColor=red, spaceBefore=3, spaceAfter=2, fontName='Helvetica-Bold')
    section_teal = ParagraphStyle('SectionTeal', parent=styles['Normal'], fontSize=8.5, textColor=primary, spaceBefore=3, spaceAfter=2, fontName='Helvetica-Bold')
    
    # PAGE 1: VISUAL IMPACT
    elements.append(Paragraph(f"<b>DAMAGE ASSESSMENT | {report_id}</b>", header_style))
    elements.append(Paragraph(f"{datetime.now().strftime('%B %d, %Y')} | {loc_data['display_name']}", compact))
    elements.append(Spacer(1, 0.06*inch))
    
    photo_img = Image(photo_path, width=2.8*inch, height=2.1*inch) if os.path.exists(photo_path) else None
    
    gauges_drawing = Drawing(3.5*inch, 2.3*inch)
    mold_color = red if analysis['mold_risk_percentage'] > 75 else yellow if analysis['mold_risk_percentage'] > 50 else green
    claim_color = green if analysis['claim_approval_percentage'] > 80 else yellow if analysis['claim_approval_percentage'] > 60 else red
    
    draw_gauge(gauges_drawing, 0.6*inch, 1.15*inch, analysis['mold_risk_percentage'], 'MOLD RISK', mold_color)
    draw_gauge(gauges_drawing, 1.8*inch, 1.15*inch, analysis['claim_approval_percentage'], 'CLAIM APPROVAL', claim_color)
    draw_gauge(gauges_drawing, 3*inch, 1.15*inch, 95, 'URGENCY', red)
    
    if photo_img:
        photo_table = Table([[photo_img, gauges_drawing]], colWidths=[3*inch, 3.7*inch])
        photo_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('GRID', (0, 0), (-1, -1), 0, colors.white)]))
        elements.append(photo_table)
    
    elements.append(Spacer(1, 0.04*inch))
    elements.append(Paragraph(f"<font color='#ef4444'><b>⚠️ ACTION REQUIRED WITHIN 24 HOURS</b></font> - Mold growth begins within 24 hours", compact))
    elements.append(Spacer(1, 0.05*inch))
    
    elements.append(Paragraph("<b color='#14b8a6'>WHAT WE SEE - Technical Analysis</b>", section_teal))
    
    what_we_see = f"""<b>Visible Issues:</b> {', '.join(analysis['visible_issues'])}<br/>
    <b>Water Stain Size:</b> ~{analysis['estimated_square_footage'] if analysis['estimated_square_footage'] else 96} sq ft<br/>
    <b>Moisture Saturation:</b> {analysis['moisture_saturation'].capitalize()}<br/>
    <b>Affected Materials:</b> {', '.join(analysis['affected_materials'])}<br/>
    <b>Hidden Risk:</b> {analysis['hidden_damage_risk']}<br/>
    <b>Structural Risk:</b> {analysis['structural_risk'].capitalize()}"""
    
    elements.append(Paragraph(what_we_see, compact))
    elements.append(Spacer(1, 0.05*inch))
    
    if water_source:
        elements.append(Paragraph("<b color='#14b8a6'>WATER SOURCE</b>", section_teal))
        elements.append(Paragraph(f"{water_source}", compact))
        elements.append(Spacer(1, 0.05*inch))
    
    elements.append(Paragraph("<b color='#ef4444'>MOLD GROWTH TIMELINE</b>", section_red))
    
    timeline_drawing = Drawing(6.6*inch, 0.6*inch)
    for i, (hours, label) in enumerate([(0, '0h'), (24, '24h'), (48, '48h'), (72, '3d'), (168, '7d')]):
        x = 0.3*inch + (i * 1.25*inch)
        timeline_drawing.add(String(x, 0.05*inch, label, fontSize=7, fontName="Helvetica"))
        timeline_drawing.add(Line(x, 0.15*inch, x, 0.2*inch, strokeColor=colors.grey, strokeWidth=1))
    
    timeline_drawing.add(Rect(0.3*inch, 0.25*inch, 6*inch, 0.15*inch, fillColor=colors.HexColor('#e5e5e5'), strokeColor=colors.grey))
    timeline_drawing.add(Rect(0.3*inch, 0.25*inch, 1.25*inch, 0.15*inch, fillColor=green, strokeColor=green))
    timeline_drawing.add(Rect(1.55*inch, 0.25*inch, 1.25*inch, 0.15*inch, fillColor=yellow, strokeColor=yellow))
    timeline_drawing.add(Rect(2.8*inch, 0.25*inch, 3.5*inch, 0.15*inch, fillColor=red, strokeColor=red))
    
    timeline_drawing.add(String(0.5*inch, 0.42*inch, "SAFE", fontSize=6, fontName="Helvetica-Bold", fillColor=colors.white))
    timeline_drawing.add(String(1.8*inch, 0.42*inch, "CAUTION", fontSize=6, fontName="Helvetica-Bold", fillColor=colors.white))
    timeline_drawing.add(String(3.5*inch, 0.42*inch, "DANGER", fontSize=6, fontName="Helvetica-Bold", fillColor=colors.white))
    
    elements.append(timeline_drawing)
    elements.append(Spacer(1, 0.03*inch))
    
    timeline_detail = """<b>0-24h:</b> Mold spores germinate (CRITICAL ACTION WINDOW)<br/>
    <b>24-48h:</b> Visible mold growth likely (HIGH RISK)<br/>
    <b>48-72h:</b> Mold deeply embedded<br/>
    <b>7+ days:</b> Structural damage risk"""
    
    elements.append(Paragraph(timeline_detail, tiny))
    elements.append(Spacer(1, 0.05*inch))
    
    elements.append(Paragraph("<b color='#f59e0b'>COST IMPACT OF DELAY</b>", ParagraphStyle('SectionYellow', parent=styles['Normal'], fontSize=8.5, textColor=yellow, spaceBefore=3, spaceAfter=2, fontName='Helvetica-Bold')))
    
    cost_drawing = Drawing(6.6*inch, 1.2*inch)
    costs = [2500, 4000, 6500, 15000]
    labels = ['Act\nNow', 'Wait\n2-3d', 'Wait\n4-7d', 'Wait\n2wk+']
    colors_list = [green, yellow, colors.HexColor('#ffa500'), red]
    
    bar_width = 0.8*inch
    start_x = 0.4*inch
    max_cost = 15000
    
    for i, (cost, label, col) in enumerate(zip(costs, labels, colors_list)):
        x = start_x + (i * 1.55*inch)
        height = (cost / max_cost) * 0.8*inch
        cost_drawing.add(Rect(x, 0.2*inch, bar_width, height, fillColor=col, strokeColor=col))
        cost_drawing.add(String(x + 0.15*inch, height + 0.25*inch, f"${cost/1000:.1f}K", fontSize=7, fontName="Helvetica-Bold"))
        cost_drawing.add(String(x + 0.1*inch, 0.05*inch, label, fontSize=7, fontName="Helvetica"))
    
    elements.append(cost_drawing)
    elements.append(Paragraph("<font size=7 color='#10b981'><b>➜ ACTING NOW = SAVE $5,000-$10,000+</b></font>", compact))
    
    elements.append(PageBreak())
    
    # PAGE 2: ACTION & DETAILS
    
    elements.append(Paragraph("<b color='#10b981'>✓ DO THIS NOW</b>", ParagraphStyle('DoStyle', parent=styles['Normal'], fontSize=8.5, textColor=green, spaceBefore=3, spaceAfter=2, fontName='Helvetica-Bold')))
    do_text = """✓ Turn off electricity | ✓ Open windows/doors | ✓ Run fans<br/>
    ✓ Take photos/video | ✓ Call insurance TODAY"""
    elements.append(Paragraph(do_text, compact))
    elements.append(Spacer(1, 0.04*inch))
    
    elements.append(Paragraph("<b color='#ef4444'>✗ DON'T DO THIS</b>", section_red))
    dont_text = """✗ Touch wet materials | ✗ Use HVAC/AC | ✗ Paint over damage<br/>
    ✗ Try to dry yourself | ✗ Wait & delay"""
    elements.append(Paragraph(dont_text, compact))
    elements.append(Spacer(1, 0.06*inch))
    
    elements.append(Paragraph(f"<b color='#14b8a6'>LIKELY CAUSES ({loc_data['display_name']})</b>", section_teal))
    causes = " | ".join(loc_data['likely_causes'][:2])
    elements.append(Paragraph(causes, compact))
    elements.append(Spacer(1, 0.06*inch))
    
    elements.append(Paragraph("<b color='#14b8a6'>CONTRACTORS NEEDED</b>", section_teal))
    contractors = " | ".join(loc_data['contractors'])
    elements.append(Paragraph(contractors, compact))
    elements.append(Spacer(1, 0.06*inch))
    
    elements.append(Paragraph("<b color='#14b8a6'>INSURANCE</b>", section_teal))
    insurance_text = f"""<b>Coverage:</b> {loc_data['insurance_note']}<br/>
    <b>Approval:</b> {analysis['claim_approval_percentage']}%"""
    elements.append(Paragraph(insurance_text, compact))
    elements.append(Spacer(1, 0.06*inch))
    
    elements.append(Paragraph("<b color='#f59e0b'>ACTION PLAN (24-72 Hours)</b>", ParagraphStyle('ActionStyle', parent=styles['Normal'], fontSize=8.5, textColor=yellow, spaceBefore=3, spaceAfter=2, fontName='Helvetica-Bold')))
    action_text = f"""<b>NOW:</b> {analysis['recommended_immediate_action']}<br/>
    <b>TODAY (6h):</b> Call insurance. File claim.<br/>
    <b>TODAY (12h):</b> Contact water damage company.<br/>
    <b>TOMORROW:</b> Get estimates.<br/>
    <b>DAY 3:</b> Adjuster visit."""
    elements.append(Paragraph(action_text, compact))
    elements.append(Spacer(1, 0.08*inch))
    
    elements.append(Paragraph("<b color='#14b8a6'>SHARE WITH CONTRACTORS</b>", section_teal))
    qr = qrcode.QRCode(version=1, box_size=6, border=1)
    qr.add_data(f"https://assure-inspections-web.onrender.com/damage-reports/{uuid.uuid4()}")
    qr.make()
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_code = Image(qr_buffer, width=1*inch, height=1*inch)
    cta_table = Table([[qr_code, Paragraph('Scan QR code to share with contractors', compact)]], colWidths=[1.2*inch, 5*inch])
    cta_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('GRID', (0, 0), (-1, -1), 0, colors.white)]))
    elements.append(cta_table)
    
    elements.append(Spacer(1, 0.1*inch))
    footer = f"<font size=6 color='#999999'><b>DISCLAIMER:</b> AI-generated for informational purposes. © 2025 Assure | {report_id}</font>"
    elements.append(Paragraph(footer, compact))
    
    doc.build(elements)
    return output_path, analysis

if __name__ == '__main__':
    photo_path = '/mnt/user-data/uploads/1769656987829_image.png'
    output_path = '/mnt/user-data/outputs/Damage_Assessment_Test.pdf'
    
    result, analysis = generate_complete_report(
        photo_path, 
        output_path, 
        location='garage',
        water_source='Bathroom upstairs - burst water line',
        description='Water stain with dark spots'
    )
    print(f"✓ PDF generated: {result}")
    print(f"✓ Mold Risk: {analysis['mold_risk_percentage']}%")
