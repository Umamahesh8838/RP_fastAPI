# Azure Deployment Troubleshooting Guide

## Common Issues and Solutions

### ❌ Issue 1: "Application Error" on Azure Web App

**Symptoms:**
- Azure Web App shows generic "Application Error"
- No detailed error message visible

**Root Causes:**
1. ODBC Driver 18 not installed on Azure
2. Database connection string misconfigured
3. Environment variables not set
4. Missing dependency (pyodbc)

**Solutions:**

#### Solution 1a: Verify ODBC Driver Installation
```bash
# SSH into Azure App Service and run:
docker exec -it <container-id> bash
odbcinst -j
pyodbc.drivers()
```

#### Solution 1b: Add startup.sh to Azure
1. In Azure App Service → Configuration → General settings
2. Set "Startup Command" to:
   ```
   /home/site/wwwroot/startup.sh
   ```
3. Ensure `startup.sh` is in your repository root

#### Solution 1c: Check Environment Variables
1. Azure Portal → App Service → Configuration
2. Verify these are set:
   ```
   DB_DRIVER=mssql
   DB_HOST=artisetsql.database.windows.net
   DB_PORT=1433
   DB_USER=artiset
   DB_PASSWORD=Qwerty@123
   DB_NAME=campus5
   APP_ENV=production
   ```

**Verification Command:**
```bash
curl https://<your-app>.azurewebsites.net/health
```

---

### ❌ Issue 2: "ODBC Driver 18 for SQL Server not found"

**Symptoms:**
```
pyodbc.Error: ('IM002', '[IM002] [Microsoft][ODBC Driver Manager] Data source name not found and no default driver specified (SQLDriverConnect)')
```

**Solution:**
1. Add `startup.sh` to your repository
2. Configure Azure startup command (see Issue 1b)
3. Or create a `Dockerfile` with ODBC installation

**Dockerfile Example:**
```dockerfile
FROM python:3.11-slim

# Install ODBC driver
RUN apt-get update && \
    apt-get install -y curl gnupg2 && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    echo "deb [signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/ubuntu/20.04/prod focal main" > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### ❌ Issue 3: "Login timeout expired" or "Connection refused"

**Symptoms:**
```
sqlalchemy.exc.OperationalError: (pyodbc.OperationalError) ('HYT00', '[HYT00] [Microsoft][ODBC Driver 18 for SQL Server] Login timeout expired')
```

**Root Causes:**
1. Azure SQL Server firewall blocking Web App
2. Incorrect database credentials
3. Database server not accessible

**Solutions:**

#### Solution 3a: Allow Azure Web App IP
1. Azure Portal → Azure SQL Server → Networking → Firewall rules
2. Add Web App's outbound IP:
   ```
   Start IP: 0.0.0.0
   End IP: 255.255.255.255
   (This allows all Azure services, most restrictive: add specific Web App IP)
   ```

#### Solution 3b: Verify Credentials
```powershell
# Test locally first
$env:DB_DRIVER="mssql"
$env:DB_HOST="artisetsql.database.windows.net"
$env:DB_PORT="1433"
$env:DB_USER="artiset"
$env:DB_PASSWORD="Qwerty@123"
$env:DB_NAME="campus5"

python -c "from config import get_settings; print(get_settings().database_url)"
```

#### Solution 3c: Test Connection String
```python
import pyodbc

connection_string = (
    "mssql+pyodbc://artiset:Qwerty%40123@artisetsql.database.windows.net:1433/campus5"
    "?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no"
)

try:
    conn = pyodbc.connect(connection_string)
    print("✓ Connection successful!")
    conn.close()
except Exception as e:
    print(f"✗ Connection failed: {e}")
