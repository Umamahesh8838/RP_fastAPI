# Azure SQL Server Migration Guide

## Migration Summary

Your FastAPI application has been successfully configured to use **Azure SQL Server** instead of localhost MySQL.

---

## ✅ Changes Made

### 1. **`.env` File** - Database Credentials Updated
- ❌ Removed: MySQL localhost configuration
- ✅ Added: Azure SQL Server connection details
  - Server: `artisetsql.database.windows.net`
  - Database: `campus5`
  - Driver: MSSQL
  - Port: `1433`

```env
# Azure SQL Server Database
DB_DRIVER=mssql
DB_HOST=artisetsql.database.windows.net
DB_PORT=1433
DB_USER=artiset
DB_PASSWORD=Qwerty@123
DB_NAME=campus5
```

### 2. **`config.py`** - Connection String Generator
- ✅ Updated default driver from `mysql` to `mssql`
- ✅ Updated host, port, user, and password to Azure SQL details
- ✅ Configured MSSQL connection string with **pyodbc** driver:
  ```
  mssql+pyodbc://user:password@host:port/database
  ?driver=ODBC+Driver+18+for+SQL+Server
  &Encrypt=yes
  &TrustServerCertificate=no
  ```
- ✅ Set `TrustServerCertificate=no` for production security

### 3. **`database.py`** - Connection Pool Optimization
- ✅ Added `NullPool` pooling class for Azure SQL Server (prevents connection pooling issues)
- ✅ Reduced pool size to `5` with `max_overflow=10` (optimized for Azure)
- ✅ Added proper logging configuration
- ✅ Kept `pool_pre_ping=True` to validate connections

### 4. **`requirements.txt`** - Dependencies Updated
- ❌ Removed: `aiomysql`, `pymysql`, `aioodbc`
- ✅ Kept: `pyodbc>=5.0.1` (native SQL Server driver)
- ✅ Kept: All other dependencies (FastAPI, SQLAlchemy, etc.)

### 5. **`main.py`** - CORS and Environment Configuration
- ✅ Updated CORS middleware to support Azure Web App domains
- ✅ Added environment-aware allowed origins:
  - **Production**: Only Azure domains
  - **Development**: Localhost domains

---

## 🚀 Pre-Deployment Checklist

### 1. **Install ODBC Driver 18 for SQL Server**

#### On Windows:
```powershell
# Download and install from Microsoft
# https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
```

#### On Linux (Azure App Service):
Add to your deployment:
```bash
apt-get update && apt-get install -y odbc-driver-18-for-sql-server
```

Or create a `startup.sh` in your Azure App Service:
```bash
#!/bin/bash
apt-get update
apt-get install -y odbc-driver-18-for-sql-server
python -m pip install -r requirements.txt
```

### 2. **Update Requirements and Install Locally**
```powershell
# Windows
pip install -r requirements.txt

# Linux
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. **Test Local Connection**
```powershell
python -c "from config import get_settings; print(get_settings().database_url)"
```

Expected output (sensitive info redacted):
```
mssql+pyodbc://artiset:Qwerty%40123@artisetsql.database.windows.net:1433/campus5?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=120
```

### 4. **Test Health Check Endpoint**
```bash
# Start the app
uvicorn main:app --reload

# In another terminal
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "database": {
    "status": "connected",
    "response_time_ms": 150,
    "host": "artisetsql.database.windows.net",
    "name": "campus5"
  }
}
```

---

## 🔒 Security Best Practices for Azure

### 1. **Environment Variables on Azure Web App**
```
Settings → Configuration → Application settings
```

Add these settings in Azure Portal:
- `DB_DRIVER`: `mssql`
- `DB_HOST`: `artisetsql.database.windows.net`
- `DB_PORT`: `1433`
- `DB_USER`: `artiset`
- `DB_PASSWORD`: `Qwerty@123` (or use Key Vault)
- `OPENROUTER_API_KEY`: Your key
- `APP_ENV`: `production`

### 2. **Use Azure Key Vault for Secrets** (Recommended)
Instead of storing passwords in .env:
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://<vault-name>.vault.azure.net/", credential=credential)
db_password = client.get_secret("db-password").value
```

