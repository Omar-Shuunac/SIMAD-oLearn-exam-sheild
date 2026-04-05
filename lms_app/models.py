from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False) # 'student', 'instructor', 'sys_admin', 'exam_admin', 'proctor'
    status = db.Column(db.String(20), default='active') # 'active', 'suspended'
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='student', lazy=True)
    submissions = db.relationship('Submission', backref='student', lazy=True)
    verifications = db.relationship('IdentityVerification', backref='student', lazy=True)

class IdentityVerification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    photo_url = db.Column(db.Text) # Web URL or local path
    video_url = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending') # 'pending', 'verified', 'flagged'

class ExamPolicy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    version = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='draft') # 'draft', 'approved', 'locked'
    
    identity_tier = db.Column(db.Integer, default=1) # Tier 1 or 2
    secure_mode = db.Column(db.Boolean, default=True) # Full lock
    proctoring_level = db.Column(db.String(50), default='full') # 'none', 'video', 'full'
    violation_threshold = db.Column(db.Integer, default=3)
    rejoin_grace_mins = db.Column(db.Integer, default=5)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('exam_session.id'), nullable=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=True)
    text = db.Column(db.Text, nullable=False)
    points = db.Column(db.Integer, default=10)
    q_type = db.Column(db.String(50), default='multiple_choice') # 'mcq', 'short_answer', 'matching', 'drag_drop'
    config_json = db.Column(db.Text, nullable=True) # For matching pairs or complex types
    
    choices = db.relationship('Choice', backref='question', lazy=True, cascade="all, delete-orphan")

class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)

class ExamSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    policy_id = db.Column(db.Integer, db.ForeignKey('exam_policy.id'))

    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    duration_mins = db.Column(db.Integer, default=60)  # Phase 2: enforced timer
    status = db.Column(db.String(20), default='scheduled')  # 'scheduled', 'live', 'ended'
    is_placement = db.Column(db.Boolean, default=False)       # Phase 2: placement test flag

    attempts = db.relationship('ExamAttempt', backref='session', lazy=True)
    questions = db.relationship('Question', backref='exam_session', lazy=True,
                                foreign_keys='Question.session_id')

class ExamAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('exam_session.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    status = db.Column(db.String(20), default='started')  # 'started', 'in_progress', 'submitted', 'flagged'
    integrity_status = db.Column(db.String(20), default='pending')  # 'pending', 'certified', 'invalidated', 'appealed'

    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime, nullable=True)

    # Phase 2: scoring + answer storage
    answers_json = db.Column(db.Text, nullable=True)   # JSON: {"q_id": "answer", ...}
    score = db.Column(db.Float, nullable=True)          # auto-calculated for MCQ
    max_score = db.Column(db.Float, nullable=True)

    student = db.relationship('User', backref='exam_attempts', lazy=True)

class IntegrityFlag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('exam_attempt.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    flag_type = db.Column(db.String(50)) # 'tab_switch', 'face_loss', 'audio_event'
    severity = db.Column(db.String(20)) # 'low', 'medium', 'high'
    evidence_url = db.Column(db.String(500))

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(200), nullable=False)
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    reason = db.Column(db.Text) # For break-glass or sensitive changes

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    modules = db.relationship('Module', backref='course', lazy=True)
    assignments = db.relationship('Assignment', backref='course', lazy=True)

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    progress = db.Column(db.Integer, default=0)
    grade = db.Column(db.Float, nullable=True)

    course = db.relationship('Course', backref='enrollments', lazy=True)

class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content_type = db.Column(db.String(50)) 
    content_url = db.Column(db.String(500))

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    points = db.Column(db.Integer, default=100)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_path = db.Column(db.String(500))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    grade = db.Column(db.Float, nullable=True)
    feedback = db.Column(db.Text, nullable=True)


# ─── Phase 1: Announcements ──────────────────────────────────────────────────

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    # NULL course_id = platform-wide; set course_id = course-level
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_pinned = db.Column(db.Boolean, default=False)

    course = db.relationship('Course', backref='announcements', lazy=True)
    author = db.relationship('User', backref='announcements', lazy=True)


# ─── Phase 1: Module Progress Tracking ───────────────────────────────────────

class ModuleView(db.Model):
    """Records when a student views/completes a specific module."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
