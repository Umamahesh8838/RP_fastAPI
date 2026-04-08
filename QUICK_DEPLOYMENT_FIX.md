# Azure Deployment - Quick Fix Reference

## ❌ Error Fixed
```
/opt/Kudu/Scripts/starter.sh: line 2: exec: startup.sh: not found
```

---

## ✅ 3 Solutions Provided

### 1️⃣ **FASTEST & SIMPLEST** (Recommended Now)
Set startup command in Azure Portal:

**Configuration → General settings → Startup command:**
```
python azure_startup.py
```

Then redeploy.

---

### 2️⃣ **MOST RELIABLE** (Use Docker)
Enable **Docker Container** deployment in Azure Portal:

**App Service → Deployment center → Docker Container**
- Source: GitHub
- Repository: Your repo
- Tag: latest

Azure will auto-detect Dockerfile and deploy automatically.

---

### 3️⃣ **MOST AUTOMATED** (Use GitHub Actions)
1. Add GitHub Actions secrets:
   - `AZURE_CLIENT_ID`
   - `AZURE_TENANT_ID`
   - `AZURE_SUBSCRIPTION_ID`

2. Push to main branch → auto-deploys via GitHub Actions

---

## 🚀 **Immediate Next Steps**

### Option A: Use Python Startup (Do This First)
1. Go to Azure Portal
2. **App Service → Configuration → General settings**
3. Set **Startup command** to: `python azure_startup.py`
4. Hit Save
5. Back in terminal:
   ```bash
   git push origin main
   ```
6. Monitor logs:
   ```bash
   az webapp log tail --resource-group <resource-group> --name resume-parser-api-hp-260406
   ```

### Option B: Use Docker (Most Reliable)
1. Go to Azure Portal
2. **App Service → Deployment center**
3. Select **Docker Container**
4. Select GitHub as source
5. Follow the wizard
6. Azure will deploy automatically

---

## ✅ What Was Fixed

| Issue | Solution |
|-------|----------|
| `startup.sh: not found` | Created Python startup script (`azure_startup.py`) |
| Bash script dependency | Provides alternative (no bash needed) |
| No diagnostics | Python script logs everything |
| Complex deployment | Docker option available |
| Manual steps | GitHub Actions automates it |

---

## 🧪 Test After Deployment

```bash
# View logs
az webapp log tail --resource-group <rg> --name resume-parser-api-hp-260406

# Test health
curl https://resume-parser-api-hp-260406.azurewebsites.net/health
```

**Expected success:**
```
✓ Settings loaded
✓ SQL Server ODBC drivers found
✓ Async engine created successfully
✓ Application started successfully!
Database connected
```

---

## 📁 New Files

1. **`Dockerfile`** - Docker container definition (ODBC pre-installed)
2. **`.github/workflows/deploy-azure.yml`** - GitHub Actions workflow
3. **`azure_startup.py`** - Python startup script
4. **`AZURE_DEPLOYMENT_FIXES.md`** - Full detailed guide
5. **`web.config`** - Updated IIS configuration

---

## ⚡ Quick Command

**One-liner to set Python startup:**
```bash
az webapp config set --resource-group <rg> --name resume-parser-api-hp-260406 --startup-file "python azure_startup.py"
```

Then:
```bash
git push origin main
```

---

## 🎯 Expected Result

**Before:**
```
Application Error
(No details, no logs)
```

**After:**
```json
GET /health

{
  "status": "ok",
  "components": {
    "database": {"status": "connected"}
  }
}
```

---

**Status: ✅ ALL FIXES COMMITTED AND PUSHED**

Changes are ready to deploy!
