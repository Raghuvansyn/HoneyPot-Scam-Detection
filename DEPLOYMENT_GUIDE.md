# Complete Deployment Guide - Render.com (Free Tier)

## Why Render?
- Free tier available
- Easy deployment from GitHub
- Automatic HTTPS
- Supports Python/FastAPI
- No credit card required for free tier

---

## Part 1: Prepare Your Code for Deployment

### 1.1 Create a Procfile

Create a new file: `C:\Users\Lenovo\Desktop\one\Procfile` (no extension)

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 1.2 Update requirements.txt

Your requirements.txt should have:

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-dotenv==1.0.0
pydantic==2.9.2
langchain-groq==0.1.9
langchain-core==0.2.38
langgraph==0.2.16
scikit-learn>=1.3.0
requests==2.31.0
```

### 1.3 Create render.yaml (Optional but Recommended)

Create `C:\Users\Lenovo\Desktop\one\render.yaml`:

```yaml
services:
  - type: web
    name: scambait-ai
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GROQ_API_KEY
        sync: false
      - key: HACKATHON_API_KEY
        sync: false
      - key: GUVI_CALLBACK_URL
        value: https://hackathon.guvi.in/api/updateHoneyPotFinalResult
      - key: LLM_MODEL
        value: llama-3.1-8b-instant
```

### 1.4 Update .gitignore

Make sure `C:\Users\Lenovo\Desktop\one\.gitignore` contains:

```
# Environment variables
.env

# Database
*.db
*.sqlite
*.sqlite3

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

---

## Part 2: Push to GitHub

### 2.1 Initialize Git (if not already done)

Open terminal in `C:\Users\Lenovo\Desktop\one`:

```bash
git init
git add .
git commit -m "Initial commit - ScamBait AI honeypot"
```

### 2.2 Create GitHub Repository

1. Go to https://github.com
2. Click the "+" icon (top right) → "New repository"
3. Name it: `scambait-ai-honeypot`
4. Description: "AI-powered honeypot for scam detection and intelligence extraction"
5. Keep it **Private** (for now)
6. **DO NOT** initialize with README (you already have code)
7. Click "Create repository"

### 2.3 Push Your Code

GitHub will show you commands. Copy and run them:

```bash
git remote add origin https://github.com/YOUR_USERNAME/scambait-ai-honeypot.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

---

## Part 3: Deploy on Render.com

### 3.1 Create Render Account

1. Go to https://render.com
2. Click "Get Started" or "Sign Up"
3. Sign up with GitHub (recommended - makes deployment easier)
4. Authorize Render to access your repositories

### 3.2 Create New Web Service

1. From Render Dashboard, click "New +" → "Web Service"
2. Connect your GitHub account if not already connected
3. Find and select `scambait-ai-honeypot` repository
4. Click "Connect"

### 3.3 Configure Web Service

Fill in these settings:

**Basic Settings:**
- **Name:** `scambait-ai` (or any name you prefer)
- **Region:** Singapore (closest to India)
- **Branch:** `main`
- **Root Directory:** (leave blank)
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Instance Type:**
- Select **Free** tier

### 3.4 Add Environment Variables

Scroll down to "Environment Variables" section and add:

| Key | Value |
|-----|-------|
| `GROQ_API_KEY` | `your_actual_groq_api_key` |
| `HACKATHON_API_KEY` | `your_hackathon_api_key` |
| `GUVI_CALLBACK_URL` | `https://hackathon.guvi.in/api/updateHoneyPotFinalResult` |
| `LLM_MODEL` | `llama-3.1-8b-instant` |
| `PYTHON_VERSION` | `3.11.0` |

### 3.5 Deploy

1. Click "Create Web Service" button at the bottom
2. Render will start building and deploying your app
3. This takes 5-10 minutes for the first deployment

**What Happens:**
- Render clones your GitHub repo
- Installs all dependencies from requirements.txt
- Trains the ML model (happens automatically when detection.py loads)
- Starts the FastAPI server

### 3.6 Get Your Deployment URL

