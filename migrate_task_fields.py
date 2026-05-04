"""
Migration script to add GitHub issue fields and priority to Task model
"""
from app import app, db
from sqlalchemy import text

def migrate():
    with app.app_context():
        try:
            # Add new columns to task table
            with db.engine.connect() as conn:
                # Check if columns exist before adding
                result = conn.execute(text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name='task' AND column_name='github_issue_number'
                """))
                
                if not result.fetchone():
                    print("Adding new columns to task table...")
                    
                    conn.execute(text("ALTER TABLE task ADD COLUMN github_issue_number VARCHAR(50)"))
                    conn.execute(text("ALTER TABLE task ADD COLUMN github_issue_title VARCHAR(500)"))
                    conn.execute(text("ALTER TABLE task ADD COLUMN github_issue_url VARCHAR(500)"))
                    conn.execute(text("ALTER TABLE task ADD COLUMN priority VARCHAR(20) DEFAULT 'medium'"))
                    conn.execute(text("ALTER TABLE task ADD COLUMN deadline TIMESTAMP"))
                    conn.execute(text("ALTER TABLE task ADD COLUMN is_muted BOOLEAN DEFAULT FALSE"))
                    conn.execute(text("ALTER TABLE task ADD COLUMN last_reminded_at TIMESTAMP"))
                    
                    conn.commit()
                    print("✅ Migration completed successfully!")
                else:
                    # Check if mute columns exist
                    result2 = conn.execute(text("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name='task' AND column_name='is_muted'
                    """))
                    
                    if not result2.fetchone():
                        print("Adding mute columns...")
                        conn.execute(text("ALTER TABLE task ADD COLUMN is_muted BOOLEAN DEFAULT FALSE"))
                        conn.execute(text("ALTER TABLE task ADD COLUMN last_reminded_at TIMESTAMP"))
                        conn.commit()
                        print("✅ Mute columns added!")
                    else:
                        print("✅ All columns already exist, no migration needed.")
                    
        except Exception as e:
            print(f"❌ Migration error: {e}")
            print("Note: If using SQLite, columns may have been added automatically.")

if __name__ == '__main__':
    migrate()

# Made with Bob
