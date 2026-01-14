# ⚡ QUICKSTART - Python Bridge Deployment

**Get your Python Bridge live in 10 minutes**

## 🎯 What You Have Ready

✅ **Complete Production Code** in this repo:
- `main.py` - FastAPI + SeleniumBase atomic executor (344 lines)
- `Dockerfile` - Production containerization
- `requirements.txt` - All dependencies
- `n8n-workflow-tummytales.json` - Ready-to-import n8n workflow

✅ **Week 1 Status:** COMPLETE - Production Ready 🚀

---

## 🚀 Deploy to Railway (Recommended - 5 minutes)

### Step 1: Deploy
1. Go to: https://railway.app/new
2. Click **"GitHub Repository"**
3. Login with GitHub (authorize Railway)
4. Select **"python-bridge-automation"** repo
5. Railway auto-detects Dockerfile and deploys
6. Wait 2-3 minutes for build

### Step 2: Get Your URL
1. Click on your deployed service
2. Go to **Settings → Generate Domain**
3. Copy your URL (e.g., `python-bridge-production.up.railway.app`)
4. Test health: `https://your-url.railway.app/health`

✅ **Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-14T14:00:00",
  "active_sessions": 0
}
```

---

## 🔗 Connect to n8n (5 minutes)

### Step 1: Import Workflow
1. Open your n8n instance
2. Click **"Import from File"**
3. Select `n8n-workflow-tummytales.json` from this repo
4. Workflow imports with 4 pre-configured nodes

### Step 2: Configure Environment Variables
In n8n Settings → Variables, add:
```
PYTHON_BRIDGE_URL=https://your-url.railway.app
GOOGLE_SHEET_ID=your_sheet_id
```

### Step 3: Test the Workflow
1. Click **"Execute Workflow"** (manual trigger)
2. Python Bridge executes test on TummyTales
3. Results automatically saved to Google Sheets

✅ **Expected Flow:**
```
Manual Trigger → Python Bridge API → Selenium Execution → 
Webhook Results → Google Sheets Save
```

---

## 🧪 Test Your Bridge (Manual)

### Health Check
```bash
curl https://your-url.railway.app/health
```

### Run Test (TummyTales Homepage)
```bash
curl -X POST https://your-url.railway.app/execute-test \
  -H "Content-Type: application/json" \
  -d '{
    "test_id": "TUMMY-001",
    "url": "https://tummytales.info",
    "browser": "chrome",
    "headless": true,
    "steps": [
      {"action": "open_url", "value": "https://tummytales.info"},
      {"action": "verify", "selector": "body", "value": "TummyTales", "timeout": 10},
      {"action": "screenshot"}
    ]
  }'
```

✅ **Expected Response:**
```json
{
  "test_id": "TUMMY-001",
  "status": "PASS",
  "duration": 8.5,
  "steps_executed": 3,
  "steps_passed": 3,
  "steps_failed": 0,
  "timestamp": "2026-01-14T14:00:00"
}
```

---

## 📋 Alternative: Deploy to Render.com

1. Go to: https://render.com/
2. Click **"New → Web Service"**
3. Connect GitHub → Select this repo
4. Render auto-detects Dockerfile
5. Click **"Create Web Service"**
6. Get URL from dashboard

---

## 🎓 Next Steps (Week 2)

### Day 2-3: Test with TummyTales (Thursday-Friday)
- [ ] Deploy complete (you are here ✅)
- [ ] Create 5 test cases for TummyTales site
- [ ] Run automated tests via n8n
- [ ] Verify Google Sheets integration

### Day 4-5: Stress Testing (Weekend)
- [ ] Run 10 parallel tests
- [ ] Check error handling and retry logic
- [ ] Review screenshot captures
- [ ] Monitor webhook callbacks

### Day 6-7: Production Ready (Monday-Tuesday)
- [ ] Document API endpoints
- [ ] Create test case library
- [ ] Set up monitoring/alerts
- [ ] Showcase to team/interviews

---

## 🆘 Troubleshooting

### "Browser not starting in Docker"
**Solution:** Headless mode is required in Docker. Ensure your test JSON has:
```json
"headless": true
```

### "Element not found"
**Solution:** Increase timeout in test step:
```json
{"action": "click", "selector": "button", "timeout": 20}
```

### "n8n can't reach local bridge"
**Solution:** Use Railway/Render URL, not `localhost`. Local bridge only works with Ngrok.

---

## 📚 Documentation Links

- **API Docs:** `https://your-url/docs` (FastAPI auto-generated)
- **Full README:** See main README.md in this repo
- **Deployment Guide:** See detailed deployment guide gist
- **n8n Workflow:** `n8n-workflow-tummytales.json` in this repo

---

## ✨ What Makes This Production-Ready

1. **Atomic Execution** - Each action is isolated with retry logic
2. **Error Handling** - 2x automatic retries on failures
3. **Screenshots** - Auto-capture on errors for debugging
4. **Webhooks** - Real-time results to n8n/Google Sheets
5. **Docker** - Consistent environment, easy deployment
6. **Health Checks** - Monitor uptime and active sessions
7. **Zero Syntax Errors** - Pre-written executor, JSON commands only

---

## 🎯 Success Criteria

✅ Deploy complete when:
- [ ] Health endpoint returns `{"status": "healthy"}`
- [ ] Test execution returns `"status": "PASS"`
- [ ] n8n workflow successfully imports
- [ ] Results appear in Google Sheets

**Timeline:** 10 minutes to deploy, 5 minutes to test = **15 minutes total**

**Status:** Week 1 COMPLETE - Ready for Production Testing 🚀
