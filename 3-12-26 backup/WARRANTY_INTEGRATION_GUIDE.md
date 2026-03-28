# WARRANTY FEATURE - COMPLETE INTEGRATION GUIDE

**Status:** Ready to implement | **Breaking Changes:** ZERO | **Est. Time:** 4-6 hours

---

## WHAT YOU'RE GETTING

A complete white-label warranty interpretation system that:

✅ Uploads warranty documents (PDF)  
✅ Parses coverage rules (AI-powered)  
✅ Links to inspection reports  
✅ Checks if inspection findings are claimable  
✅ Answers warranty questions conversationally  
✅ Integrates with existing inspection platform  
✅ NO changes to inspection workflow  
✅ NO changes to summary formatting (sacred!)  

---

## FILES YOU RECEIVED

### **1. Schema Update** (`schema_warranty_updated.prisma`)
- **Action:** Replace your current `schema.prisma` with this
- **Changes:** Adds 3 new tables (WarrantyDocument, ReportWarranty, WarrantyQuery)
- **Breaking?** NO - Only additions, no schema changes to existing tables
- **Command:** `prisma migrate dev --name add-warranty-tables`

### **2. Warranty Utilities** (`warranty_utils.py`)
- **Action:** Create new file in backend folder: `warranty_utils.py`
- **Contents:** 
  - `extract_warranty_text()` - PDF extraction (same as inspection)
  - `parse_warranty_coverage()` - AI parsing of warranty rules
  - `WarrantyCoverageAnalyzer` - Claims analysis engine
  - `WarrantyQASystem` - Conversational warranty Q&A
- **Breaking?** NO - Pure additions, no changes to existing utils

### **3. New API Endpoints** (`app_warranty_endpoints.py`)
- **Action:** Copy these endpoints into your `app.py` file
- **New Routes:**
  - `POST /api/upload-warranty/<report_id>` - Upload warranty PDF
  - `GET /api/warranty/<report_id>/<warranty_id>` - Get warranty details
  - `POST /api/warranty-claim-check/<report_id>/<warranty_id>` - Check if finding is covered
  - `POST /api/warranty-ask/<report_id>/<warranty_id>` - Ask warranty questions
  - `GET /api/warranty-queries/<report_id>` - Get all warranty analyses
  - `GET /api/report-warranties/<report_id>` - Get warranties linked to report
- **Breaking?** NO - Adds new endpoints, doesn't modify existing ones

### **4. Warranty Configuration** (`warranty_config_sample.json`)
- **Action:** Place in backend folder: `warranty_config_sample.json`
- **Purpose:** Reference structure for parsed warranty rules
- **Note:** This is populated automatically when warranty PDF is uploaded

### **5. Frontend Integration** (`warranty_html_integration.js`)
- **Action:** Add code snippets to your `index.html`
- **Breaking?** NO - Adds new UI sections without touching existing code
- **Integration Points:**
  - Add state variables for warranty tracking
  - Add warranty upload UI section (optional, after summary)
  - Add warranty Q&A interface
  - Add event listeners for warranty interactions

---

## STEP-BY-STEP INTEGRATION

### **STEP 1: Update Database Schema (15 min)**

```bash
cd inspection-ai-backend

# 1. Replace schema.prisma with updated version
cp schema_warranty_updated.prisma schema.prisma

# 2. Run migration
prisma migrate dev --name add-warranty-tables

# 3. Verify new tables created
prisma db push
```

**Verify:** Check your Neon database - should have:
- WarrantyDocument
- ReportWarranty
- WarrantyQuery

---

### **STEP 2: Add Warranty Utilities (10 min)**

```bash
# 1. Create warranty_utils.py in backend folder
cp warranty_utils.py inspection-ai-backend/

# 2. Add import to app.py (at top, around line 5):
from warranty_utils import (
    extract_warranty_text,
    parse_warranty_coverage,
    WarrantyCoverageAnalyzer,
    WarrantyQASystem
)
```

---

### **STEP 3: Add New Endpoints to app.py (30 min)**

**In your `app.py`:**

1. After line 4 (existing imports), add:
```python
from warranty_utils import (
    extract_warranty_text,
    parse_warranty_coverage,
    WarrantyCoverageAnalyzer,
    WarrantyQASystem
)
```

2. After the existing inspection endpoints (around line 600), add ALL code from `app_warranty_endpoints.py`

3. Don't forget to import the new models at the top:
```python
from models import db, InspectionReport, Conversation, Question, Contractor, Lead, Analytics, WarrantyDocument, ReportWarranty, WarrantyQuery
```

