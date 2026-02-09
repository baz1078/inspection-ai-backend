# Inspection Report Platform - Customer Data Fix

## What Was Broken
Your quote request flow was losing customer data:
1. Customer info entered on upload page
2. Customer clicks "Request Quote" 
3. **PROBLEM:** Customer data wasn't saved/passed to backend
4. Admin sees blank customer info and poorly formatted data

---

## What Was Fixed

### **Frontend (index.html)**

#### ✅ State Management
- Added customer data fields to application state:
  ```javascript
  customerName: '',
  customerEmail: '',
  customerPhone: ''
  ```
- Data persists in state across screens (upload → chat → quote)

#### ✅ Data Capture During Upload
- Customer info from form is now captured and stored in state:
  ```javascript
  state.customerName = document.getElementById('customerName').value;
  state.customerEmail = document.getElementById('customerEmail').value;
  state.customerPhone = document.getElementById('customerPhone').value;
  ```

#### ✅ Quote Confirmation Modal
- **NEW:** When customer clicks "Request Quote", a confirmation modal appears
- Shows:
  - ✓ Customer name
  - ✓ Customer email
  - ✓ Customer phone
  - ✓ Property address
  - ✓ Issue type
- Customer can review before sending
- Better UX: prevents accidental submissions, confirms data accuracy

#### ✅ Complete Data Passing
- Quote request now includes all customer data:
  ```javascript
  body: JSON.stringify({
      report_id: state.reportId,
      question_id: questionId,
      contractor_id: contractorId,
      customer_name: state.customerName,      // NOW INCLUDED
      customer_email: state.customerEmail,    // NOW INCLUDED
      customer_phone: state.customerPhone     // NOW INCLUDED
  })
  ```

---

### **Backend (app.py)**

#### ✅ Updated `/api/referral-request` Endpoint
- Now accepts customer data from frontend
- Stores customer info in Lead record:
  ```python
  lead = Lead(
      report_id=data['report_id'],
      question_id=data['question_id'],
      contractor_id=data['contractor_id'],
      customer_name=data.get('customer_name', ''),      # NEW
      customer_email=data.get('customer_email', ''),    # NEW
      customer_phone=data.get('customer_phone', ''),    # NEW
      status='pending'
  )
  ```
- Also updates the report record with latest customer info

#### ✅ Updated `/api/admin/leads` Endpoint
- Now returns complete customer information:
  ```python
  {
      'id': l.id,
      'customer_name': l.customer_name or 'N/A',
      'customer_email': l.customer_email or 'N/A',
      'customer_phone': l.customer_phone or 'N/A',
      'contractor_name': l.contractor.name,
      'issue_type': l.question.issue_type,
      'status': l.status,
      'created_at': l.created_at.isoformat()
  }
  ```

---

### **Admin Dashboard (admin.html)**

#### ✅ Updated Leads Table Header
- Changed from: `Contractor | Issue | Status | Date | Actions`
- Changed to: `Customer Name | Contact Info | Contractor | Issue | Status | Actions`
- Better grid layout to accommodate all columns

#### ✅ Updated Display Logic
- Shows customer name prominently
- Shows contact info (email preferred, falls back to phone)
- Issue type highlighted with yellow badge
- All in organized columns

---

## Installation Steps

### **Step 1: Check Your Database Model**
You need to verify that your `Lead` model has customer fields. 

Check your `models.py` file and look for the `Lead` class. It should have:

```python
class Lead(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = db.Column(db.String(36), db.ForeignKey('inspection_report.id'), nullable=False)
    question_id = db.Column(db.String(36), db.ForeignKey('question.id'), nullable=False)
    contractor_id = db.Column(db.String(36), db.ForeignKey('contractor.id'), nullable=False)
    
    # THESE FIELDS MUST EXIST:
    customer_name = db.Column(db.String(255), nullable=True)      # ADD IF MISSING
    customer_email = db.Column(db.String(255), nullable=True)     # ADD IF MISSING
    customer_phone = db.Column(db.String(20), nullable=True)      # ADD IF MISSING
    
    status = db.Column(db.String(20), default='pending')
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    report = db.relationship('InspectionReport', backref='leads')
    question = db.relationship('Question', backref='leads')
    contractor = db.relationship('Contractor', backref='leads')
```

**If these three fields are missing**, add them:
```python
customer_name = db.Column(db.String(255), nullable=True)
customer_email = db.Column(db.String(255), nullable=True)
customer_phone = db.Column(db.String(20), nullable=True)
```

### **Step 2: Migrate Database (if needed)**
If you had to add the fields, you need to create a migration OR delete your old database:

**Option A (Quick - for development):**
```bash
# Delete the old database
rm inspection_reports.db

# Restart your app - it will recreate the database with new schema
python app.py
```

**Option B (Production - use Alembic):**
```bash
# Create migration
alembic revision --autogenerate -m "Add customer fields to Lead"

# Apply migration
alembic upgrade head
```

### **Step 3: Replace Files**
1. **index.html** - Customer portal with confirmation modal
2. **app.py** - Updated API endpoints
3. **admin.html** - Updated leads display

Copy these to your project directory.

### **Step 4: Test**

