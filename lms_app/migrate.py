"""
Migration script: Applies the new schema to the live PostgreSQL database.
Run once from the lms_app/ directory:
    python migrate.py
"""
from app import app, db
from sqlalchemy import text

MIGRATIONS = [
    # ── Question Bank ──────────────────────────────────────────────────────────
    "ALTER TABLE question ADD COLUMN IF NOT EXISTS author_id INTEGER REFERENCES \"user\"(id)",
    "ALTER TABLE question ADD COLUMN IF NOT EXISTS course_id INTEGER REFERENCES course(id)",
    "ALTER TABLE question ADD COLUMN IF NOT EXISTS explanation TEXT",
    "ALTER TABLE question ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()",
    "ALTER TABLE question ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()",
    "ALTER TABLE question DROP COLUMN IF EXISTS session_id",
    "ALTER TABLE question DROP COLUMN IF EXISTS assignment_id",

    # QuestionTag table
    """CREATE TABLE IF NOT EXISTS question_tag (
        id SERIAL PRIMARY KEY,
        question_id INTEGER NOT NULL REFERENCES question(id) ON DELETE CASCADE,
        tag VARCHAR(100) NOT NULL
    )""",

    # ExamQuestion junction table
    """CREATE TABLE IF NOT EXISTS exam_question (
        id SERIAL PRIMARY KEY,
        session_id INTEGER NOT NULL REFERENCES exam_session(id) ON DELETE CASCADE,
        question_id INTEGER NOT NULL REFERENCES question(id),
        "order" INTEGER DEFAULT 0,
        points_override INTEGER
    )""",

    # ── ExamSession upgrades ───────────────────────────────────────────────────
    "ALTER TABLE exam_session ADD COLUMN IF NOT EXISTS description TEXT",
    "ALTER TABLE exam_session ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES \"user\"(id)",
    "ALTER TABLE exam_session ADD COLUMN IF NOT EXISTS structural_lock BOOLEAN DEFAULT FALSE",
    "ALTER TABLE exam_session ADD COLUMN IF NOT EXISTS grades_released BOOLEAN DEFAULT FALSE",
    "ALTER TABLE exam_session ADD COLUMN IF NOT EXISTS passing_score FLOAT DEFAULT 60.0",
    "ALTER TABLE exam_session ADD COLUMN IF NOT EXISTS attempts_allowed INTEGER DEFAULT 1",
    "ALTER TABLE exam_session ADD COLUMN IF NOT EXISTS randomize_questions BOOLEAN DEFAULT FALSE",
    "ALTER TABLE exam_session ADD COLUMN IF NOT EXISTS randomize_choices BOOLEAN DEFAULT FALSE",
    "ALTER TABLE exam_session ADD COLUMN IF NOT EXISTS allow_navigation BOOLEAN DEFAULT TRUE",
    "ALTER TABLE exam_session ADD COLUMN IF NOT EXISTS show_answers_after BOOLEAN DEFAULT FALSE",
    "ALTER TABLE exam_session ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()",

    # ── ExamAttempt upgrades ──────────────────────────────────────────────────
    "ALTER TABLE exam_attempt ADD COLUMN IF NOT EXISTS identity_verified BOOLEAN DEFAULT FALSE",
    "ALTER TABLE exam_attempt ADD COLUMN IF NOT EXISTS browser_locked BOOLEAN DEFAULT FALSE",
    "ALTER TABLE exam_attempt ADD COLUMN IF NOT EXISTS webcam_active BOOLEAN DEFAULT FALSE",

    # ── IntegrityFlag upgrades ────────────────────────────────────────────────
    "ALTER TABLE integrity_flag ADD COLUMN IF NOT EXISTS ai_confidence FLOAT",
    "ALTER TABLE integrity_flag ADD COLUMN IF NOT EXISTS screenshot_url TEXT",
    "ALTER TABLE integrity_flag ADD COLUMN IF NOT EXISTS reviewed_by INTEGER REFERENCES \"user\"(id)",
    "ALTER TABLE integrity_flag ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP",
    "ALTER TABLE integrity_flag ADD COLUMN IF NOT EXISTS resolution VARCHAR(20)",
    "ALTER TABLE integrity_flag ADD COLUMN IF NOT EXISTS review_note TEXT",
    "ALTER TABLE integrity_flag DROP COLUMN IF EXISTS evidence_url",

    # ── Course upgrades ───────────────────────────────────────────────────────
    "ALTER TABLE course ADD COLUMN IF NOT EXISTS description TEXT",
    "ALTER TABLE course ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'draft'",
    "ALTER TABLE course ADD COLUMN IF NOT EXISTS enrollment_cap INTEGER",
    "ALTER TABLE course ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()",

    # ── Enrollment upgrades ───────────────────────────────────────────────────
    "ALTER TABLE enrollment ADD COLUMN IF NOT EXISTS enrolled_at TIMESTAMP DEFAULT NOW()",
    "ALTER TABLE enrollment ADD COLUMN IF NOT EXISTS extra_time_mins INTEGER DEFAULT 0",

    # ── Module upgrades ───────────────────────────────────────────────────────
    "ALTER TABLE module ADD COLUMN IF NOT EXISTS section VARCHAR(200)",
    "ALTER TABLE module ADD COLUMN IF NOT EXISTS \"order\" INTEGER DEFAULT 0",
    "ALTER TABLE module ADD COLUMN IF NOT EXISTS is_published BOOLEAN DEFAULT FALSE",

    # ── Assignment upgrades ───────────────────────────────────────────────────
    "ALTER TABLE assignment ADD COLUMN IF NOT EXISTS submission_type VARCHAR(50) DEFAULT 'any'",
    "ALTER TABLE assignment ADD COLUMN IF NOT EXISTS allow_late BOOLEAN DEFAULT FALSE",
    "ALTER TABLE assignment ADD COLUMN IF NOT EXISTS late_penalty_pct FLOAT DEFAULT 0.0",
    "ALTER TABLE assignment ADD COLUMN IF NOT EXISTS grades_released BOOLEAN DEFAULT FALSE",

    # ── Submission upgrades ───────────────────────────────────────────────────
    "ALTER TABLE submission ADD COLUMN IF NOT EXISTS content_text TEXT",
    "ALTER TABLE submission ADD COLUMN IF NOT EXISTS link_url TEXT",
    "ALTER TABLE submission ADD COLUMN IF NOT EXISTS is_late BOOLEAN DEFAULT FALSE",
    "ALTER TABLE submission ADD COLUMN IF NOT EXISTS feedback_released BOOLEAN DEFAULT FALSE",

    # GradeAppeal table
    """CREATE TABLE IF NOT EXISTS grade_appeal (
        id SERIAL PRIMARY KEY,
        student_id INTEGER NOT NULL REFERENCES \"user\"(id),
        attempt_id INTEGER REFERENCES exam_attempt(id),
        submission_id INTEGER REFERENCES submission(id),
        reason TEXT NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT NOW(),
        resolved_at TIMESTAMP,
        resolved_by INTEGER REFERENCES \"user\"(id),
        resolution_note TEXT
    )""",

    # ModuleView upgrades
    "ALTER TABLE module_view ADD COLUMN IF NOT EXISTS completed BOOLEAN DEFAULT FALSE",

    # Flag Review logic
    "ALTER TABLE exam_attempt ADD COLUMN IF NOT EXISTS flags_json TEXT",

    # Security & MFA
    "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS mfa_enabled BOOLEAN DEFAULT FALSE",
    "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS mfa_secret VARCHAR(100)",

    """CREATE TABLE IF NOT EXISTS login_session (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES \"user\"(id),
        session_token VARCHAR(255) NOT NULL UNIQUE,
        ip_address VARCHAR(45),
        device_info VARCHAR(200),
        created_at TIMESTAMP DEFAULT NOW(),
        is_active BOOLEAN DEFAULT TRUE
    )""",

    """CREATE TABLE IF NOT EXISTS bookmark (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES \"user\"(id),
        module_id INTEGER REFERENCES module(id),
        title VARCHAR(200),
        url VARCHAR(500) NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    )""",

    """CREATE TABLE IF NOT EXISTS student_note (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES \"user\"(id),
        course_id INTEGER REFERENCES course(id),
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    )""",

    """CREATE TABLE IF NOT EXISTS system_config (
        key VARCHAR(100) PRIMARY KEY,
        value TEXT,
        description VARCHAR(255),
        updated_at TIMESTAMP DEFAULT NOW()
    )""",
]

with app.app_context():
    for sql in MIGRATIONS:
        try:
            db.session.execute(text(sql))
            db.session.commit()
            print(f"✅ OK: {sql[:60]}...")
        except Exception as e:
            db.session.rollback()
            print(f"⚠️  SKIP (already exists?): {str(e)[:100]}")

print("\n✅ Migration complete!")