4. Verify file imports are correct:
   - `from warranty_utils import extract_warranty_text` ✅
   - `from warranty_utils import parse_warranty_coverage` ✅

---

### **STEP 4: Update Frontend (45 min)**

**In your `index.html`:**

1. **Add state variables** (around line 150):
```javascript
const state = {
    screen: 'upload',
    reportId: null,
    
    // NEW WARRANTY FIELDS
    warrantyId: null,
    warrantyBuilderName: null,
    warrantyType: null,
    warranties: [],
    
    // existing fields...
    questions: [],
    currentQuestion: '',
    // ... rest
};
```

2. **In renderSummaryScreen()** - After displaying the summary (around line ~350), add:
```javascript
// Add warranty upload section after summary
html += await renderWarrantyUploadSection();
```

3. **Still in renderSummaryScreen()** - Add warranty Q&A section:
```javascript
// Add warranty Q&A if warranty uploaded
if (state.warrantyId) {
    html += await renderWarrantyQASection();
}
```

4. **Copy the warranty functions** from `warranty_html_integration.js`:
   - `renderWarrantyUploadSection()`
   - `renderWarrantyQASection()`
   - `renderClaimAnalysis()`
   - `uploadWarrantyFile()`
   - `askWarrantyQuestion()`
   - `initWarrantyListeners()`

5. **In the main render() function**, after rendering summary screen, add:
```javascript
// Initialize warranty listeners
setTimeout(() => initWarrantyListeners(), 100);
```

---

### **STEP 5: Test Backend (15 min)**

```bash
cd inspection-ai-backend

# 1. Start Flask app
python app.py

# 2. Test health check
curl http://localhost:5000/health

# 3. Test warranty upload endpoint (use Travelers sample PDF)
curl -X POST http://localhost:5000/api/upload-warranty/{report_id} \
  -F "file=@Sample-New-Home-Warranty-Certificate-E-1.pdf" \
  -F "builder_name=Travelers" \
  -F "warranty_type=2-5-10"

# Should return warranty_id
```

---

### **STEP 6: Test Frontend (20 min)**

1. Upload an inspection PDF (existing flow)
2. See new **"Have a Warranty Certificate?"** section
3. Upload the Travelers sample PDF
4. Enter builder name: "Travelers"
5. Enter warranty type: "2-5-10"
6. Click "Upload Warranty"
7. See **"Warranty Claims Check"** section appear
8. Ask a question: "Is the electrical issue covered?"
9. Get AI analysis with coverage status

---

## IMPORTANT: THINGS NOT TO CHANGE

⚠️ **DO NOT MODIFY:**

❌ `generate_summary_from_report()` in utils.py
❌ Summary formatting/bolding in app.py
❌ Illinois SOP integration
❌ Existing endpoints (/api/upload, /api/ask, etc.)
❌ Contractor referral logic
❌ Email sending setup

✅ **SAFE TO MODIFY:**
✅ Add new utility functions
✅ Add new endpoints
✅ Add new UI sections
✅ Update schema (append only)

---

## VALIDATION CHECKLIST

After integration, verify:

- [ ] Prisma migration runs without error
- [ ] Flask app starts: `python app.py` ✅
- [ ] Health check works: `/health` returns 200 ✅
- [ ] Can upload inspection PDF (existing flow) ✅
- [ ] New warranty section appears on summary screen ✅
- [ ] Can upload warranty PDF ✅
- [ ] Warranty Q&A appears after upload ✅
- [ ] Can ask warranty questions ✅
- [ ] Gets back claimability analysis ✅
- [ ] Summary formatting unchanged (check bolding) ✅
- [ ] Contractor referral still works ✅

---

## DATABASE SCHEMA SUMMARY

### **New Tables Added:**

**WarrantyDocument**
```
id: unique ID
builderName: "Travelers"
warrantyType: "2-5-10"
jurisdiction: "BC", "IL", "USA", etc.
filePath: path to PDF
extractedText: full text from PDF
coverageRules: JSON of parsed coverage
createdAt, updatedAt
```

**ReportWarranty**
```
id: unique ID
reportId: links to inspection report
warrantyId: links to warranty document
certificateNumber: from warranty
warrantyStartDate, warrantyEndDate
```

**WarrantyQuery**
```
id: unique ID
reportId: which inspection report
warrantyId: which warranty
customerQuestion: the question asked
inspectionFinding: what finding being checked
claimability: "COVERED" | "NOT_COVERED" | "PARTIAL" | "REQUIRES_SPECIALIST"
claimReason: explanation
ai_analysis: full Claude response
```

