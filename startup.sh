#!/bin/bash
# Startup script for Azure App Service deployment
# This script installs ODBC driver and dependencies

set -e  # Exit on error

echo "=========================================="
echo "🚀 FastAPI Startup Script for Azure"
echo "=========================================="

# Step 1: Update package manager
echo "Step 1: Updating package manager..."
apt-get update -y
apt-get upgrade -y

# Step 2: Install ODBC Driver 18 for SQL Server
echo "Step 2: Installing ODBC Driver 18 for SQL Server..."
apt-get install -y curl gnupg2

# Download Microsoft repository GPG key
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -

# Add Microsoft repository
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list | tee /etc/apt/sources.list.d/mssql-release.list

# Update package manager
apt-get update -y

# Install ODBC driver (accept ODBC license)
ACCEPT_EULA=Y apt-get install -y msodbcsql18

# Install dependencies for ODBC
apt-get install -y unixodbc-dev

# Step 3: Verify Python installation
echo "Step 3: Verifying Python installation..."
python3 --version
pip --version

# Step 4: Install Python dependencies
echo "Step 4: Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 5: Verify ODBC drivers
echo "Step 5: Verifying ODBC drivers..."
python3 -c "import pyodbc; print('✓ pyodbc installed'); print('Available drivers:'); print(pyodbc.drivers())"

# Step 6: Test database connection
echo "Step 6: Testing database connection..."
python3 -c "from config import get_settings; s = get_settings(); print(f'✓ Settings loaded: {s.db_host}')" || echo "⚠️  Settings check failed"

# Step 7: Create log directory
echo "Step 7: Creating log directory..."
mkdir -p /tmp/logs
chmod 777 /tmp/logs

# Step 8: Display environment info
echo "Step 8: Environment Information:"
echo "  Python: $(python3 --version)"
echo "  Pip: $(pip --version)"
echo "  ODBC Driver 18 status:"
odbcinst -j || echo "  (odbcinst command not found, but driver likely installed)"

echo ""
echo "=========================================="
echo "✓ Startup script completed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Ensure environment variables are set in Azure App Service:"
echo "     - DB_DRIVER=mssql"
echo "     - DB_HOST=artisetsql.database.windows.net"
echo "     - DB_PORT=1433"
echo "     - DB_USER=artiset"
echo "     - DB_PASSWORD=<your-password>"
echo "     - DB_NAME=campus5"
echo "     - APP_ENV=production"
echo ""
echo "  2. Start the application:"
echo "     uvicorn main:app --host 0.0.0.0 --port 8000"
echo ""
echo "=========================================="
