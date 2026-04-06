from app import app, db
from models import ExamSession, ExamQuestion
from sqlalchemy import text

with app.app_context():
    # ExamSession updates
    db.session.execute(text("ALTER TABLE exam_session ADD COLUMN IF NOT EXISTS exam_type VARCHAR(20) DEFAULT 'quiz';"))
    db.session.execute(text("ALTER TABLE exam_session ADD COLUMN IF NOT EXISTS weight FLOAT DEFAULT 10.0;"))
    
    # ExamQuestion updates (Sections)
    db.session.execute(text("ALTER TABLE exam_question ADD COLUMN IF NOT EXISTS section_name VARCHAR(100) DEFAULT 'Section A';"))
    db.session.execute(text("ALTER TABLE exam_question ADD COLUMN IF NOT EXISTS section_order INTEGER DEFAULT 0;"))
    
    db.session.commit()
    print('Database successfully migrated!')