Once deployment succeeds (you'll see "Live" status), Render will give you a URL like:

```
https://scambait-ai.onrender.com
```

This is your **public endpoint URL**!

---

## Part 4: Test with Judge's Tool

Now that your app is deployed, use the judge's testing interface:

### 4.1 Prepare Test Data

**Your Endpoint URL:**
```
https://scambait-ai.onrender.com/honeypot
```

**Your API Key (from .env):**
```
your_hackathon_api_key
```

**Request Headers:**
```json
{
  "x-api-key": "your_hackathon_api_key",
  "Content-Type": "application/json"
}
```

**Request Body (Test Scam Message):**
```json
{
  "sessionId": "test-judge-001",
  "message": {
    "sender": "scammer",
    "text": "URGENT! Your bank account will be blocked today. Verify immediately by sending OTP to 9876543210.",
    "timestamp": "2026-02-03T10:00:00Z"
  },
  "conversationHistory": [],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

### 4.2 Using Judge's Testing Tool

1. **Enter Endpoint URL:**
   ```
   https://scambait-ai.onrender.com/honeypot
   ```

2. **Add API Key Header:**
   - In the header field, add:
   ```
   x-api-key: your_hackathon_api_key
   ```

3. **Click "Test Honeypot Endpoint"**

### 4.3 Expected Response

You should receive a response like:

```json
{
  "status": "success",
  "reply": "Oh no! What happened? I'm very worried! Let me get my pen... what was that number again?",
  "meta": {
    "agentState": "engaging",
    "sessionStatus": "active",
    "persona": "confused_customer",
    "turn": 2,
    "agentNotes": "Detection: SCAM (confidence: 0.95)"
  }
}
```

This means:
- ✅ Authentication working
- ✅ Scam detected (confidence 0.95)
- ✅ Persona engaged
- ✅ Response generated

---

## Part 5: Verify Everything Works

### 5.1 Check Logs on Render

1. Go to your Render dashboard
2. Click on your web service
3. Click "Logs" tab
4. You should see:
   - "✅ ML model trained (TF-IDF + SVM, 100 samples)"
   - Detection results
   - Persona generation logs

### 5.2 Test Multiple Scenarios

Test with different messages using the judge's tool:

**Test 1: Strong Scam**
```json
{
  "sessionId": "test-002",
  "message": {
    "sender": "scammer",
    "text": "Your KYC verification pending. Click here to update or account will be frozen.",
    "timestamp": "2026-02-03T10:01:00Z"
  }
}
```

**Test 2: Legitimate Message**
```json
{
  "sessionId": "test-003",
  "message": {
    "sender": "user",
    "text": "Hi, how are you doing today?",
    "timestamp": "2026-02-03T10:02:00Z"
  }
}
```

Expected: Should get polite dismissal, NOT scam engagement.

---

## Part 6: Troubleshooting Common Issues

### Issue 1: "Application failed to respond"

**Cause:** Server didn't start properly.

**Solution:**
1. Check Render logs for errors
2. Verify all environment variables are set
3. Make sure Procfile is correct
4. Check that port is using `$PORT` not hardcoded

### Issue 2: "401 Unauthorized"

**Cause:** API key mismatch.

**Solution:**
1. Verify the API key in Render environment variables matches what you're sending
2. Make sure header is `x-api-key` (lowercase)
3. Check for extra spaces in the API key value

### Issue 3: "500 Internal Server Error"

**Cause:** Runtime error in the code.

**Solution:**
1. Check Render logs for the full error traceback
2. Most common: Missing GROQ_API_KEY
3. Check database initialization (SQLite should auto-create)

### Issue 4: Slow Response (>10 seconds)

**Cause:** Free tier cold starts or LLM API delays.

**Solution:**
1. First request after inactivity will be slow (cold start)
2. Subsequent requests should be faster
3. If consistently slow, check Groq API status

### Issue 5: "Module not found" errors

**Cause:** Missing dependencies.

**Solution:**
1. Check requirements.txt has all packages
2. Verify build logs show all packages installed
3. Trigger manual redeploy from Render dashboard

---

## Part 7: Keep Your App Running (Important!)

**Free Tier Limitation:**
Render free tier apps sleep after 15 minutes of inactivity.

**Solutions:**

### Option A: Use Uptime Monitor (Recommended)
1. Sign up for free at https://uptimerobot.com
2. Create new monitor:
   - Type: HTTP(s)
   - URL: `https://scambait-ai.onrender.com/`
   - Interval: 5 minutes
3. This pings your app every 5 minutes, keeping it awake

### Option B: Accept Cold Starts
- First request after sleep takes 30-60 seconds
- Subsequent requests are fast
- Tell judges the first test might be slow

---

## Part 8: Submit to Judges

### What to Submit:

1. **Endpoint URL:**
   ```
   https://scambait-ai.onrender.com/honeypot
   ```

2. **API Key:**
   ```
   (provide your actual hackathon API key)
   ```

3. **GitHub Repository:**
   ```
   https://github.com/YOUR_USERNAME/scambait-ai-honeypot
   ```

4. **Documentation:**
   - Swagger UI: `https://scambait-ai.onrender.com/docs`
   - README.md (should be in your repo)
   - Project report (the comprehensive one we created)

5. **Demo Video (Optional but Recommended):**
   - Screen recording showing:
     - Swagger UI test
     - Detection working (scam vs legit)
     - Conversation flow
     - Intelligence extraction
     - Final callback

---

## Quick Command Reference

```bash
# Local testing
python run.py

# Git commands
git status
git add .
git commit -m "message"
git push

# View logs locally
# Check logs/ directory

# Test endpoint locally
curl -X POST http://localhost:8000/honeypot \
  -H "x-api-key: your_key" \
  -H "Content-Type: application/json" \
  -d @tests/test_scam.json
```

---

## Emergency Fixes

If something breaks after deployment:

1. Fix the code locally
2. Test locally to confirm it works
3. Commit and push:
   ```bash
   git add .
   git commit -m "Fix: description of what you fixed"
   git push
   ```
4. Render will automatically redeploy (takes 5-10 min)
5. Check logs to verify fix worked

---

## Final Checklist Before Submission

- [ ] App deployed and URL accessible
- [ ] Swagger UI works at `/docs`
- [ ] Test scam message gets engaged
- [ ] Test legit message gets dismissed
- [ ] API key authentication working
- [ ] Logs show ML model trained successfully
- [ ] GitHub repo is clean and well-organized
- [ ] README.md explains the project
- [ ] All sensitive data (API keys) are in environment variables, NOT in code
- [ ] Project report is ready
- [ ] You can explain every component to judges

---

You're ready to deploy! Start with Part 1 (verify locally), then move through each section step by step.
