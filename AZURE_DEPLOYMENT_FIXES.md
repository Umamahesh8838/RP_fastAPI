# Azure Deployment - Fixing Startup Errors

## ❌ Error Encountered

```
/opt/Kudu/Scripts/starter.sh: line 2: exec: startup.sh: not found
Deployment Failed
```

## ✅ Solutions

We've created multiple solutions to fix the startup error. Choose the approach that best fits your needs:

---

## 🚀 **RECOMMENDED: GitHub Actions + Docker Deployment**

This is the most reliable and fastest deployment method.

### Step 1: Set Up Azure Credentials for GitHub Actions

You need to create a Service Principal for GitHub Actions to authenticate with Azure.

**Option A: Using Azure CLI (Recommended)**
```bash
# Login to Azure
az login

# Create Service Principal
az ad sp create-for-rbac --name "resume-parser-github" --role contributor --scopes /subscriptions/{SUBSCRIPTION_ID} --json
```

This will output:
```json
{
  "clientId": "YOUR_CLIENT_ID",
  "clientSecret": "YOUR_CLIENT_SECRET",
  "subscriptionId": "YOUR_SUBSCRIPTION_ID",
  "tenantId": "YOUR_TENANT_ID"
}
```

**Option B: Azure Portal**
1. Go to **Azure Portal → App Service → Details**
2. Note your **Subscription ID**
3. Go to **Microsoft Entra ID → App registrations** → Create new app registration
4. Name it "resume-parser-github"
5. Create a Client Secret (note the value)

### Step 2: Add Secrets to GitHub Repository

1. Go to **GitHub repo → Settings → Secrets and variables → Actions**
2. Add these secrets:
   - `AZURE_CLIENT_ID`: Your clientId
   - `AZURE_TENANT_ID`: Your tenantId
   - `AZURE_SUBSCRIPTION_ID`: Your subscriptionId

### Step 3: Commit and Push to GitHub

```bash
git add Dockerfile
git add .github/workflows/deploy-azure.yml
git add web.config
git add .deployment
git add azure_startup.py
git commit -m "Add Azure deployment configuration"
git push origin main
```

The GitHub Actions workflow will automatically:
- Test Python code
- Test app import
- Build Docker image (if using Docker deployment)
- Deploy to Azure
- Test health endpoint

---

## 🐳 **ALTERNATIVE 1: Docker Deployment (Most Reliable)**

Docker deployment gives you complete control over the environment, including ODBC driver installation.

### Step 1: Enable Docker Deployment in Azure Portal

1. Go to **App Service → Deployment center**
2. Select **Docker Container** as Source
3. Choose **GitHub** as Repository
4. Select your repository and main branch
5. Azure will auto-detect the Dockerfile and deploy

### Step 2: Push Changes to GitHub

```bash
git add Dockerfile
git push origin main
```

**Benefits:**
- ✅ ODBC driver installed automatically
- ✅ Consistent environment
- ✅ All dependencies bundled
- ✅ No shell script execution issues

---

## 🔧 **ALTERNATIVE 2: Direct Azure CLI Deployment (Fastest)**

Deploy directly without GitHub Actions or Docker.

### Step 1: Set Startup Command in Azure

```bash
az webapp config set \
  --resource-group <resource-group> \
  --name resume-parser-api-hp-260406 \
  --startup-file "python -m uvicorn main:app --host 0.0.0.0 --port 8000"
```

### Step 2: Deploy Code

```bash
# Push code to Azure
git push azure main

# Or manually deploy
az webapp deployment source config-zip \
  --resource-group <resource-group> \
  --name resume-parser-api-hp-260406 \
  --src app.zip
```

### Step 3: Check Logs

```bash
az webapp log tail --resource-group <resource-group> --name resume-parser-api-hp-260406
```

---

## 🔌 **ALTERNATIVE 3: Python Startup Script**

Use the new `azure_startup.py` script as the startup command.

### Step 1: Set Startup Command in Azure Portal

**Configuration → General settings → Startup command:**
```
python azure_startup.py
```

Or via CLI:
```bash
az webapp config set \
  --resource-group <resource-group> \
  --name resume-parser-api-hp-260406 \
  --startup-file "python azure_startup.py"
```

### Step 2: Deploy

```bash
git push origin main
```

**Benefits:**
- ✅ No bash shell dependency
- ✅ Python-native startup
- ✅ Clear startup diagnostics
- ✅ Automatic dependency installation

---

## ⚙️ **Environment Variables Required**

Regardless of deployment method, ensure these are set in **Azure Portal → Configuration → Application settings:**

