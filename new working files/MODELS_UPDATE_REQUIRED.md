# Models.py Update Required - CRITICAL CHECK

## What You Need To Do

Your `models.py` file likely has a `Lead` model that's missing three fields. You need to add them.

---

## STEP 1: Open models.py and Find the Lead Class

Look for something like:

```python
class Lead(db.Model):
    __tablename__ = 'lead'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = db.Column(db.String(36), db.ForeignKey('inspection_report.id'), nullable=False)
    question_id = db.Column(db.String(36), db.ForeignKey('question.id'), nullable=False)
    contractor_id = db.Column(db.String(36), db.ForeignKey('contractor.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

## STEP 2: Check - Are These Fields Present?

Search for these three lines in your Lead class:

```python
customer_name = db.Column(db.String(255), nullable=True)
customer_email = db.Column(db.String(255), nullable=True)
customer_phone = db.Column(db.String(20), nullable=True)
```

### ✅ If YES - They're there
You're good! Just use the updated app.py and index.html.

### ❌ If NO - They're missing
You need to add them. Follow instructions below.

---

## STEP 3: Add Missing Fields

In your Lead class, add these three lines after the `contractor_id` line:

```python
class Lead(db.Model):
    __tablename__ = 'lead'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = db.Column(db.String(36), db.ForeignKey('inspection_report.id'), nullable=False)
    question_id = db.Column(db.String(36), db.ForeignKey('question.id'), nullable=False)
    contractor_id = db.Column(db.String(36), db.ForeignKey('contractor.id'), nullable=False)
    
    # ADD THESE THREE LINES:
    customer_name = db.Column(db.String(255), nullable=True)
    customer_email = db.Column(db.String(255), nullable=True)
    customer_phone = db.Column(db.String(20), nullable=True)
    
    status = db.Column(db.String(20), default='pending')
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    report = db.relationship('InspectionReport', backref='leads')
    question = db.relationship('Question', backref='leads')
    contractor = db.relationship('Contractor', backref='leads')
```

---

## STEP 4: Update Your Database

After adding the fields, you must update your database. Choose ONE of these:

### Option A: Fresh Start (Development - Easiest)
```bash
# Stop Flask (Ctrl+C)

# Delete old database
rm inspection_reports.db

# Start Flask again
python app.py

# Flask will recreate the database with new schema
```

**Pros:** Simple, guaranteed to work
**Cons:** Loses all existing data

### Option B: Migration (Production - Preserves Data)

Using Flask-Migrate (Alembic under the hood):

```bash
# Initialize migration if not done yet (one-time)
flask db init

# Create migration
flask db migrate -m "Add customer fields to Lead model"

# Apply migration
flask db upgrade
```

**Pros:** Keeps existing data
**Cons:** More complex, requires Flask-Migrate installed

### Option C: Manual SQL (Advanced)
If you use raw SQLite:

```bash
sqlite3 inspection_reports.db

# Then run:
ALTER TABLE lead ADD COLUMN customer_name VARCHAR(255);
ALTER TABLE lead ADD COLUMN customer_email VARCHAR(255);
ALTER TABLE lead ADD COLUMN customer_phone VARCHAR(20);
```

---

## STEP 5: Verify It Worked

After updating the database, check that the table has the new columns:

```bash
sqlite3 inspection_reports.db ".schema lead"
```

You should see:
```
CREATE TABLE lead (
    id VARCHAR(36) NOT NULL,
    report_id VARCHAR(36) NOT NULL,
    question_id VARCHAR(36) NOT NULL,
    contractor_id VARCHAR(36) NOT NULL,
    customer_name VARCHAR(255),          ← SHOULD BE HERE
    customer_email VARCHAR(255),         ← SHOULD BE HERE
    customer_phone VARCHAR(20),          ← SHOULD BE HERE
    status VARCHAR(20) DEFAULT 'pending',
    notes TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    PRIMARY KEY (id),
    ...
)
```

---

## STEP 6: Test

1. Restart Flask: `python app.py`
2. Go to http://localhost:5000
3. Fill in customer name, email, phone
4. Upload a PDF
5. Ask a question
6. Request a quote
7. Check admin panel → Leads tab
8. You should see customer info displayed

---

## Troubleshooting

### Error: "column customer_name not found"
**Problem:** Database wasn't updated after adding fields
**Solution:** 
1. Delete `inspection_reports.db`
2. Restart Flask
3. Try again

### Migration fails with "ERROR: column already exists"
**Problem:** Columns were already added (you may have done this before)
**Solution:** 
The model and database are already in sync. Just use the new app.py and index.html.

### Admin dashboard still shows blank customer info
**Problem:** 
1. Old app.py still running
2. Or database fields not properly created
**Solution:**
1. Stop Flask (Ctrl+C)
2. Verify database has the columns (see Step 5)
3. Start Flask again
4. Test the entire flow

---

## Complete Lead Model Example

Here's what your complete Lead class should look like:

```python
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Lead(db.Model):
    __tablename__ = 'lead'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = db.Column(db.String(36), db.ForeignKey('inspection_report.id'), nullable=False)
    question_id = db.Column(db.String(36), db.ForeignKey('question.id'), nullable=False)
    contractor_id = db.Column(db.String(36), db.ForeignKey('contractor.id'), nullable=False)
    
    # Customer information fields
    customer_name = db.Column(db.String(255), nullable=True)
    customer_email = db.Column(db.String(255), nullable=True)
    customer_phone = db.Column(db.String(20), nullable=True)
    
    # Lead status and notes
    status = db.Column(db.String(20), default='pending')  # pending, contacted, converted, lost
    notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    report = db.relationship('InspectionReport', backref='leads')
    question = db.relationship('Question', backref='leads')
    contractor = db.relationship('Contractor', backref='leads')
    
    def __repr__(self):
        return f'<Lead {self.id} - {self.customer_name}>'
```

---

## Summary

1. **Find** the Lead class in models.py
2. **Check** if it has customer_name, customer_email, customer_phone fields
3. **If missing:** Add the three fields
4. **Update** your database (delete old DB or run migration)
5. **Restart** Flask
6. **Deploy** the new app.py and index.html
7. **Test** the complete flow

That's it! 🚀