```

---

### ❌ Issue 4: "Certificate verification failed" or SSL Errors

**Symptoms:**
```
pyodbc.Error: SSL: CERTIFICATE_VERIFY_FAILED
```

**Root Causes:**
1. Missing SSL certificate on server
2. TrustServerCertificate setting incorrect

**Solution:**
Our config already has the correct setting:
```python
TrustServerCertificate=no  # Enforces proper certificate verification
Encrypt=yes                 # Encrypts connection
```

If you still get errors:
1. Ensure Azure SQL Server has valid SSL certificate
2. Update to latest ODBC driver: `apt-get install -y msodbcsql18`
3. Verify system has CA certificates: `apt-get install -y ca-certificates`

---

### ❌ Issue 5: "Application logs show pyodbc import error"

**Symptoms:**
```
ModuleNotFoundError: No module named 'pyodbc'
```

**Solution:**
1. Reinstall requirements: `pip install --upgrade -r requirements.txt`
2. In Azure, ensure startup.sh runs: `pip install -r requirements.txt`
3. Check Python environment: `pip list | grep pyodbc`

**Verification:**
```bash
pip install pyodbc
python -c "import pyodbc; print(pyodbc.version)"
```

---

### ❌ Issue 6: "Health check endpoint returns database disconnected"

**Symptoms:**
```json
{
  "status": "degraded",
  "components": {
    "database": {
      "status": "disconnected",
      "error": "..."
    }
  }
}
```

**Debugging Steps:**

1. **Check startup logs:**
   ```bash
   az webapp log tail --name <app-name> --resource-group <rg>
   ```

2. **Look for these logs:**
   - `✓ Settings loaded from environment`
   - `✓ Async engine created successfully`
   - `✓ SQL Server ODBC drivers found`

3. **If missing, check:**
   - Startup script execution
   - Environment variables set correctly
   - Python dependencies installed

4. **Manual connection test in Azure:**
   ```bash
   # SSH into App Service
   az webapp remote-connection create --resource-group <rg> --name <app-name>
   
   # Then from SSH terminal:
   python3 -c "from database import engine; print('Engine created')"
   ```

---

### ❌ Issue 7: "Application logs not visible"

**Symptoms:**
- No logs in Azure portal
- Can't see startup error messages

**Solution:**
1. Configure application logging:
   ```bash
   az webapp log config --resource-group <rg> --name <app-name> \
     --application-logging filesystem \
     --level information
   ```

2. View logs:
   ```bash
   az webapp log tail --resource-group <rg> --name <app-name>
   ```

3. Or in Portal: App Service → Log stream

---

## ✅ Pre-Deployment Checklist

- [ ] All environment variables set in Azure Portal
- [ ] ODBC Driver 18 installed (via startup.sh or Dockerfile)
- [ ] pyodbc installed locally and verified
- [ ] Connection string tested locally
- [ ] Azure SQL firewall allows Web App
- [ ] Database credentials verified
- [ ] `/health` endpoint returns `"status": "ok"`
- [ ] `requirements.txt` updated without MySQL drivers
- [ ] `config.py` uses environment variables
- [ ] `startup.sh` has executable permissions

---

## 🔍 Diagnostic Commands

### Local Testing
```bash
# Test settings loading
python -c "from config import get_settings; print(get_settings().get_db_config_summary())"

# Test pyodbc
python -c "import pyodbc; print('Available drivers:'); print(pyodbc.drivers())"

# Test connection
python -c "from database import engine; print('Engine created successfully')"

# Start app
uvicorn main:app --host 0.0.0.0 --port 8000

# Test health endpoint
curl http://localhost:8000/health
```

### Azure Testing
```bash
# View live logs
az webapp log tail --resource-group <rg> --name <app-name>

# SSH into container
az webapp remote-connection create --resource-group <rg> --name <app-name>

# Test from within container
python3 -c "import pyodbc; print(pyodbc.drivers())"

# Check environment variables
env | grep DB_
```

---

## 📋 Files Updated for Azure

1. **config.py**
   - ✅ Uses `os.getenv()` for all settings
   - ✅ Added `get_db_config_summary()` method
   - ✅ Priority: Environment > .env > defaults

2. **database.py**
   - ✅ Startup diagnostics logging
   - ✅ ODBC driver verification
   - ✅ Comprehensive error handling
   - ✅ NullPool for Azure SQL

3. **main.py**
   - ✅ Enhanced logging to stdout for Azure
   - ✅ Startup database test
   - ✅ Environment-aware CORS
   - ✅ Detailed error messages

4. **requirements.txt**
   - ✅ Removed MySQL drivers (aiomysql, pymysql)
   - ✅ Kept pyodbc for SQL Server

5. **startup.sh** (NEW)
   - ✅ Installs ODBC Driver 18
   - ✅ Verifies dependencies
   - ✅ Tests database connection

---

## 🚀 Quick Deploy Steps

1. **Update Azure Portal Settings:**
   - App Service → Configuration → Application settings
   - Add all DB_* environment variables

2. **Set Startup Command:**
   - Configuration → General settings
   - Startup Command: `/home/site/wwwroot/startup.sh`

3. **Deploy code:**
   ```bash
   git push azure main
   # or
   az webapp deployment source config-zip --resource-group <rg> --name <app-name> --src app.zip
   ```

4. **Monitor logs:**
   ```bash
   az webapp log tail --resource-group <rg> --name <app-name>
   ```

5. **Test health endpoint:**
   ```bash
   curl https://<your-app>.azurewebsites.net/health
   ```

---

## 🆘 Still Having Issues?

1. Check startup.sh execution in logs
2. Verify environment variables are exactly as expected
3. Test connection string locally first
4. Ensure ODBC Driver 18 is installed
5. Check Azure SQL Server firewall rules
6. Review Azure Application Insights for detailed errors

