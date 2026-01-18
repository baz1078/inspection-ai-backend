"""
NEW WARRANTY ENDPOINTS - Add these to app.py

These endpoints handle warranty document upload, parsing, and claims analysis
NO changes to existing inspection endpoints
"""

# ============================================================================
# WARRANTY ENDPOINTS
# ============================================================================

@app.route('/api/upload-warranty/<report_id>', methods=['POST'])
def upload_warranty(report_id):
    """
    Upload warranty document for an inspection report
    Creates link between inspection and warranty
    
    Expected multipart form data:
    - file: PDF warranty document
    - builder_name: "Travelers", "National Home Warranty", "Dweller", etc.
    - warranty_type: "2-5-10", "10-year", etc.
    """
    try:
        # Verify report exists
        report = InspectionReport.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get warranty metadata from form
        builder_name = request.form.get('builder_name', 'Unknown Builder')
        warranty_type = request.form.get('warranty_type', 'Standard')
        jurisdiction = request.form.get('jurisdiction', 'USA')
        
        # Save file
        filepath = save_uploaded_file(file, app.config['UPLOAD_FOLDER'])
        
        # Extract warranty text
        print(f"Extracting text from warranty PDF...")
        warranty_text = extract_warranty_text(filepath)
        
        # Parse warranty coverage rules
        print(f"Parsing warranty coverage rules...")
        from warranty_utils import parse_warranty_coverage
        coverage_rules_json = parse_warranty_coverage(warranty_text, builder_name, warranty_type)
        
        # Create WarrantyDocument record
        warranty_doc = WarrantyDocument(
            builder_name=builder_name,
            warranty_type=warranty_type,
            jurisdiction=jurisdiction,
            file_path=filepath,
            original_filename=secure_filename(file.filename),
            file_size=os.path.getsize(filepath),
            extracted_text=warranty_text,
            coverage_rules=coverage_rules_json,
            is_active=True
        )
        
        db.session.add(warranty_doc)
        db.session.commit()
        
        # Link warranty to report
        report_warranty = ReportWarranty(
            report_id=report_id,
            warranty_id=warranty_doc.id,
            warranty_start_date=datetime.utcnow()  # Could extract from doc
        )
        
        db.session.add(report_warranty)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'warranty_id': warranty_doc.id,
            'builder_name': builder_name,
            'warranty_type': warranty_type,
            'message': f'{builder_name} warranty uploaded successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error uploading warranty: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/warranty/<report_id>/<warranty_id>', methods=['GET'])
