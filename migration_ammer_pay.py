#!/usr/bin/env python3
"""
Migration script to add Ammer Pay fields to the orders table
Run this script to update your database schema
"""

import asyncio
import os
from sqlalchemy import text
from src.core.database import engine

async def migrate_database():
    """Add Ammer Pay fields to orders table"""
    
    migrations = [
        """
        ALTER TABLE orders 
        ADD COLUMN IF NOT EXISTS ammer_payment_id TEXT;
        """,
        """
        ALTER TABLE orders 
        ADD COLUMN IF NOT EXISTS ammer_payment_url TEXT;
        """,
        """
        ALTER TABLE orders 
        ADD COLUMN IF NOT EXISTS payment_method VARCHAR(20) DEFAULT 'ammer_pay';
        """
    ]
    
    try:
        async with engine.begin() as conn:
            for migration in migrations:
                print(f"Executing: {migration.strip()}")
                await conn.execute(text(migration))
                print("✅ Migration executed successfully")
        
        print("\n🎉 All migrations completed successfully!")
        print("Your database is now ready for Ammer Pay integration.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔄 Starting database migration for Ammer Pay integration...")
    success = asyncio.run(migrate_database())
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("You can now deploy your application with Ammer Pay support.")
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above and try again.")