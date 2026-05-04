"""
Database migration script to add Environment table and update existing data
Run this once to upgrade your database schema
"""
from app import app, db
from sqlalchemy import text

def migrate():
    with app.app_context():
        print("Starting database migration...")
        print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[-1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else 'SQLite'}")
        
        try:
            # Create all tables (will create new tables if they don't exist)
            db.create_all()
            print("✓ All tables created/verified")
            
            # Check if environment_id column exists in dashboard_link
            with db.engine.connect() as conn:
                # Check for PostgreSQL or SQLite
                if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
                    # PostgreSQL query
                    result = conn.execute(text("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name='dashboard_link' AND column_name='environment_id'
                    """))
                    column_exists = result.fetchone() is not None
                else:
                    # SQLite query
                    result = conn.execute(text("PRAGMA table_info(dashboard_link)"))
                    columns = [row[1] for row in result.fetchall()]
                    column_exists = 'environment_id' in columns
                
                if not column_exists:
                    print("Adding environment_id column to dashboard_link table...")
                    conn.execute(text("ALTER TABLE dashboard_link ADD COLUMN environment_id INTEGER"))
                    conn.commit()
                    print("✓ Column added successfully")
                else:
                    print("✓ environment_id column already exists")
                
                # Check existing data
                result = conn.execute(text("SELECT COUNT(*) FROM dashboard_link WHERE environment_id IS NULL"))
                links_without_env = result.fetchone()[0]
                
                if links_without_env > 0:
                    print(f"Found {links_without_env} links without environment assignment")
            
            print("\n✓ Migration completed successfully!")
            print("\nYou can now:")
            print("1. Start the Flask server: python app.py")
            print("   Or with Gunicorn: gunicorn wsgi:app")
            print("2. Create environments in the dashboard")
            print("3. Assign links to environments")
            print("4. Import GitHub issues as tasks")
            
        except Exception as e:
            print(f"✗ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == '__main__':
    migrate()

# Made with Bob
