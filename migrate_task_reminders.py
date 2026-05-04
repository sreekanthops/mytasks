#!/usr/bin/env python3
"""
Migration script to add TaskReminder table
"""
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def migrate():
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not found in .env file")
        return
    
    conn = None
    try:
        # Connect to database using DATABASE_URL
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        print("Connected to database successfully!")
        
        # Create TaskReminder table
        print("\nCreating TaskReminder table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS task_reminder (
                id SERIAL PRIMARY KEY,
                task_id INTEGER NOT NULL REFERENCES task(id) ON DELETE CASCADE,
                reminder_type VARCHAR(20) NOT NULL,
                interval_minutes INTEGER,
                custom_time TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                last_triggered TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on task_id for faster lookups
        print("Creating index on task_id...")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_task_reminder_task_id 
            ON task_reminder(task_id)
        """)
        
        # Create index on is_active for faster filtering
        print("Creating index on is_active...")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_task_reminder_active 
            ON task_reminder(is_active)
        """)
        
        # Commit changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("TaskReminder table created with indexes")
        
        # Verify table creation
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'task_reminder'
            ORDER BY ordinal_position
        """)
        
        print("\nTaskReminder table structure:")
        print("-" * 60)
        for row in cur.fetchall():
            print(f"  {row[0]:<20} {row[1]:<20} {'NULL' if row[2] == 'YES' else 'NOT NULL'}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        if conn:
            conn.rollback()
        raise

if __name__ == '__main__':
    migrate()

# Made with Bob
