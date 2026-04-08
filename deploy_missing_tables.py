import asyncio
from database import engine
from sqlalchemy import text

async def create_missing_tables():
    with open('missing_tables_sqlserver.sql', 'r') as f:
        sql_content = f.read()
    
    # Split by GO statements and execute each batch
    statements = sql_content.split('GO')
    
    async with engine.begin() as conn:
        for i, statement in enumerate(statements):
            stmt = statement.strip()
            if stmt and not stmt.startswith('--'):
                try:
                    print(f"Executing batch {i}...")
                    await conn.execute(text(stmt))
                    print(f"  ✓ Success")
                except Exception as e:
                    print(f"  ✗ Error: {e}")
    
    print("\nAll missing tables created!")

if __name__ == "__main__":
    asyncio.run(create_missing_tables())