```
DB_DRIVER=mssql
DB_HOST=artisetsql.database.windows.net
DB_PORT=1433
DB_USER=artiset
DB_PASSWORD=Qwerty@123
DB_NAME=campus5
APP_ENV=production
OPENROUTER_API_KEY=your-key-here
```

---

## ✔️ **Deployment Checklist**

- [ ] GitHub Actions secrets added (if using GitHub Actions)
- [ ] Startup command set in Azure Portal (if not using Docker)
- [ ] Environment variables set in Azure Portal
- [ ] Files committed and pushed to GitHub:
  - [ ] `Dockerfile`
  - [ ] `.github/workflows/deploy-azure.yml`
  - [ ] `azure_startup.py`
  - [ ] `web.config`
  - [ ] `.deployment`
- [ ] Deployment triggered and completed
- [ ] Logs show no errors
- [ ] Health check returns `status: ok`

---

## 🧪 **Testing After Deployment**

### View Logs
```bash
# Option 1: Azure CLI
az webapp log tail --resource-group <rg> --name resume-parser-api-hp-260406

# Option 2: Azure Portal
# App Service → Log stream
```

### Expected Success Logs
```
DATABASE CONFIGURATION
  driver          : mssql
  host            : artisetsql.database.windows.net
✓ Settings loaded
✓ pyodbc version X.X.X detected
✓ SQL Server ODBC drivers found
✓ Async engine created successfully
✓ Application started successfully!
✓ Database connection verified!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Test Health Endpoint
```bash
curl https://resume-parser-api-hp-260406.azurewebsites.net/health
```

Expected response:
```json
{
  "status": "ok",
  "components": {
    "database": {
      "status": "connected"
    }
  }
}
```

---

## 🐛 **Troubleshooting Specific Errors**

### Error: "startup.sh: not found"
**Cause:** startup.sh not included in deployment package

**Solution:** Use one of the recommended approaches above (GitHub Actions, Docker, or Python startup script)

### Error: "ODBC Driver 18 not found"
**Cause:** ODBC driver not installed on the app server

**Solutions:**
1. **Use Docker** (recommended) - Dockerfile installs it automatically
2. **Use GitHub Actions** with Container deployment
3. **Manually connect via SSH** and run:
   ```bash
   curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
   apt-get update
   ACCEPT_EULA=Y apt-get install -y msodbcsql18
   ```

### Error: "Connection timeout"
**Cause:** Azure SQL Server firewall blocking connection

**Solution:**
1. Go to **Azure SQL Server → Networking → Firewall rules**
2. Add Web App:
   - Start IP: 0.0.0.0
   - End IP: 255.255.255.255
   (Or specify specific Web App IP if known)

### Error: "Python module not found"
**Cause:** Dependencies not installed

**Solution:**
1. Verify `requirements.txt` exists and is complete
2. Use Docker deployment (installs on build)
3. Or manually install: `az webapp ssh --resource-group <rg> --name <name>` then `pip install -r requirements.txt`

---

## 📋 **Files Added/Modified for Azure Deployment**

### New Files:
- `Dockerfile` - Docker container definition
- `.github/workflows/deploy-azure.yml` - GitHub Actions workflow
- `azure_startup.py` - Python startup script
- `AZURE_DEPLOYMENT_FIXES.md` - This file

### Modified Files:
- `web.config` - Updated for proper ASGI routing
- `.deployment` - Removed startup.sh dependency

---

## 🎯 **Recommended Deployment Path**

**Best for production:**
1. Use **GitHub Actions + Docker** deployment
2. Set environment variables in Azure Portal
3. Push to main branch → auto-deploy
4. Monitor logs and health endpoint

**Quick deployment:**
1. Set startup command: `python azure_startup.py`
2. Set environment variables
3. Push code to Azure
4. Test health endpoint

---

## 📞 **Getting Help**

If deployment still fails:

1. **Check logs:** `az webapp log tail --resource-group <rg> --name <name>`
2. **SSH into app:** `az webapp ssh --resource-group <rg> --name <name>`
3. **Check environment variables:** `env | grep DB_`
4. **Test module imports:** `python -c "from config import get_settings; print('OK')"`
5. **Test database connection:** `python -c "from database import engine; print('OK')"`

---

## ✨ **Summary**

The startup.sh error is now fixed by:

1. **GitHub Actions workflow** - Automated, reliable, recommended
2. **Docker deployment** - Complete environment control
3. **Python startup script** - No bash dependency
4. **Azure CLI direct** - Simple command-line deployment

Choose the method that works best for your workflow!