**Test Locally:**
```bash
# Terminal 1: Start backend
python app.py

# Terminal 2: Open customer portal
# Go to http://localhost:5000 (or wherever you serve index.html)

# Step 1: Fill in customer info
# Step 2: Upload PDF
# Step 3: Ask a question
# Step 4: Click "Request Quote"
# Step 5: Confirmation modal appears - CHECK IT SHOWS YOUR INFO
# Step 6: Confirm and send
# Step 7: Check admin panel - leads page should show customer data
```

**What You Should See:**

**Frontend:**
- Upload page shows customer form (name, email, phone)
- After upload, customer can ask questions
- When contractor suggestion appears, "Request Quote" button is available
- Clicking "Request Quote" shows confirmation modal with all customer data
- After confirming, you get success message

**Admin Dashboard:**
- Go to "Leads" tab
- You should see columns: Customer Name | Contact Info | Contractor | Issue | Status | Actions
- Each lead shows the customer who requested it
- Shows their email or phone number

---

## Data Flow (Complete)

```
CUSTOMER SIDE:
1. User enters: Name, Email, Phone
2. User uploads PDF
3. DATA SAVED → state.customerName/Email/Phone
4. User asks question
5. System suggests contractors
6. User clicks "Request Quote"
   ↓
   CONFIRMATION MODAL APPEARS
   Shows all customer data + address + issue type
   User can review or go back
   ↓
   User clicks "Send Quote Request"
   ↓
7. DATA SENT TO BACKEND:
   {
     report_id,
     question_id,
     contractor_id,
     customer_name,    ← INCLUDED NOW
     customer_email,   ← INCLUDED NOW
     customer_phone    ← INCLUDED NOW
   }

BACKEND:
1. Receives quote request with all data
2. Creates Lead record with customer fields
3. Updates Report with customer info
4. Saves to database

ADMIN SIDE:
1. Admin goes to "Leads" tab
2. API returns: customer_name, customer_email, customer_phone
3. Admin sees formatted table with:
   - Customer Name | Contact Info | Contractor | Issue | Status | Actions
4. Can click "Update" to change lead status
```

---

## Potential Issues & Solutions

### **Issue 1: "ModuleNotFoundError" or "AttributeError" on backend**
**Cause:** Database schema mismatch - Lead model missing customer fields

**Solution:**
1. Check `models.py` - do you have the three customer fields?
2. If not, add them
3. Delete `inspection_reports.db` 
4. Restart Flask (`python app.py`)

### **Issue 2: Admin dashboard shows "No leads yet" after quote request**
**Cause:** Either Lead wasn't created or there's an error

**Solution:**
1. Check terminal for error messages when you click "Send Quote Request"
2. Look at your browser console (F12 → Console tab)
3. Check database - run: `sqlite3 inspection_reports.db "SELECT * FROM lead;"`
4. If empty, check for errors in Flask output

### **Issue 3: Confirmation modal doesn't show**
**Cause:** Old index.html still being served, or JavaScript error

**Solution:**
1. Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
2. Clear browser cache
3. Check browser console for JavaScript errors
4. Verify you're serving the new index.html

### **Issue 4: Customer fields appear blank in admin**
**Cause:** Quote request wasn't sent with customer data (old code still running)

**Solution:**
1. Verify you replaced `app.py` with the new version
2. Restart Flask: Stop the process and run `python app.py` again
3. Test again - fill out customer form completely before uploading

---

## Key Changes Summary

| Component | What Changed | Why |
|-----------|--------------|-----|
| **index.html** | Added state fields for customer data | Persist data across screens |
| **index.html** | Added confirmation modal | Let customers review before sending |
| **index.html** | Pass customer data in quote request | Backend receives complete info |
| **app.py** | Accept customer fields in `/api/referral-request` | Store in database |
| **app.py** | Return customer fields from `/api/admin/leads` | Admin can see who requested quote |
| **admin.html** | Updated table header with customer columns | Display customer info |
| **admin.html** | Updated loadLeads function | Format customer data in display |
| **models.py** | *May need to add* customer fields to Lead | Store customer info |

---

## Testing Checklist

- [ ] Customer info form appears on upload page
- [ ] Customer data persists after PDF upload
- [ ] Question/answer chat works
- [ ] Contractor suggestions appear
- [ ] "Request Quote" button is clickable
- [ ] Confirmation modal shows all customer data
- [ ] Can review and confirm quote request
- [ ] Success message appears
- [ ] Admin dashboard loads
- [ ] Leads tab shows customer names
- [ ] Customer email/phone visible in leads table
- [ ] Update button works for changing status
- [ ] Database contains lead records with customer data

---

## Next Steps

1. **Verify models.py** - Check for customer fields
2. **Add fields if needed** - And migrate database
3. **Deploy updated files** - index.html, app.py, admin.html
4. **Test end-to-end** - Follow testing checklist above
5. **Monitor** - Watch admin dashboard as leads come in

---

## Questions?

If something breaks:
1. Check terminal output from Flask for error messages
2. Check browser console (F12 → Console)
3. Check database: `sqlite3 inspection_reports.db ".tables"` 
4. Verify all three files were updated: index.html, app.py, admin.html

You've got this! 🚀
