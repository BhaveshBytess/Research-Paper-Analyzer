# Streamlit Cloud Deployment Instructions

## 🚀 Deployment Status
✅ **Live URL**: https://research-paper-analyzer-n55umbhgiafzbkntyzvq9d.streamlit.app

---

## 📝 Steps to Deploy (Already Completed)

### 1. Push to GitHub
```bash
git add -A
git commit -m "Prepare for Streamlit deployment"
git push origin main
```

### 2. Configure Streamlit App
- Log in to [Streamlit Cloud](https://share.streamlit.io)
- Click "New app"
- Select repository: `BhaveshBytess/research-paper-analyzer`
- Set main file path: `research-paper-analyzer/app/app.py`
- Click "Deploy"

### 3. Set Secrets (CRITICAL)
In Streamlit Cloud dashboard → App Settings → Secrets:

```toml
OPENROUTER_API_KEY = "your_api_key_here"
```

**Without this, the app will show a 401 error when trying to process papers.**

---

## 🔧 Configuration Files

### `.streamlit/config.toml`
```toml
[server]
headless = true
port = 8501

[theme]
primaryColor = "#6366f1"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f3f4f6"
textColor = "#1f2937"
```

### `requirements.txt` (Key Dependencies)
- `streamlit==1.42.0` - Web UI framework
- `python-dotenv==1.0.0` - Environment variable loading (CRITICAL for deployment)
- `openai==1.12.0` - OpenRouter client
- `pymupdf==1.24.14` - PDF parsing
- `pydantic==1.10.12` - Data validation

---

## 🐛 Common Deployment Issues & Fixes

### Issue 1: `ModuleNotFoundError: No module named 'dotenv'`
**Symptom**: App crashes on startup with import error.

**Fix**: Ensure `python-dotenv==1.0.0` is in `requirements.txt`

**Status**: ✅ Fixed (added to requirements.txt)

---

### Issue 2: `401 - User not found` when processing paper
**Symptom**: Paper processing fails with API authentication error.

**Root Cause**: `OPENROUTER_API_KEY` not set in Streamlit secrets.

**Fix**:
1. Go to Streamlit Cloud dashboard
2. Click on your app → Settings → Secrets
3. Add:
   ```toml
   OPENROUTER_API_KEY = "sk-or-v1-..."
   ```
4. Save and restart app

**Code Changes Made**:
```python
# research-paper-analyzer/app/app.py (lines 133-148)
if llm_choice.startswith("openrouter::"):
    # Try Streamlit secrets first, then environment
    openrouter_api_key = None
    try:
        openrouter_api_key = st.secrets.get("OPENROUTER_API_KEY")
    except:
        pass
    if not openrouter_api_key:
        openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
    
    if not openrouter_api_key:
        st.error("⚠️ OPENROUTER_API_KEY not found...")
        st.info("Add your API key in Streamlit Cloud dashboard under 'Secrets'.")
        st.stop()
```

**Status**: ✅ Fixed (graceful error handling added)

---

### Issue 3: App path not found
**Symptom**: Streamlit Cloud says "File not found" during deployment.

**Fix**: Ensure main file path is set to `research-paper-analyzer/app/app.py` (NOT `app.py` or `app/app.py`)

**Status**: ✅ Verified

---

## 📊 Monitoring & Logs

### View Logs
- Streamlit Cloud dashboard → Your app → Manage app → Logs
- Shows real-time Python stdout/stderr
- Useful for debugging API errors, import issues

### Restart App
- Streamlit Cloud dashboard → Your app → Reboot
- Needed after changing secrets or configuration

---

## 🔐 Security Best Practices

### ✅ DO:
- Store API keys in Streamlit secrets (never in code)
- Use `.gitignore` to exclude `.env` files
- Use environment variables for sensitive config

### ❌ DON'T:
- Commit API keys to Git
- Hardcode credentials in source code
- Share secrets publicly

---

## 🧪 Testing Deployment

### 1. Test UI Loads
- Navigate to: https://research-paper-analyzer-n55umbhgiafzbkntyzvq9d.streamlit.app
- Should see "Research Paper Analyzer" title
- Should see file uploader and model selector

### 2. Test Paper Processing
- Upload a sample PDF (e.g., from `samples/` folder)
- Select model (DeepSeek recommended)
- Click "Run Extraction"
- Should complete without errors in 15-30 seconds

### 3. Test Error Handling
- Remove API key from secrets → Should show helpful error message
- Upload non-PDF file → Should show validation error

---

## 📈 Usage Limits

### OpenRouter Free Tier
- **DeepSeek**: ~10-20 papers per day
- **Gemma**: ~10-20 papers per day
- Rate limit: ~60 requests per minute

### Streamlit Cloud Free Tier
- **Resources**: 1 GB RAM, 1 CPU core
- **Uptime**: App sleeps after 1 hour of inactivity
- **Storage**: Ephemeral (no persistent disk)

**Implication**: Batch evaluation should be run locally, not on Streamlit Cloud (will hit resource limits).

---

## 🔄 Redeploying After Code Changes

### Automatic Redeployment
Streamlit Cloud automatically redeploys on push to `main` branch:

```bash
# Make changes locally
git add -A
git commit -m "Update extraction logic"
git push origin main

# Wait 2-3 minutes → App automatically rebuilds
```

### Manual Redeployment
- Streamlit Cloud dashboard → Your app → Reboot

---

## 📝 Resume-Ready Deployment Info

**For your resume or portfolio**:

```
Research Paper Analyzer
Deployed: Streamlit Cloud
URL: [live link]
Tech Stack: Python, Streamlit, OpenRouter API, PyMuPDF
Metrics: 100% JSON validity, 80% evidence precision across 10 papers
Features: Real-time PDF extraction, multi-model support, evidence grounding
```

---

## 🎯 Next Steps (Optional)

### 1. Custom Domain
- Streamlit Cloud supports custom domains (paid tier)
- Or use free subdomain: `research-paper-analyzer.streamlit.app`

### 2. Analytics
- Add Google Analytics to track usage
- Monitor API usage via OpenRouter dashboard

### 3. API Wrapper
- Deploy FastAPI backend separately (Heroku/Railway/Render)
- Streamlit frontend → API backend → Paper extraction

### 4. Upgrade to Paid Tier
- More resources (4 GB RAM, 2 CPU cores)
- Always-on (no sleep)
- Custom secrets management

---

## 📧 Support

**Issues?** Contact:
- GitHub: [@BhaveshBytess](https://github.com/BhaveshBytess)
- Email: 10bhavesh7.11@gmail.com

**Streamlit Docs**: https://docs.streamlit.io/streamlit-community-cloud

---

**Last Updated**: November 3, 2025  
**Deployment Version**: 1.0.0  
**Status**: ✅ Production-Ready

