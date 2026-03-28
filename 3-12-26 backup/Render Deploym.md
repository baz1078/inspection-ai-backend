# Assure Inspections AI - Render Deployment Guide

**Your app will be live at: `https://assure-inspections-ai.onrender.com` (example)**

---

## **STEP 1: Prepare Your Code for Render**

### Update your files:

1. **Copy frontend files to outputs:**
   ```bash
   cp frontend_new.html frontend.html
   cp admin_dashboard.html admin.html
   ```

2. **Create `.gitignore` in your backend folder:**
   ```
   __pycache__/
   *.pyc
   .env
   uploads/
   *.db
   ```

3. **Create `runtime.txt`:**
   ```
   python-3.12.0
   ```

4. **Create `Procfile`:**
   ```
   web: gunicorn app:app
   ```

---

## **STEP 2: Set Up Render Account**

1. Go to **render.com**
2. Click **"Get Started"**
3. Sign up with GitHub, Google, or Email
4. Verify your email

---

## **STEP 3: Create Render PostgreSQL Database**

1. In Render dashboard, click **"New +"**
2. Select **"PostgreSQL"**
3. Name: `assure-inspections-db`
4. Region: `US East`
5. Click **"Create Database"**
6. **Copy your connection string** (you'll need it)

**Important:** Use the "Internal Database URL" for the app connection.

---

## **STEP 4: Deploy Backend to Render**

1. In Render dashboard, click **"New +"**
2. Select **"Web Service"**
3. **Connect GitHub:**
   - Click "Connect account"
   - Authorize Render to access your GitHub
   - Select your repository
   - Click "Connect"

4. **Configure the service:**
   - Name: `assure-inspections-api`
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Region: `US East`

5. **Add Environment Variables** (click "Advanced"):
   ```
   ANTHROPIC_API_KEY=sk-ant-xxxxx (your API key)
   DATABASE_URL=postgresql://... (from Step 3)
   FLASK_ENV=production
   ```

6. Click **"Create Web Service"**

**Wait 5-10 minutes for deployment...**

Once deployed, you'll get a URL like: `https://assure-inspections-api.onrender.com`

---

## **STEP 5: Update Frontend to Point to Live API**

In your `frontend.html`, change:
```javascript
const API_URL = 'http://localhost:5000';
```

To:
```javascript
const API_URL = 'https://assure-inspections-api.onrender.com';
```

In your `admin.html`, do the same.

---

## **STEP 6: Deploy Frontend (Static Files)**

You have two options:

### **Option A: Render Static Site (Easiest)**

1. In Render dashboard, click **"New +"**
2. Select **"Static Site"**
3. Name: `assure-inspections-web`
4. Build Command: (leave empty)
5. Publish Directory: `.` (or folder with your HTML files)
6. Click **"Create Static Site"**

Then commit your updated `frontend.html` and `admin.html` to GitHub.

**Your frontend URL:** `https://assure-inspections-web.onrender.com`

### **Option B: Serve Frontend from Backend (Advanced)**

Create a `static` folder in your backend:
```
inspection-ai-backend/
├── app.py
├── models.py
├── utils.py
└── static/
    ├── frontend.html
    └── admin.html
```

Then in `app.py`, add at the top:
```python
from flask import send_from_directory

@app.route('/')
def index():
    return send_from_directory('static', 'frontend.html')

@app.route('/admin')
def admin():
    return send_from_directory('static', 'admin.html')
```

This way everything is on one domain.

---

## **STEP 7: Update Database in Render

After backend is deployed, run migrations:

```bash
# In Render deployment, add to your Build Command:
pip install -r requirements.txt && flask db upgrade
```

Or manually run via Render shell:
```bash
python
>>> from app import db, app
>>> with app.app_context():
...     db.create_all()
```

---

## **STEP 8: Test Live Deployment**

1. **Test API health:**
   ```bash
   curl https://assure-inspections-api.onrender.com/health
   ```

   You should get:
   ```json
   {"status":"healthy","service":"Assure Inspections AI"}
   ```

2. **Visit your frontend:**
   - Main app: `https://assure-inspections-web.onrender.com`
   - Admin: `https://assure-inspections-web.onrender.com/admin`

3. **Upload a test report and ask a question**

---

## **STEP 9: Add Your Logo & Files**

1. **Upload logo to backend:**
   - Add `assure-logo.jpg` to your static folder

2. **Or use a public URL:**
   ```html
   <img src="https://your-domain.com/assure-logo.jpg" alt="Assure" />
   ```

---

## **STEP 10: Set Up Custom Domain (Optional)**

1. In Render dashboard, go to your service
2. Click **"Settings"**
3. Scroll to **"Custom Domains"**
4. Add your domain: `inspections.yourcompany.com`
5. Follow DNS instructions

---

## **Troubleshooting**

### **API not connecting to database:**
- Check `DATABASE_URL` is correct in Render environment variables
- Ensure PostgreSQL instance is created and running
- Check Neon dashboard that database exists

### **Frontend can't reach API:**
- Make sure `API_URL` in frontend.html uses HTTPS
- Check CORS is enabled in app.py
- Verify backend is running: `curl https://assure-inspections-api.onrender.com/health`

### **Static files not loading:**
- Make sure files are in the right directory
- Check file paths are correct
- Use absolute URLs for images/assets

### **Database migrations not running:**
- Add migration commands to Render Build Command
- Or run manually via Render shell
- Check logs in Render dashboard

---

## **Next Steps After Deployment**

1. **Test with real realtors** - Share the URL
2. **Add contractors** - Use admin dashboard to add your trusted contractors
3. **Monitor analytics** - Track questions and leads
4. **Optimize referrals** - Add more contractors in key specialties
5. **Scale to other states** - Duplicate setup with different contractor databases

---

## **Monthly Costs (Rough Estimate)**

- **Render Web Service:** $12-50/month (depends on traffic)
- **PostgreSQL Database:** $15/month (Neon free tier or $15 paid)
- **Anthropic API:** $0.01-1/month (depends on usage)
- **Total:** ~$30-50/month for moderate traffic

---

## **Keeping It Running**

- Render auto-deploys when you push to GitHub
- Database backups handled by Neon
- Logs available in Render dashboard
- Free SSL certificates (HTTPS included)

---

**YOU'RE LIVE! 🎉**

Share your URL with realtors. Start collecting data. Optimize referrals.

Questions? Check Render docs: https://render.com/docs