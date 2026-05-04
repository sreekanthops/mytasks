#!/usr/bin/env python3
"""
Migration script to add mute_until column to Task table
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///mytasks.db')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

print(f"Connecting to database...")
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        # Check if column exists
        if 'postgresql' in DATABASE_URL:
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='task' AND column_name='mute_until'
            """))
            exists = result.fetchone() is not None
        else:
            # SQLite
            result = conn.execute(text("PRAGMA table_info(task)"))
            columns = [row[1] for row in result.fetchall()]
            exists = 'mute_until' in columns
        
        if exists:
            print("✓ Column 'mute_until' already exists in task table")
        else:
            print("Adding 'mute_until' column to task table...")
            conn.execute(text("ALTER TABLE task ADD COLUMN mute_until TIMESTAMP"))
            conn.commit()
            print("✓ Successfully added 'mute_until' column")
        
        print("\n✅ Migration completed successfully!")
        
except Exception as e:
    print(f"\n❌ Migration failed: {e}")
    print("\nPlease run this script to add the mute_until column:")
    print("python migrate_mute_until.py")

# Made with Bob
