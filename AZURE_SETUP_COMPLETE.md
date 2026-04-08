# Azure Deployment - Complete Setup Guide

## 🎯 Overview

Your FastAPI application has been fully configured for Azure SQL Server deployment. This guide covers all deployment steps and fixes for "Application Error" issues.

---

## ✅ Changes Made for Azure

### 1. **config.py** - Environment Variable Priority
```python
# Before: Hardcoded values
db_password: str = "Qwerty@123"

# After: Environment variables with fallback
db_password: str = os.getenv("DB_PASSWORD", "")
```

**Benefits:**
- Secrets are not stored in code
- Environment-specific configuration
- Azure Key Vault compatible

### 2. **database.py** - Startup Diagnostics
```python
# New: Comprehensive startup logging
log_startup_info()  # Logs all DB config
if settings.db_driver == "mssql":
    import pyodbc
    drivers = pyodbc.drivers()  # Check ODBC drivers
```

**Benefits:**
- Detects missing ODBC driver immediately
- Clear error messages during startup
- Easier troubleshooting

### 3. **main.py** - Production-Ready Logging
```python
# Enhanced logging to stdout (required for Azure)
logging.StreamHandler(sys.stdout)

# Comprehensive startup test
async with AsyncSessionLocal() as db:
    await db.execute(text("SELECT 1"))
```

**Benefits:**
- Logs visible in Azure Application Insights
- Database connectivity tested at startup
- Graceful error messages

### 4. **requirements.txt** - Clean Dependencies
```diff
- aiomysql>=0.2.0
- pymysql>=1.1.0
- aioodbc>=0.5.0
+ pyodbc>=5.0.1
```

### 5. **startup.sh** (NEW) - Automated Setup
```bash
#!/bin/bash
# Installs ODBC Driver 18
# Verifies dependencies
# Tests database connection
```

---

## 🚀 Deployment Steps

### Step 1: Set Environment Variables in Azure Portal

Navigate to: **App Service → Configuration → Application settings**

Add these settings:

| Key | Value | Required |
|-----|-------|----------|
| `DB_DRIVER` | `mssql` | ✅ Yes |
| `DB_HOST` | `artisetsql.database.windows.net` | ✅ Yes |
| `DB_PORT` | `1433` | ✅ Yes |
| `DB_USER` | `artiset` | ✅ Yes |
| `DB_PASSWORD` | `Qwerty@123` | ✅ Yes |
| `DB_NAME` | `campus5` | ✅ Yes |
| `APP_ENV` | `production` | ✅ Yes |
| `OPENROUTER_API_KEY` | Your API key | ✅ Yes |

**Example in Portal:**
```
KEY: DB_DRIVER
VALUE: mssql

KEY: DB_HOST
VALUE: artisetsql.database.windows.net
```

### Step 2: Configure Startup Command

Navigate to: **App Service → Configuration → General settings**

Set **Startup command** to:
```
/home/site/wwwroot/startup.sh
```

This ensures ODBC driver is installed on deployment.

### Step 3: Deploy Code to Azure

**Option A: Using Git**
```bash
# Add Azure remote
az webapp deployment source config-zip \
  --resource-group <resource-group> \
  --name <app-name> \
  --src app.zip
```

**Option B: Using Git Push (if configured)**
```bash
git push azure main
```

**Option C: Using Azure CLI**
```bash
# Build and deploy
az webapp up --name <app-name> --resource-group <resource-group> --sku B1
```

### Step 4: Verify Deployment

**Check Application Logs:**
```bash
az webapp log tail --resource-group <resource-group> --name <app-name>
```

**Expected Success Logs:**
```
✓ Settings loaded from environment
✓ pyodbc version 4.0.39 detected
✓ SQL Server ODBC drivers found
✓ Async engine created successfully
✓ Application started successfully!
✓ Database connection verified!
```

**Test Health Endpoint:**
```bash
curl https://<your-app>.azurewebsites.net/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "components": {
    "database": {
      "status": "connected",
      "response_time_ms": 150,
      "host": "artisetsql.database.windows.net",
      "name": "campus5"
    }
  }
}
```

---

## 🔒 Security Configuration

### Option 1: Azure Key Vault (Recommended)
```python
# In config.py
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://<vault-name>.vault.azure.net/", credential=credential)

db_password = client.get_secret("db-password").value
```

### Option 2: Managed Identity
- Enable in App Service → Identity → System assigned
- Grant access in Azure SQL → Managed identities

### Option 3: Environment Variables (Current)
- Stored in App Service Configuration
- Encrypted at rest in Azure

---

## 📊 Monitoring & Diagnostics

### View Live Logs
```bash
az webapp log tail --resource-group <rg> --name <app-name> --provider application
```

### SSH into Container
```bash
az webapp remote-connection create --resource-group <rg> --name <app-name>
```

Then from SSH terminal:
```bash
# Check ODBC drivers
python3 -c "import pyodbc; print(pyodbc.drivers())"

# Check database connection
python3 -c "from database import engine; print('Engine: OK')"

# Check environment variables
env | grep DB_
```

