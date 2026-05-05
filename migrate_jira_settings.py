#!/usr/bin/env python3
"""
Migration script to add Jira configuration columns to the Settings table
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///mytasks.db')

# Handle Heroku postgres:// to postgresql:// conversion
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

def migrate_postgresql():
    """Migrate PostgreSQL database"""
    # Parse connection string
    # Format: postgresql://user@host:port/dbname
    import re
    match = re.match(r'postgresql://([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
    if not match:
        # Try without port
        match = re.match(r'postgresql://([^@]+)@([^/]+)/(.+)', DATABASE_URL)
        if match:
            user, host, dbname = match.groups()
            port = 5432
        else:
            print("Could not parse DATABASE_URL")
            return False
    else:
        user, host, port, dbname = match.groups()
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            dbname=dbname
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Connected to PostgreSQL database")
        
        # Check if columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='settings' AND column_name='jira_url'
        """)
        
        if cursor.fetchone():
            print("✓ Jira columns already exist")
            return True
        
        # Add Jira columns
        print("Adding Jira configuration columns...")
        
        cursor.execute("""
            ALTER TABLE settings 
            ADD COLUMN IF NOT EXISTS jira_url VARCHAR(200),
            ADD COLUMN IF NOT EXISTS jira_email VARCHAR(200),
            ADD COLUMN IF NOT EXISTS jira_api_token VARCHAR(200),
            ADD COLUMN IF NOT EXISTS jira_project_key VARCHAR(50)
        """)
        
        print("✓ Successfully added Jira columns to settings table")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Error migrating PostgreSQL: {e}")
        return False

def migrate_sqlite():
    """Migrate SQLite database"""
    import sqlite3
    
    try:
        conn = sqlite3.connect('mytasks.db')
        cursor = conn.cursor()
        
        print("Connected to SQLite database")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(settings)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'jira_url' in columns:
            print("✓ Jira columns already exist")
            return True
        
        # Add Jira columns
        print("Adding Jira configuration columns...")
        
        cursor.execute("ALTER TABLE settings ADD COLUMN jira_url VARCHAR(200)")
        cursor.execute("ALTER TABLE settings ADD COLUMN jira_email VARCHAR(200)")
        cursor.execute("ALTER TABLE settings ADD COLUMN jira_api_token VARCHAR(200)")
        cursor.execute("ALTER TABLE settings ADD COLUMN jira_project_key VARCHAR(50)")
        
        conn.commit()
        print("✓ Successfully added Jira columns to settings table")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Error migrating SQLite: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Jira Settings Migration Script")
    print("=" * 60)
    print(f"Database URL: {DATABASE_URL}")
    print()
    
    if DATABASE_URL.startswith('postgresql://'):
        success = migrate_postgresql()
    elif DATABASE_URL.startswith('sqlite:///'):
        success = migrate_sqlite()
    else:
        print("✗ Unsupported database type")
        success = False
    
    print()
    if success:
        print("=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        print("\nYou can now:")
        print("1. Restart your application")
        print("2. Go to Settings page")
        print("3. Configure Jira settings")
        print("4. Access Jira Issues page")
    else:
        print("=" * 60)
        print("✗ Migration failed")
        print("=" * 60)

# Made with Bob