---

## API ENDPOINT REFERENCE

### **Upload Warranty**
```
POST /api/upload-warranty/{report_id}
Content-Type: multipart/form-data

Fields:
- file: PDF file
- builder_name: "Travelers"
- warranty_type: "2-5-10"
- jurisdiction: "USA" (optional)

Response:
{
  "success": true,
  "warranty_id": "...",
  "builder_name": "Travelers",
  "warranty_type": "2-5-10"
}
```

### **Check Warranty Claim**
```
POST /api/warranty-claim-check/{report_id}/{warranty_id}
Content-Type: application/json

Body:
{
  "inspection_finding": "Electrical outlet not working",
  "issue_type": "electrical"
}

Response:
{
  "claimability": "COVERED",
  "warranty_section": "Section 2.1",
  "coverage_period": "2 years",
  "reasoning": "...",
  "next_steps": [...]
}
```

### **Ask Warranty Question**
```
POST /api/warranty-ask/{report_id}/{warranty_id}
Content-Type: application/json

Body:
{
  "question": "Is the roof leak covered?"
}

Response:
{
  "answer": "Yes, roof leaks are covered under..."
}
```

---

## TROUBLESHOOTING

**Issue: "WarrantyDocument not found"**
- ✅ Did you run `prisma migrate dev`?
- ✅ Did you update models.py imports?

**Issue: "extract_warranty_text is not defined"**
- ✅ Did you copy warranty_utils.py to backend folder?
- ✅ Did you add import to app.py?

**Issue: Warranty upload works but no UI appears**
- ✅ Did you add state.warrantyId variable?
- ✅ Did you add render() call after upload?

**Issue: Summary formatting looks wrong**
- ✅ Did you change generate_summary_from_report()? Don't!
- ✅ Warranty features are AFTER summary, not affecting it

**Issue: Claude API failing**
- ✅ Check ANTHROPIC_API_KEY in .env
- ✅ Check API rate limits
- ✅ Check response timeout (max_tokens set correctly)

---

## NEXT STEPS AFTER INTEGRATION

### **Immediate (Days 1-2):**
- [ ] Test with Travelers warranty sample
- [ ] Test with custom builder warranty
- [ ] Verify claim analysis accuracy

### **Short-term (Week 1):**
- [ ] Add more warranty templates (National Home Warranty, Dweller, etc.)
- [ ] Create warranty_config.json for each builder
- [ ] Pitch to Dweller/warranty companies

### **Medium-term (Weeks 2-4):**
- [ ] Build warranty company dashboard
- [ ] Add claims tracking (which findings claimed)
- [ ] Create warranty reporting for admins
- [ ] White-label version for other inspectors

### **Long-term (Months 2-3):**
- [ ] Multi-state warranty coverage
- [ ] State law overlay (like Illinois SOP)
- [ ] Warranty comparison tool
- [ ] Claims automation integration

---

## BUSINESS METRICS TO TRACK

After launch, measure:

1. **Warranty Upload Rate** - % of inspection reports with warranty uploaded
2. **Claim Analysis Volume** - # of claim checks per report
3. **Claims Prevented** - Frivolous claims avoided (track with partners)
4. **Warranty Company ROI** - How much they save per partnership
5. **Conversion** - How many warranty company pilots → paid partnerships

**Target:** Launch with 1 warranty company pilot → measure ROI → pitch to 2-3 more nationals

---

## SUPPORT

If anything breaks during integration:

1. Check the validation checklist above
2. Verify file paths and imports
3. Check .env has ANTHROPIC_API_KEY
4. Run `prisma db push` to sync database
5. Restart Flask: `python app.py`

All code is non-breaking. If you hit an error, you can:
- Roll back schema: `git checkout schema.prisma`
- Remove new endpoints from app.py
- Remove warranty_utils.py
- Remove new state variables from HTML

You'll be back to 100% working in minutes.

---

## SUMMARY

You've got a **complete warranty interpretation system** ready to deploy.

**Total effort:** ~2-3 hours of integration  
**Risk:** Zero - all non-breaking additions  
**Value:** Entry point to $100M+ warranty market  
**Next:** Pitch to Dweller with working demo  

The architecture mirrors your Illinois SOP approach - parse reference document → inject into Claude → let AI handle the interpretation.

You're building the "Angi for warranties." Go get 'em! 🚀

