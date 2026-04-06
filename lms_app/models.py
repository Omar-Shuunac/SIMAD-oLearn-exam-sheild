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
    mfa_enabled = db.Column(db.Boolean, default=False)
    mfa_secret = db.Column(db.String(100), nullable=True)
    
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


# ─── Question Bank (First-Class Entity) ──────────────────────────────────────
# Questions are standalone — they belong to the bank, not to any single exam.
# Use the ExamQuestion junction table to associate questions with exams.

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # author/owner — which instructor created this question
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)

    text = db.Column(db.Text, nullable=False)
    points = db.Column(db.Integer, default=10)
    q_type = db.Column(db.String(50), default='mcq')
    # q_type values: 'mcq', 'true_false', 'short_answer', 'essay', 'fill_blank', 'matching'
    config_json = db.Column(db.Text, nullable=True)
    explanation = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    choices = db.relationship('Choice', backref='question', lazy=True, cascade="all, delete-orphan")
    tags = db.relationship('QuestionTag', backref='question', lazy=True, cascade="all, delete-orphan")
    author = db.relationship('User', backref='questions', lazy=True)


class QuestionTag(db.Model):
    """Tagging system for the question bank (topic, difficulty, chapter, etc.)"""
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    tag = db.Column(db.String(100), nullable=False)


class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)


# ─── Exam Session ─────────────────────────────────────────────────────────────

class ExamSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    policy_id = db.Column(db.Integer, db.ForeignKey('exam_policy.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    duration_mins = db.Column(db.Integer, default=60)
    status = db.Column(db.String(20), default='draft')
    # status: 'draft', 'scheduled', 'live', 'ended', 'archived'

    # CRITICAL: Structural lock — True once ANY student starts an attempt.
    structural_lock = db.Column(db.Boolean, default=False)

    # CRITICAL: Grade release — teacher must explicitly flip True.
    grades_released = db.Column(db.Boolean, default=False)

    passing_score = db.Column(db.Float, default=60.0)
    attempts_allowed = db.Column(db.Integer, default=1)
    randomize_questions = db.Column(db.Boolean, default=False)
    randomize_choices = db.Column(db.Boolean, default=False)
    allow_navigation = db.Column(db.Boolean, default=True)
    show_answers_after = db.Column(db.Boolean, default=False)
    is_placement = db.Column(db.Boolean, default=False)
    exam_type = db.Column(db.String(20), default='quiz')
    weight = db.Column(db.Float, default=10.0)


    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    attempts = db.relationship('ExamAttempt', backref='session', lazy=True)
    exam_questions = db.relationship('ExamQuestion', backref='session', lazy=True,
                                     cascade="all, delete-orphan")
    creator = db.relationship('User', backref='created_exams', lazy=True)


class ExamQuestion(db.Model):
    """Junction table: links Questions to ExamSessions.
    Allows the same question to appear in multiple exams."""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('exam_session.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    order = db.Column(db.Integer, default=0)
    points_override = db.Column(db.Integer, nullable=True)
    section_name = db.Column(db.String(100), default='Section A')
    section_order = db.Column(db.Integer, default=0)


    question = db.relationship('Question', backref='exam_links', lazy=True)


class ExamAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('exam_session.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    status = db.Column(db.String(20), default='started')
    integrity_status = db.Column(db.String(20), default='pending')

    identity_verified = db.Column(db.Boolean, default=False)
    browser_locked = db.Column(db.Boolean, default=False)
    webcam_active = db.Column(db.Boolean, default=False)

    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime, nullable=True)

    answers_json = db.Column(db.Text, nullable=True)
    flags_json = db.Column(db.Text, nullable=True)
    score = db.Column(db.Float, nullable=True)
    max_score = db.Column(db.Float, nullable=True)

    student = db.relationship('User', backref='exam_attempts', lazy=True)
    flags = db.relationship('IntegrityFlag', backref='attempt', lazy=True)


class IntegrityFlag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('exam_attempt.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    flag_type = db.Column(db.String(50))
    severity = db.Column(db.String(20))  # 'low', 'medium', 'high'
    ai_confidence = db.Column(db.Float, nullable=True)
    screenshot_url = db.Column(db.Text, nullable=True)

    # CRITICAL: flags NEVER auto-terminate. Human proctor decides.
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    resolution = db.Column(db.String(20), nullable=True)  # 'dismissed', 'confirmed', 'escalated'
    review_note = db.Column(db.Text, nullable=True)

    reviewer = db.relationship('User', backref='reviewed_flags', lazy=True)


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(200), nullable=False)
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    reason = db.Column(db.Text)

    user = db.relationship('User', backref='audit_logs', lazy=True)


# ─── Course ───────────────────────────────────────────────────────────────────

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='draft')  # 'draft', 'published', 'archived'
    enrollment_cap = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    modules = db.relationship('Module', backref='course', lazy=True)
    assignments = db.relationship('Assignment', backref='course', lazy=True)


class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    progress = db.Column(db.Integer, default=0)
    grade = db.Column(db.Float, nullable=True)
    extra_time_mins = db.Column(db.Integer, default=0)

    course = db.relationship('Course', backref='enrollments', lazy=True)


class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content_type = db.Column(db.String(50))
    content_url = db.Column(db.Text)
    section = db.Column(db.String(200), nullable=True)
    order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=False)

    views = db.relationship('ModuleView', backref='module', lazy=True)


class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    points = db.Column(db.Integer, default=100)
    submission_type = db.Column(db.String(50), default='any')  # 'file', 'text', 'link', 'any'
    allow_late = db.Column(db.Boolean, default=False)
    weight           = db.Column(db.Float, default=10.0)
    grades_released  = db.Column(db.Boolean, default=False)


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_path = db.Column(db.Text, nullable=True)
    content_text = db.Column(db.Text, nullable=True)
    link_url = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_late = db.Column(db.Boolean, default=False)
    grade = db.Column(db.Float, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    feedback_released = db.Column(db.Boolean, default=False)


class GradeAppeal(db.Model):
    """Student can request a review of their grade."""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    attempt_id = db.Column(db.Integer, db.ForeignKey('exam_attempt.id'), nullable=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submission.id'), nullable=True)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'under_review', 'upheld', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    resolution_note = db.Column(db.Text, nullable=True)

    student = db.relationship('User', foreign_keys=[student_id], backref='appeals', lazy=True)
    resolver = db.relationship('User', foreign_keys=[resolved_by], backref='resolved_appeals', lazy=True)


# ─── Announcements ────────────────────────────────────────────────────────────

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_pinned = db.Column(db.Boolean, default=False)

    course = db.relationship('Course', backref='announcements', lazy=True)
    author = db.relationship('User', backref='announcements', lazy=True)


# ─── Module Progress Tracking ─────────────────────────────────────────────────

class ModuleView(db.Model):
    """Records when a student views/completes a specific module."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)

# ─── Course Interaction ───────────────────────────────────────────────────────

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=True)
    title = db.Column(db.String(200), nullable=True)
    url = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StudentNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ─── Security & MFA ───────────────────────────────────────────────────────────

class LoginSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_token = db.Column(db.String(255), unique=True, nullable=False)
    ip_address = db.Column(db.String(45))
    device_info = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class SystemConfig(db.Model):
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SuperAdminSession(db.Model):
    """Hardware-bound privileged session token for Super Admin role."""
    __tablename__ = 'super_admin_session'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(300))
    mfa_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    revoked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    owner = db.relationship('User', foreign_keys=[user_id], backref='super_sessions')

class RolePermission(db.Model):
    """Dynamic permission matrix — defines capabilities per role."""
    __tablename__ = 'role_permission'
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(50), nullable=False)
    permission = db.Column(db.String(100), nullable=False)
    granted = db.Column(db.Boolean, default=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