### Application Insights
1. Azure Portal → App Service → Application Insights
2. Filter by Error or Warning
3. Review exception details

---

## 🐛 Common Issues & Quick Fixes

### Issue: "Application Error"
```bash
# Fix 1: Check startup.sh execution
az webapp log tail --resource-group <rg> --name <app-name>

# Look for: ODBC driver installation errors

# Fix 2: Update Startup command in Azure Portal
Startup command: /home/site/wwwroot/startup.sh

# Fix 3: Redeploy with fresh startup.sh
```

### Issue: "ODBC Driver not found"
```bash
# The startup.sh should handle this, but if not:
# SSH into app and run manually:
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

### Issue: "Login timeout"
```bash
# Check Azure SQL firewall:
# SQL Server → Networking → Firewall rules
# Add: 0.0.0.0 - 255.255.255.255 (allows all Azure services)
```

### Issue: Credentials not being read
```bash
# Verify environment variables are set:
curl https://<your-app>.azurewebsites.net/health

# Check the config summary includes your values
# or SSH in and run: python3 -c "from config import get_settings; print(get_settings().get_db_config_summary())"
```

---

## 📁 New/Modified Files Summary

```
RP_flask/
├── config.py              ✏️  MODIFIED - Environment variable support
├── database.py            ✏️  MODIFIED - Startup diagnostics
├── main.py                ✏️  MODIFIED - Production logging
├── requirements.txt       ✏️  MODIFIED - MSSQL/pyodbc optimized
├── startup.sh             ✨ NEW - ODBC driver installation
├── app.py                 ✨ NEW - Azure App Service wrapper
├── .deployment            ✨ NEW - Azure deployment configuration
├── web.config             ✨ NEW - IIS configuration (optional)
├── AZURE_DEPLOYMENT.md    ✨ NEW - Deployment guide
└── AZURE_TROUBLESHOOTING.md ✨ NEW - Troubleshooting guide
```

---

## 🧪 Local Testing Before Deployment

### 1. Test Locally
```bash
# Set environment variables
$env:DB_DRIVER="mssql"
$env:DB_HOST="artisetsql.database.windows.net"
$env:DB_PORT="1433"
$env:DB_USER="artiset"
$env:DB_PASSWORD="Qwerty@123"
$env:DB_NAME="campus5"

# Start app
uvicorn main:app --reload

# Test health endpoint
curl http://localhost:8000/health
```

### 2. Verify Settings
```bash
python -c "from config import get_settings; print(get_settings().get_db_config_summary())"
```

### 3. Test Database Connection
```bash
python -c "
import asyncio
from database import AsyncSessionLocal
from sqlalchemy import text

async def test():
    async with AsyncSessionLocal() as db:
        await db.execute(text('SELECT 1'))
        print('✓ Database connection successful')

asyncio.run(test())
"
```

---

## 🚀 Deployment Checklist

- [ ] All environment variables set in Azure Portal
- [ ] Startup command set to: `/home/site/wwwroot/startup.sh`
- [ ] Code deployed to Azure (startup.sh included)
- [ ] Application logs show no errors
- [ ] `/health` endpoint returns `status: ok`
- [ ] Database test endpoint works
- [ ] CORS allows your domain (if needed)
- [ ] Tested API endpoints
- [ ] Logs visible in Application Insights
- [ ] Database connections don't timeout

---

## 🎓 Understanding the Connection Flow

```
User Request
    ↓
FastAPI App (main.py)
    ↓
Settings (config.py) → Reads environment variables
    ↓
Database Engine (database.py) → Creates connection string
    ↓
pyodbc → Uses ODBC Driver 18
    ↓
ODBC Driver 18 → Connects to Azure SQL Server
    ↓
Azure SQL Server
    ↓
Response back to User
```

**Key Points:**
1. Settings read from environment (Azure Portal)
2. Connection string built with environment values
3. pyodbc used for MSSQL (not aioodbc)
4. ODBC Driver 18 installed via startup.sh
5. NullPool used for Azure-optimized connections

---

## 📞 Additional Resources

- [Azure SQL Database Connection](https://learn.microsoft.com/en-us/azure/azure-sql/database/connect-query-python)
- [ODBC Driver Installation](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server)
- [FastAPI on Azure](https://learn.microsoft.com/en-us/azure/app-service/quickstart-python)
- [Application Insights for Python](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opencensus-python)

---

## ✨ Summary

Your FastAPI application is now ready for production on Azure:

✅ **Database:** Azure SQL Server with proper MSSQL/pyodbc configuration  
✅ **Environment Variables:** Securely read from Azure Portal  
✅ **Startup:** Automated ODBC driver installation  
✅ **Logging:** Full diagnostics visible in Azure logs  
✅ **Monitoring:** Health check endpoint for status verification  
✅ **Error Handling:** Comprehensive error messages for troubleshooting  

**Next Step:** Deploy and monitor the `/health` endpoint!

