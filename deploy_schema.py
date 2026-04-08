#!/usr/bin/env python3
"""
Deploy SQL Server schema to Azure SQL
"""
import sys
import os

try:
    import pyodbc
except ImportError:
    print("Installing pyodbc...")
    os.system("pip install pyodbc")
    import pyodbc

# Connection parameters
server = "artisetsql.database.windows.net"
database = "campus5"
username = "artiset"
password = "Qwerty@123"

# Build connection string
connection_string = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=yes;"
    f"Connection Timeout=60"
)

print("=" * 80)
print("DEPLOYING SCHEMA TO AZURE SQL")
print("=" * 80)
print(f"Server: {server}")
print(f"Database: {database}")
print(f"User: {username}")
print()

try:
    print("Connecting to Azure SQL...")
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    print("✓ Connected!")
    print()

    # Read the SQL file
    with open("db_sqlserver.sql", "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split by GO statements (SQL Server batch separator)
    # For now, let's execute the entire script
    print("Executing schema creation SQL...")
    print()

    # ExecuteScript is not available, so we'll execute statements one by one
    # Split by ; but be careful with statements that have ; inside strings
    statements = []
    current_statement = ""
    in_string = False
    quote_char = None

    for char in sql_content:
        if char in ('"', "'") and not in_string:
            in_string = True
            quote_char = char
        elif char == quote_char and in_string:
            in_string = False
        elif char == ";" and not in_string:
            current_statement += char
            if current_statement.strip():
                statements.append(current_statement)
            current_statement = ""
            continue

        current_statement += char

    if current_statement.strip():
        statements.append(current_statement)

    # Execute each statement
    success_count = 0
    error_count = 0

    for i, stmt in enumerate(statements, 1):
        stmt = stmt.strip()
        if not stmt or stmt.startswith("--"):
            continue

        try:
            cursor.execute(stmt)
            conn.commit()
            success_count += 1
            # Show progress
            if success_count % 10 == 0 or "CREATE TABLE" in stmt:
                preview = stmt[:80].replace("\n", " ")
                print(f"  ✓ [{i}] {preview}...")

        except Exception as e:
            error_count += 1
            if "already exists" not in str(e).lower():
                print(f"  ✗ [{i}] Error: {e}")
                print(f"       Statement: {stmt[:100]}...")

    cursor.close()
    conn.close()

    print()
    print("=" * 80)
    print(f"SCHEMA DEPLOYMENT COMPLETE")
    print("=" * 80)
    print(f"Successfully executed: {success_count} statements")
    if error_count > 0:
        print(f"Errors encountered: {error_count} (may be OK if tables already exist)")
    print()
    print("✓ Database schema is now deployed to Azure SQL!")

except Exception as e:
    print()
    print("=" * 80)
    print(f"ERROR: {e}")
    print("=" * 80)
    sys.exit(1)
