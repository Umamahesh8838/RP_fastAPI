# OpenRouter API Setup Guide

## ❌ Error: "User not found" (401)

This means the `OPENROUTER_API_KEY` environment variable is not set or is invalid.

---

## ✅ Solution: Set Environment Variables on Azure

### Step 1: Get Your OpenRouter API Key

1. Go to [https://openrouter.ai/keys](https://openrouter.ai/keys)
2. Sign in or create a free account
3. Create a new API key
4. Copy the key (format: `sk-or-v1-xxxxx...`)

### Step 2: Set Environment Variables on Azure Portal

**For Azure Web App:**

1. Go to [Azure Portal](https://portal.azure.com)
2. Select your App Service: **resume-parser-api-hp-260406**
3. In left sidebar, click **Configuration**
4. Click **New application setting** button
5. Add the following settings:

| Name | Value |
|------|-------|
| `OPENROUTER_API_KEY` | `sk-or-v1-xxxxx...` (your API key) |
| `OPENROUTER_MODEL` | `openai/gpt-3.5-turbo` |
| `DB_PASSWORD` | `Qwerty@123` |
| `DB_USER` | `artiset` |
| `DB_HOST` | `artisetsql.database.windows.net` |
| `DB_NAME` | `campus5` |

6. Click **Save** button
7. **IMPORTANT**: Click **Continue** when prompted to restart the app

### Step 3: Verify Deployment

After saving, Azure will restart your app. Check logs:

```bash
az webapp log tail --resource-group resume-parser-rg --name resume-parser-api-hp-260406
```

Look for:
```
✓ OpenRouter API key configured
✓ Model: openai/gpt-3.5-turbo
```

If you see this, the key is set correctly! ✅

---

## 🧪 Test the API Locally First

Before deploying, test with environment variables set:

### On Windows (PowerShell):

```powershell
# Set environment variables
$env:OPENROUTER_API_KEY = "sk-or-v1-xxxxx..."
$env:OPENROUTER_MODEL = "openai/gpt-3.5-turbo"
$env:DB_PASSWORD = "Qwerty@123"
$env:DB_USER = "artiset"
$env:DB_HOST = "artisetsql.database.windows.net"
$env:DB_NAME = "campus5"

# Run locally
python -m uvicorn main:app --reload
```

### On Linux/Mac:

```bash
# Set environment variables
export OPENROUTER_API_KEY="sk-or-v1-xxxxx..."
export OPENROUTER_MODEL="openai/gpt-3.5-turbo"
export DB_PASSWORD="Qwerty@123"
export DB_USER="artiset"
export DB_HOST="artisetsql.database.windows.net"
export DB_NAME="campus5"

# Run locally
python -m uvicorn main:app --reload
```

---

## 📝 Add to .env File for Local Development

Create `.env` file in project root:

```bash
# OpenRouter LLM
OPENROUTER_API_KEY=sk-or-v1-xxxxx...
OPENROUTER_MODEL=openai/gpt-3.5-turbo

# Database
DB_DRIVER=mssql
DB_HOST=artisetsql.database.windows.net
DB_PORT=1433
DB_USER=artiset
DB_PASSWORD=Qwerty@123
DB_NAME=campus5

# App
APP_ENV=development
APP_PORT=8000
```

---

## 🔄 Test Resume Parsing

### Local Test:

```bash
curl -X POST http://localhost:8000/resume/parse-preview \
  -F "file=@boya_mohan_resume.pdf"
```

### Azure Test:

```bash
curl -X POST https://resume-parser-api-hp-260406.azurewebsites.net/resume/parse-preview \
  -F "file=@boya_mohan_resume.pdf"
```

### Expected Success Response:

```json
{
  "success": true,
  "resume_hash": "abc123def456...",
  "already_exists": false,
  "parsed_data": {
    "first_name": "Boya",
    "last_name": "Mohan",
    "email": "boya@example.com",
    ...
  }
}
```

### Error Response (Missing API Key):

```json
{
  "success": false,
  "error": "OpenRouter API key is not configured! Set OPENROUTER_API_KEY environment variable.",
  "detail": null
}
```

---

## 🔑 Available LLM Models

You can use different models by changing `OPENROUTER_MODEL`:

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| `openai/gpt-3.5-turbo` | ⚡ Fast | 💰 Cheap | General tasks |
| `openai/gpt-4o-mini` | ⚡ Fast | 💰 Cheap | Better accuracy |
| `openai/gpt-4` | 🐢 Slow | 💰💰💰 Expensive | Complex parsing |
| `anthropic/claude-3-haiku` | ⚡ Fast | 💰 Cheap | Lightweight |
| `meta-llama/llama-2-70b-chat` | ⚡ Fast | 💰 Free | Open source |

---

## ❓ Troubleshooting

### Error: "User not found" (401)

**Cause**: API key is invalid, expired, or not set

**Fix**:
1. Go to [https://openrouter.ai/keys](https://openrouter.ai/keys)
2. Generate a new API key
3. Update on Azure: Configuration → Application settings
4. Restart the app

### Error: "Rate limit exceeded"

**Cause**: Too many API calls in short time

**Fix**:
- Wait a few minutes before retrying
- Consider upgrading your OpenRouter plan

### Error: "Model not found"

**Cause**: Model name is incorrect or not available

**Fix**:
- Check available models at [https://openrouter.ai/docs/models](https://openrouter.ai/docs/models)
- Update `OPENROUTER_MODEL` in Azure settings

### Error: "Timeout"

**Cause**: API is slow or network is unstable

**Fix**:
- Increase timeout in `llm_service.py` (currently 120s)
- Check internet connection
- Try a faster model

---

## 📚 References

- OpenRouter Docs: [https://openrouter.ai/docs](https://openrouter.ai/docs)
- Get API Key: [https://openrouter.ai/keys](https://openrouter.ai/keys)
- Azure Configuration: [Azure App Service Environment Variables](https://learn.microsoft.com/en-us/azure/app-service/configure-common)

---

## ✅ Checklist

- [ ] Created OpenRouter account
- [ ] Generated API key
- [ ] Set OPENROUTER_API_KEY in Azure Application settings
- [ ] Test locally with .env file
- [ ] Deployed to Azure
- [ ] Verified logs show "API key configured"
- [ ] Test /resume/parse-preview endpoint
- [ ] Confirm response is successful

**Once all boxes are checked, your LLM integration is complete!** ✨
