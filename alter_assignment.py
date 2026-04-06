import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'lms_app')))
from app import app, db
from sqlalchemy import text

def run_migration():
    with app.app_context():
        try:
            # Add weight column to assignment
            db.session.execute(text('ALTER TABLE assignment ADD COLUMN IF NOT EXISTS weight FLOAT DEFAULT 10.0'))
            db.session.commit()
            print("Successfully added weight to assignment table.")
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()

if __name__ == "__main__":
    run_migration()
