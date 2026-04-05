import sys
import os
import json

# Add lms_app to path
sys.path.insert(0, os.path.abspath('lms_app'))

from app import app
from models import db, User, Course, Enrollment, ExamSession, Question, Choice, Module, Assignment, IdentityVerification, IntegrityFlag, AuditLog

def backup_db():
    with app.app_context():
        backup_file = "neon_db_backup.json"
        
        # Check connection
        try:
            db.session.execute(db.text('SELECT 1'))
            print("Database connection verified.")
        except Exception as e:
            print(f"Connection failed: {e}")
            return

        data = {
            "users": [dict(id=u.id, name=u.name, email=u.email, role=u.role, status=u.status) for u in User.query.all()],
            "courses": [dict(id=c.id, code=c.code, title=c.title, instructor_id=c.instructor_id) for c in Course.query.all()],
            "enrollments": [dict(id=e.id, user_id=e.user_id, course_id=e.course_id, progress=e.progress, grade=e.grade) for e in Enrollment.query.all()],
            "sessions": [dict(id=s.id, title=s.title, course_id=s.course_id, status=s.status) for s in ExamSession.query.all()],
            "questions": [dict(id=q.id, text=q.text, q_type=q.q_type, points=q.points) for q in Question.query.all()],
            "choices": [dict(id=c.id, question_id=c.question_id, text=c.text, is_correct=c.is_correct) for c in Choice.query.all()],
            "verifications": [dict(id=v.id, user_id=v.user_id, status=v.status) for v in IdentityVerification.query.all()],
            "flags": [dict(id=f.id, attempt_id=f.attempt_id, flag_type=f.flag_type) for f in IntegrityFlag.query.all()],
            "audit_logs": [dict(id=l.id, user_id=l.user_id, action=l.action) for l in AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()]
        }
        
        with open(backup_file, "w") as f:
            json.dump(data, f, indent=4)
        
        print(f"JSON Backup successful! File created: {os.path.abspath(backup_file)}")

if __name__ == "__main__":
    backup_db()