def get_warranty_details(report_id, warranty_id):
    """Get warranty document details and coverage rules"""
    try:
        warranty = WarrantyDocument.query.get(warranty_id)
        if not warranty:
            return jsonify({'error': 'Warranty not found'}), 404
        
        # Parse coverage rules
        coverage_rules = json.loads(warranty.coverage_rules)
        
        return jsonify({
            'warranty_id': warranty.id,
            'builder_name': warranty.builder_name,
            'warranty_type': warranty.warranty_type,
            'jurisdiction': warranty.jurisdiction,
            'coverage_rules': coverage_rules,
            'created_at': warranty.created_at.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/warranty-claim-check/<report_id>/<warranty_id>', methods=['POST'])
def check_warranty_claim(report_id, warranty_id):
    """
    Check if an inspection finding is covered under warranty
    
    Expected JSON:
    {
        "inspection_finding": "Electrical outlet not working in master bedroom",
        "issue_type": "electrical"
    }
    
    Returns:
    {
        "claimability": "COVERED" | "NOT_COVERED" | "PARTIAL" | "REQUIRES_SPECIALIST",
        "warranty_section": "Section 2.1 - Materials and Labour (2 Year)",
        "coverage_period": "2 years",
        "reasoning": "...",
        "next_steps": [...]
    }
    """
    try:
        data = request.get_json()
        if not data or 'inspection_finding' not in data:
            return jsonify({'error': 'Missing inspection_finding'}), 400
        
        inspection_finding = data['inspection_finding']
        issue_type = data.get('issue_type', 'general')
        
        # Get warranty document
        warranty = WarrantyDocument.query.get(warranty_id)
        if not warranty:
            return jsonify({'error': 'Warranty not found'}), 404
        
        # Get coverage rules
        coverage_rules = json.loads(warranty.coverage_rules)
        
        # Analyze claim using warranty analyzer
        from warranty_utils import WarrantyCoverageAnalyzer
        analyzer = WarrantyCoverageAnalyzer(coverage_rules)
        analysis = analyzer.analyze_claim(inspection_finding, issue_type)
        
        # Store query in database
        warranty_query = WarrantyQuery(
            report_id=report_id,
            warranty_id=warranty_id,
            customer_question=f"Is '{inspection_finding}' covered?",
            inspection_finding=inspection_finding,
            claimability=analysis.get('claimability'),
            claim_reason=analysis.get('reasoning'),
            warranty_section=analysis.get('warranty_section'),
            ai_analysis=json.dumps(analysis)
        )
        
        db.session.add(warranty_query)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'query_id': warranty_query.id,
            'analysis': analysis
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error checking warranty claim: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/warranty-ask/<report_id>/<warranty_id>', methods=['POST'])
def ask_warranty_question(report_id, warranty_id):
    """
    Ask a warranty Q&A question in conversational context
    
    Expected JSON:
    {
        "question": "Is the roof damage covered by my warranty?"
    }
    
    Returns:
    {
        "answer": "...",
        "query_id": "..."
    }
    """
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400
        
        question = data['question'].strip()
        
        # Get report and warranty
        report = InspectionReport.query.get(report_id)
        warranty = WarrantyDocument.query.get(warranty_id)
        
        if not (report and warranty):
            return jsonify({'error': 'Report or warranty not found'}), 404
        
        # Create warranty Q&A system
        from warranty_utils import WarrantyQASystem
        coverage_rules = json.loads(warranty.coverage_rules)
        qa_system = WarrantyQASystem(
            report.extracted_text,
            coverage_rules,
            warranty.builder_name,
            warranty.warranty_type
        )
        
        # Get answer
        answer = qa_system.answer_warranty_question(question)
        
        # Store in database
        warranty_query = WarrantyQuery(
            report_id=report_id,
            warranty_id=warranty_id,
            customer_question=question,
            inspection_finding="conversational",
            claimability="INQUIRY",
            claim_reason=answer,
            ai_analysis=answer
        )
        
        db.session.add(warranty_query)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'query_id': warranty_query.id,
            'answer': answer
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error answering warranty question: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/warranty-queries/<report_id>', methods=['GET'])
def get_warranty_queries(report_id):
    """Get all warranty claim checks and questions for a report"""
    try:
        queries = WarrantyQuery.query.filter_by(report_id=report_id).all()
        
        return jsonify({
            'total_queries': len(queries),
            'queries': [
                {
                    'id': q.id,
                    'question': q.customer_question,
                    'claimability': q.claimability,
                    'reasoning': q.claim_reason,
                    'warranty_section': q.warranty_section,
                    'created_at': q.created_at.isoformat()
                }
                for q in queries
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/report-warranties/<report_id>', methods=['GET'])
def get_report_warranties(report_id):
    """Get all warranties linked to a report"""
    try:
        report = InspectionReport.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        warranties = db.session.query(WarrantyDocument).join(
            ReportWarranty
        ).filter(ReportWarranty.report_id == report_id).all()
        
        return jsonify({
            'report_id': report_id,
            'total_warranties': len(warranties),
            'warranties': [
                {
                    'id': w.id,
                    'builder_name': w.builder_name,
                    'warranty_type': w.warranty_type,
                    'jurisdiction': w.jurisdiction,
                    'created_at': w.created_at.isoformat()
                }
                for w in warranties
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