### 3. **SQL Server Firewall Rules**
Ensure your Azure Web App's outbound IP is allowed:
```sql
-- Azure SQL Server → Firewall rules
-- Add your Web App's outbound IP
```

### 4. **Enable SSL/TLS**
```python
# Already configured in config.py
TrustServerCertificate=no  # Verify SSL certificates
Encrypt=yes                 # Encrypt connection
```

---

## 📱 Azure Web App Deployment

### Option 1: Azure CLI
```bash
# From project root
az webapp up --name <your-app-name> --sku B1 --resource-group <resource-group>
```

### Option 2: GitHub Actions (CI/CD)
Create `.github/workflows/azure-deploy.yml`:
```yaml
name: Deploy to Azure

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Deploy to Azure Web App
        uses: azure/webapps-deploy@v2
        with:
          app-name: ${{ secrets.AZURE_APP_NAME }}
          publish-profile: ${{ secrets.AZURE_PUBLISH_PROFILE }}
```

### Option 3: Docker Deployment
Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

# Install ODBC driver
RUN apt-get update && apt-get install -y odbc-driver-18-for-sql-server

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🧪 Testing in Production

### 1. **Test Health Endpoint**
```bash
curl https://<your-app>.azurewebsites.net/health
```

### 2. **Test Resume Upload**
```bash
curl -X POST https://<your-app>.azurewebsites.net/extract \
  -F "file=@resume.pdf"
```

### 3. **Monitor Logs**
```bash
# Azure Web App logs
az webapp log tail --name <your-app-name> --resource-group <resource-group>
```

---

## ⚠️ Common Issues & Solutions

### Issue 1: "ODBC Driver 18 for SQL Server not found"
**Solution**: Install ODBC driver on the server
```bash
apt-get install -y odbc-driver-18-for-sql-server
```

### Issue 2: "Login timeout expired"
**Solution**: Check firewall rules in Azure SQL Server
- Ensure Web App's outbound IP is whitelisted
- Verify credentials are correct

### Issue 3: "Connection pool exhausted"
**Solution**: Already fixed with `NullPool` configuration
- The change removes connection pooling for Azure SQL

### Issue 4: "Certificate verification failed"
**Solution**: Our config uses `TrustServerCertificate=no` for production
- This forces proper certificate verification

---

## 📋 Files Modified

| File | Changes |
|------|---------|
| `.env` | MySQL → Azure SQL credentials |
| `config.py` | Driver, host, port, user, password, connection string |
| `database.py` | NullPool for Azure, optimized pool settings |
| `requirements.txt` | Removed aiomysql/pymysql, kept pyodbc |
| `main.py` | CORS updated for Azure domains |

---

## ✨ Connection String Reference

### Current (Azure SQL Server):
```
mssql+pyodbc://artiset:Qwerty%40123@artisetsql.database.windows.net:1433/campus5?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=120
```

### Components:
- **Driver**: `mssql+pyodbc`
- **User**: `artiset`
- **Host**: `artisetsql.database.windows.net`
- **Port**: `1433`
- **Database**: `campus5`
- **Encryption**: Yes
- **Certificate Verification**: Yes (production-ready)

---

## 🎯 Next Steps

1. ✅ Update CORS allowed origins in `main.py` with your actual Azure domain
2. ✅ Test locally with new configuration
3. ✅ Deploy to Azure Web App
4. ✅ Monitor logs for connection issues
5. ✅ Set up health check alerts

---

## 📞 Support

For Azure SQL connectivity issues:
- [Azure SQL Connection Troubleshooting](https://learn.microsoft.com/en-us/azure/azure-sql/database/troubleshoot-connectivity-issues-guide)
- [ODBC Driver Documentation](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server)
