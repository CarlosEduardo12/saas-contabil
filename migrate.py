#!/usr/bin/env python3
"""
Simple migration script for Railway
"""
import asyncio
import os
import sys
sys.path.append('/app')

from sqlalchemy import text
from src.core.database import engine

async def migrate():
    """Add Ammer Pay fields to orders table"""
    
    migrations = [
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS ammer_payment_id TEXT;",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS ammer_payment_url TEXT;", 
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_method VARCHAR(20) DEFAULT 'ammer_pay';"
    ]
    
    try:
        async with engine.begin() as conn:
            for migration in migrations:
                print(f"Executing: {migration}")
                await conn.execute(text(migration))
                print("✅ Success")
        
        print("🎉 Migration completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(migrate())
    sys.exit(0 if success else 1)