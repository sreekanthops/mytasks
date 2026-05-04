"""
Database migration script to add Environment table and update existing data
Run this once to upgrade your database schema
"""
from app import app, db
import sqlite3

def migrate():
    with app.app_context():
        print("Starting database migration...")
        
        # Get database path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check if environment_id column exists
            cursor.execute("PRAGMA table_info(dashboard_link)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'environment_id' not in columns:
                print("Adding environment_id column to dashboard_link table...")
                cursor.execute("ALTER TABLE dashboard_link ADD COLUMN environment_id INTEGER")
                conn.commit()
                print("✓ Column added successfully")
            else:
                print("✓ environment_id column already exists")
            
            # Create environment table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS environment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    color VARCHAR(20) DEFAULT '#2563eb',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("✓ Environment table created/verified")
            
            # Check existing data
            cursor.execute("SELECT COUNT(*) FROM dashboard_link WHERE environment_id IS NULL")
            links_without_env = cursor.fetchone()[0]
            
            if links_without_env > 0:
                print(f"Found {links_without_env} links without environment assignment")
            
            conn.close()
            
            print("\n✓ Migration completed successfully!")
            print("\nYou can now:")
            print("1. Restart the Flask server: python app.py")
            print("2. Create environments in the dashboard")
            print("3. Assign links to environments")
            print("4. Import GitHub issues as tasks")
            
        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"✗ Migration failed: {e}")
            raise

if __name__ == '__main__':
    migrate()

# Made with Bob
