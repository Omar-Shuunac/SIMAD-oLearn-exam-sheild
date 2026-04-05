from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'simad_olearn_dev_key_change_in_prod')

# ─── Database Configuration ───────────────────────────────────────────────────
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://neondb_owner:npg_fXqno0th9eLi@ep-square-pine-aijrixgc-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 280,
    "pool_pre_ping": True,
}

# ─── File Upload Config ───────────────────────────────────────────────────────
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt', 'png', 'jpg', 'jpeg', 'zip'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

from models import (db, User, Course, ExamPolicy, ExamSession, AuditLog,
                    ExamAttempt, IntegrityFlag, Question, Choice, Enrollment,
                    IdentityVerification, Module, Assignment, Submission,
                    Announcement, ModuleView)
db.init_app(app)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    """Decorator: redirect to login if not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please sign in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """Decorator: enforce one of the allowed roles."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                flash('You do not have permission to access that page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator


def log_action(user_id, action, resource_type=None, resource_id=None, reason=None):
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=request.remote_addr,
        reason=reason
    )
    db.session.add(log)
    db.session.commit()


def recalculate_progress(user_id, course_id):
    """Recalculate a student's progress % for a course based on viewed modules."""
    total_modules = Module.query.filter_by(course_id=course_id).count()
    if total_modules == 0:
        return
    viewed_module_ids = {
        mv.module_id for mv in ModuleView.query.filter_by(user_id=user_id).all()
    }
    course_module_ids = {
        m.id for m in Module.query.filter_by(course_id=course_id).all()
    }
    viewed_in_course = len(viewed_module_ids & course_module_ids)
    progress_pct = int((viewed_in_course / total_modules) * 100)

    enrollment = Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
    if enrollment:
        enrollment.progress = progress_pct
        db.session.commit()


# ─── Static Asset Route ───────────────────────────────────────────────────────

@app.route('/styles.css')
def styles():
    return app.send_static_file('styles.css')


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['role'] = user.role
            log_action(user.id, "User Login")
            return redirect(url_for('dashboard'))
        return render_template('login.html', error="Invalid email or password.")
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        if not name or not email or not password:
            return render_template('register.html', error="All fields are required.")
        if password != confirm:
            return render_template('register.html', error="Passwords do not match.")
        if len(password) < 8:
            return render_template('register.html', error="Password must be at least 8 characters.")
        if User.query.filter_by(email=email).first():
            return render_template('register.html', error="An account with that email already exists.")

        hashed = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(name=name, email=email, password_hash=hashed, role='student')
        db.session.add(new_user)
        db.session.commit()
        log_action(new_user.id, "Student Self-Registration")
        flash('Account created! Please sign in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        log_action(user_id, "User Logout")
    session.clear()
    return redirect(url_for('login'))


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD (role-based routing)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/')
@app.route('/index.html')
@login_required
def dashboard():
    role = session.get('role')

    if role == 'sys_admin':
        stats = {
            'total_users': User.query.count(),
            'total_courses': Course.query.count(),
            'audit_logs': AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()
        }
        recent_users = User.query.order_by(User.id.desc()).limit(10).all()
        platform_announcements = Announcement.query.filter_by(course_id=None).order_by(
            Announcement.created_at.desc()).limit(5).all()
        return render_template('sys_admin_dashboard.html', stats=stats,
                               recent_users=recent_users,
                               announcements=platform_announcements)

    elif role == 'exam_admin':
        exam_stats = {
            'active_policies': ExamPolicy.query.count(),
            'scheduled_sessions': ExamSession.query.count(),
            'pending_reviews': ExamAttempt.query.filter_by(integrity_status='pending').count()
        }
        return render_template('exam_admin_dashboard.html', stats=exam_stats)

    elif role == 'instructor':
        courses = Course.query.filter_by(instructor_id=session['user_id']).all()
        pending_submissions = (Submission.query
                               .join(Assignment, Submission.assignment_id == Assignment.id)
                               .join(Course, Assignment.course_id == Course.id)
                               .filter(Course.instructor_id == session['user_id'])
                               .filter(Submission.grade == None)
                               .count())
        return render_template('instructor_dashboard.html', courses=courses,
                               pending_submissions=pending_submissions)

    else:  # student
        enrollments = Enrollment.query.filter_by(user_id=session['user_id']).all()
        # Gather announcements: platform-wide + course-specific for enrolled courses
        enrolled_course_ids = [e.course_id for e in enrollments]
        announcements = (Announcement.query
                         .filter(
                             (Announcement.course_id == None) |
                             (Announcement.course_id.in_(enrolled_course_ids))
                         )
                         .order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc())
                         .limit(5).all())
        return render_template('index.html', user=session['user_name'],
                               enrollments=enrollments, announcements=announcements)


# ═══════════════════════════════════════════════════════════════════════════════
# COURSES & CONTENT
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/courses.html')
@login_required
def courses():
    enrollments = Enrollment.query.filter_by(user_id=session['user_id']).all()
    return render_template('courses.html', user=session['user_name'], enrollments=enrollments)


@app.route('/course-detail.html')
@login_required
def course_detail():
    course_id = request.args.get('id', type=int)
    mod_id    = request.args.get('mod', type=int)   # which module to display

    course = Course.query.get_or_404(course_id) if course_id else Course.query.first()
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('courses'))

    # Security: students may only view courses they're enrolled in
    if session.get('role') == 'student':
        enrollment = Enrollment.query.filter_by(
            user_id=session['user_id'], course_id=course.id).first()
        if not enrollment:
            flash('You are not enrolled in this course.', 'danger')
            return redirect(url_for('courses'))

    # Determine active module
    active_module = None
    if mod_id:
        active_module = Module.query.get(mod_id)
        # Mark this module as viewed for progress tracking
        if session.get('role') == 'student' and active_module:
            already_viewed = ModuleView.query.filter_by(
                user_id=session['user_id'], module_id=mod_id).first()
            if not already_viewed:
                mv = ModuleView(user_id=session['user_id'], module_id=mod_id)
                db.session.add(mv)
                db.session.commit()
                recalculate_progress(session['user_id'], course.id)
    elif course.modules:
        active_module = course.modules[0]

    # Which assignments has this student already submitted?
    submitted_assignment_ids = set()
    if session.get('role') == 'student':
        subs = Submission.query.filter_by(student_id=session['user_id']).all()
        submitted_assignment_ids = {s.assignment_id for s in subs}

    announcements = (Announcement.query
                     .filter_by(course_id=course.id)
                     .order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc())
                     .all())

    return render_template('course-detail.html',
                           course=course,
                           active_module=active_module,
                           submitted_ids=submitted_assignment_ids,
                           announcements=announcements,
                           user=session['user_name'])


# ─── Instructor: Create Course ────────────────────────────────────────────────

@app.route('/instructor/create_course', methods=['GET', 'POST'])
@role_required('instructor', 'sys_admin')
def create_course():
    if request.method == 'POST':
        code  = request.form.get('code', '').strip().upper()
        title = request.form.get('title', '').strip()
        if not code or not title:
            flash('Course code and title are required.', 'danger')
            return render_template('create_course.html')
        if Course.query.filter_by(code=code).first():
            flash(f'A course with code {code} already exists.', 'danger')
            return render_template('create_course.html')
        new_course = Course(code=code, title=title, instructor_id=session['user_id'])
        db.session.add(new_course)
        db.session.commit()
        log_action(session['user_id'], f"Created Course: {code}", "Course", new_course.id)
        flash(f'Course {code} created successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('create_course.html')


# ─── Instructor: Add Module ───────────────────────────────────────────────────

@app.route('/instructor/add_module/<int:course_id>', methods=['GET', 'POST'])
@role_required('instructor', 'sys_admin')
def add_module(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        title        = request.form.get('title', '').strip()
        content_type = request.form.get('content_type', 'text')
        content_url  = request.form.get('content_url', '').strip()
        content_text = request.form.get('content_text', '').strip()

        # Store text content in content_url field if type is text
        if content_type == 'text':
            content_url = content_text

        mod = Module(course_id=course_id, title=title,
                     content_type=content_type, content_url=content_url)
        db.session.add(mod)
        db.session.commit()
        log_action(session['user_id'], f"Added Module: {title}", "Module", mod.id)
        flash(f'Module "{title}" added.', 'success')
        return redirect(url_for('course_detail', id=course_id))
    return render_template('add_module.html', course=course)


# ─── Instructor: Add Assignment ───────────────────────────────────────────────

@app.route('/instructor/add_assignment/<int:course_id>', methods=['GET', 'POST'])
@role_required('instructor', 'sys_admin')
def add_assignment(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        due_date_str = request.form.get('due_date', '')
        points      = int(request.form.get('points', 100))

        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                pass

        assignment = Assignment(course_id=course_id, title=title,
                                description=description, due_date=due_date,
                                points=points)
        db.session.add(assignment)
        db.session.commit()
        log_action(session['user_id'], f"Created Assignment: {title}", "Assignment", assignment.id)
        flash(f'Assignment "{title}" created.', 'success')
        return redirect(url_for('course_detail', id=course_id))
    return render_template('add_assignment.html', course=course)


# ─── Student: View Assignment Detail & Submit ─────────────────────────────────

@app.route('/assignment/<int:assignment_id>', methods=['GET'])
@login_required
def assignment_detail(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    course     = Course.query.get(assignment.course_id)

    existing_submission = None
    if session.get('role') == 'student':
        existing_submission = Submission.query.filter_by(
            assignment_id=assignment_id,
            student_id=session['user_id']
        ).first()

    return render_template('assignment_detail.html',
                           assignment=assignment,
                           course=course,
                           submission=existing_submission)


@app.route('/assignment/<int:assignment_id>/submit', methods=['POST'])
@role_required('student')
def submit_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)

    # Check for existing submission — no resubmissions
    existing = Submission.query.filter_by(
        assignment_id=assignment_id, student_id=session['user_id']).first()
    if existing:
        flash('You have already submitted this assignment.', 'warning')
        return redirect(url_for('assignment_detail', assignment_id=assignment_id))

    file_path = None
    if 'file' in request.files and request.files['file'].filename:
        f = request.files['file']
        if not allowed_file(f.filename):
            flash('File type not allowed. Please upload PDF, DOCX, TXT, or ZIP.', 'danger')
            return redirect(url_for('assignment_detail', assignment_id=assignment_id))
        filename = secure_filename(f.filename)
        save_dir = os.path.join(UPLOAD_FOLDER, 'assignments')
        os.makedirs(save_dir, exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_name = f"{session['user_id']}_{ts}_{filename}"
        full_path   = os.path.join(save_dir, unique_name)
        f.save(full_path)
        file_path = f"assignments/{unique_name}"

    sub = Submission(
        assignment_id=assignment_id,
        student_id=session['user_id'],
        file_path=file_path
    )
    db.session.add(sub)
    db.session.commit()
    log_action(session['user_id'], f"Submitted Assignment ID {assignment_id}", "Submission", sub.id)

    # Update progress after submission
    recalculate_progress(session['user_id'], assignment.course_id)

    flash('Assignment submitted successfully! 🎉', 'success')
    return redirect(url_for('assignment_detail', assignment_id=assignment_id))


# ─── Instructor: Gradebook ────────────────────────────────────────────────────

@app.route('/instructor/gradebook/<int:assignment_id>')
@role_required('instructor', 'sys_admin')
def gradebook(assignment_id):
    assignment  = Assignment.query.get_or_404(assignment_id)
    course      = Course.query.get(assignment.course_id)
    submissions = (Submission.query
                   .filter_by(assignment_id=assignment_id)
                   .join(User, Submission.student_id == User.id)
                   .add_entity(User)
                   .all())
    return render_template('gradebook.html',
                           assignment=assignment,
                           course=course,
                           submissions=submissions)


@app.route('/instructor/grade_submission/<int:submission_id>', methods=['POST'])
@role_required('instructor', 'sys_admin')
def grade_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    grade      = request.form.get('grade', type=float)
    feedback   = request.form.get('feedback', '').strip()

    if grade is None or grade < 0:
        flash('Please enter a valid grade.', 'danger')
        return redirect(url_for('gradebook', assignment_id=submission.assignment_id))

    submission.grade    = grade
    submission.feedback = feedback
    db.session.commit()

    # Update the student's enrollment grade to the average of all graded submissions
    assignment = Assignment.query.get(submission.assignment_id)
    all_submissions = Submission.query.filter_by(
        student_id=submission.student_id).join(
        Assignment, Submission.assignment_id == Assignment.id).filter(
        Assignment.course_id == assignment.course_id,
        Submission.grade != None).all()

    if all_submissions:
        avg = sum(s.grade for s in all_submissions) / len(all_submissions)
        enrollment = Enrollment.query.filter_by(
            user_id=submission.student_id, course_id=assignment.course_id).first()
        if enrollment:
            enrollment.grade = round(avg, 1)
            db.session.commit()

    log_action(session['user_id'], f"Graded Submission ID {submission_id} — {grade}pts",
               "Submission", submission_id)
    flash(f'Grade saved: {grade} pts', 'success')
    return redirect(url_for('gradebook', assignment_id=submission.assignment_id))


# ═══════════════════════════════════════════════════════════════════════════════
# ANNOUNCEMENTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/announcements/create', methods=['GET', 'POST'])
@role_required('instructor', 'sys_admin', 'exam_admin')
def create_announcement():
    role = session.get('role')
    # Instructors can only post to their own courses
    if role == 'instructor':
        my_courses = Course.query.filter_by(instructor_id=session['user_id']).all()
    else:
        my_courses = Course.query.all()

    if request.method == 'POST':
        title     = request.form.get('title', '').strip()
        body      = request.form.get('body', '').strip()
        course_id = request.form.get('course_id') or None
        is_pinned = bool(request.form.get('is_pinned'))

        if course_id:
            course_id = int(course_id)

        ann = Announcement(
            title=title, body=body,
            course_id=course_id,
            author_id=session['user_id'],
            is_pinned=is_pinned
        )
        db.session.add(ann)
        db.session.commit()
        log_action(session['user_id'], f"Posted Announcement: {title}", "Announcement", ann.id)
        flash('Announcement posted!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('create_announcement.html', courses=my_courses)


# ═══════════════════════════════════════════════════════════════════════════════
# QUIZ / EXAM
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/instructor/create_quiz', methods=['GET', 'POST'])
@role_required('instructor')
def create_quiz():
    if request.method == 'POST':
        title  = request.form.get('title')
        q_text = request.form.get('question_text')
        q_type = request.form.get('q_type', 'multiple_choice')
        points = int(request.form.get('points', 10))

        new_exam = ExamSession(title=title, start_time=datetime.utcnow(), end_time=datetime.utcnow())
        db.session.add(new_exam)
        db.session.flush()

        q = Question(session_id=new_exam.id, text=q_text, q_type=q_type, points=points)
        db.session.add(q)
        db.session.flush()

        if q_type == 'multiple_choice':
            for i in range(1, 5):
                choice_text = request.form.get(f'choice_{i}')
                if choice_text:
                    c = Choice(question_id=q.id, text=choice_text, is_correct=(i == 1))
                    db.session.add(c)

        db.session.commit()
        flash('Quiz created successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('create_quiz.html')


# ═══════════════════════════════════════════════════════════════════════════════
# EXAM SHIELD
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/log_flag', methods=['POST'])
@login_required
def log_flag():
    data = request.json
    flag = IntegrityFlag(
        attempt_id=data.get('attempt_id'),
        flag_type=data.get('flag_type'),
        severity=data.get('severity', 'medium')
    )
    db.session.add(flag)
    db.session.commit()
    return jsonify({"status": "logged"}), 200


@app.route('/api/upload_identity', methods=['POST'])
@login_required
def upload_identity():
    uid = session['user_id']
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    upload_dir = os.path.join(UPLOAD_FOLDER, 'identity')
    os.makedirs(upload_dir, exist_ok=True)

    photo_url = ""
    video_url = ""

    photo_data = request.form.get('photo')
    if photo_data:
        import base64
        try:
            head, data = photo_data.split(',', 1)
            file_ext = head.split(';')[0].split('/')[1]
            fname = f"{uid}_{timestamp}.{file_ext}"
            with open(os.path.join(upload_dir, fname), "wb") as f:
                f.write(base64.b64decode(data))
            photo_url = f"identity/{fname}"
        except Exception:
            pass

    if 'video' in request.files:
        video = request.files['video']
        fname = f"{uid}_{timestamp}.webm"
        video.save(os.path.join(upload_dir, fname))
        video_url = f"identity/{fname}"

    verify_record = IdentityVerification(
        user_id=uid, photo_url=photo_url,
        video_url=video_url, status='verified'
    )
    db.session.add(verify_record)
    db.session.commit()
    log_action(uid, f"Identity Verified (Record {verify_record.id})", "Verification", verify_record.id)
    return jsonify({"status": "ok", "record_id": verify_record.id}), 200


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/admin/add_user', methods=['POST'])
@role_required('sys_admin', 'exam_admin')
def admin_add_user():
    name     = request.form.get('name', '').strip()
    email    = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    role     = request.form.get('role', 'student')
    reason   = request.form.get('reason', 'Account provisioning')

    if User.query.filter_by(email=email).first():
        flash(f'User {email} already exists.', 'danger')
        return redirect(url_for('dashboard'))

    hashed   = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(name=name, email=email, password_hash=hashed, role=role)
    db.session.add(new_user)
    db.session.commit()
    log_action(session['user_id'], f"Provisioned User: {email} ({role})", "User", new_user.id, reason)
    flash(f'User {name} ({role}) created successfully.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/admin/enroll_student', methods=['POST'])
@role_required('sys_admin', 'instructor')
def enroll_student():
    student_id = request.form.get('student_id', type=int)
    course_id  = request.form.get('course_id', type=int)
    if not student_id or not course_id:
        flash('Student and course are required.', 'danger')
        return redirect(url_for('dashboard'))
    if Enrollment.query.filter_by(user_id=student_id, course_id=course_id).first():
        flash('Student is already enrolled.', 'warning')
        return redirect(url_for('dashboard'))
    enrollment = Enrollment(user_id=student_id, course_id=course_id)
    db.session.add(enrollment)
    db.session.commit()
    log_action(session['user_id'], f"Enrolled Student {student_id} in Course {course_id}",
               "Enrollment", enrollment.id)
    flash('Student enrolled successfully.', 'success')
    return redirect(url_for('dashboard'))








# ═══════════════════════════════════════════════════════════════════════════════
# SIMPLE PROTECTED PAGES
# ═══════════════════════════════════════════════════════════════════════════════




@app.route('/shield-check.html')
@login_required
def shield_check():
    return render_template('shield-check.html')


@app.route('/shield-verify.html')
@login_required
def shield_verify():
    return render_template('shield-verify.html')


@app.route('/quiz-interface.html')
@login_required
def quiz_interface():
    questions = Question.query.all()
    return render_template('quiz-interface.html', questions=questions)


@app.route('/support.html')
@login_required
def support():
    return render_template('support.html')


@app.route('/settings.html')
@login_required
def settings():
    user = User.query.get(session['user_id'])
    return render_template('settings.html', user=user)


@app.route('/calendar.html')
@login_required
def calendar():
    return render_template('calendar.html')


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — TEST MODULE
# ═══════════════════════════════════════════════════════════════════════════════
import json


# ─── Exam Admin: Session Scheduling ──────────────────────────────────────────

@app.route('/exam_admin/sessions')
@role_required('exam_admin', 'sys_admin')
def exam_sessions():
    sessions = ExamSession.query.order_by(ExamSession.start_time.desc()).all()
    courses  = Course.query.all()
    policies = ExamPolicy.query.all()
    pending  = ExamAttempt.query.filter_by(integrity_status='pending').count()
    stats = {
        'active_policies': ExamPolicy.query.count(),
        'scheduled_sessions': ExamSession.query.filter_by(status='scheduled').count(),
        'live_sessions': ExamSession.query.filter_by(status='live').count(),
        'pending_reviews': pending,
    }
    return render_template('exam_admin_dashboard.html',
                           sessions=sessions, courses=courses,
                           policies=policies, stats=stats)


@app.route('/exam_admin/schedule_exam', methods=['GET', 'POST'])
@role_required('exam_admin', 'sys_admin')
def schedule_exam():
    courses  = Course.query.all()
    policies = ExamPolicy.query.filter(ExamPolicy.status != 'draft').all()
    if request.method == 'POST':
        title         = request.form.get('title', '').strip()
        course_id     = request.form.get('course_id') or None
        policy_id     = request.form.get('policy_id') or None
        start_str     = request.form.get('start_time', '')
        end_str       = request.form.get('end_time', '')
        duration_mins = int(request.form.get('duration_mins', 60))
        is_placement  = bool(request.form.get('is_placement'))

        try:
            start_time = datetime.strptime(start_str, '%Y-%m-%dT%H:%M')
            end_time   = datetime.strptime(end_str,   '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date/time format.', 'danger')
            return render_template('schedule_exam.html', courses=courses, policies=policies)

        sess = ExamSession(
            title=title,
            course_id=int(course_id) if course_id else None,
            policy_id=int(policy_id) if policy_id else None,
            start_time=start_time,
            end_time=end_time,
            duration_mins=duration_mins,
            is_placement=is_placement,
            status='scheduled'
        )
        db.session.add(sess)
        db.session.commit()
        log_action(session['user_id'], f"Scheduled Exam: {title}", "ExamSession", sess.id)
        flash(f'Exam "{title}" scheduled successfully.', 'success')
        return redirect(url_for('exam_sessions'))
    return render_template('schedule_exam.html', courses=courses, policies=policies)


@app.route('/exam_admin/session/<int:session_id>/activate', methods=['POST'])
@role_required('exam_admin', 'sys_admin')
def activate_session(session_id):
    sess = ExamSession.query.get_or_404(session_id)
    sess.status = 'live'
    db.session.commit()
    log_action(session['user_id'], f"Activated Exam Session: {sess.title}", "ExamSession", session_id)
    flash(f'Session "{sess.title}" is now LIVE.', 'success')
    return redirect(url_for('exam_sessions'))


@app.route('/exam_admin/session/<int:session_id>/end', methods=['POST'])
@role_required('exam_admin', 'sys_admin')
def end_session(session_id):
    sess = ExamSession.query.get_or_404(session_id)
    sess.status = 'ended'
    db.session.commit()
    log_action(session['user_id'], f"Ended Exam Session: {sess.title}", "ExamSession", session_id)
    flash(f'Session "{sess.title}" has ended.', 'success')
    return redirect(url_for('exam_sessions'))


# ─── Exam Admin: Policy CRUD ──────────────────────────────────────────────────

@app.route('/admin/policies')
@role_required('exam_admin', 'sys_admin')
def manage_policies():
    policies = ExamPolicy.query.order_by(ExamPolicy.created_at.desc()).all()
    return render_template('admin_policies.html', policies=policies)


@app.route('/admin/policies/create', methods=['GET', 'POST'])
@role_required('exam_admin', 'sys_admin')
def create_policy():
    if request.method == 'POST':
        name                = request.form.get('name', '').strip()
        identity_tier       = int(request.form.get('identity_tier', 1))
        secure_mode         = bool(request.form.get('secure_mode'))
        proctoring_level    = request.form.get('proctoring_level', 'full')
        violation_threshold = int(request.form.get('violation_threshold', 3))
        rejoin_grace_mins   = int(request.form.get('rejoin_grace_mins', 5))

        policy = ExamPolicy(
            name=name,
            identity_tier=identity_tier,
            secure_mode=secure_mode,
            proctoring_level=proctoring_level,
            violation_threshold=violation_threshold,
            rejoin_grace_mins=rejoin_grace_mins,
            created_by=session['user_id']
        )
        db.session.add(policy)
        db.session.commit()
        log_action(session['user_id'], f"Created Policy: {name}", "ExamPolicy", policy.id)
        flash(f'Policy "{name}" created.', 'success')
        return redirect(url_for('manage_policies'))
    return render_template('create_policy.html')


@app.route('/admin/policies/<int:policy_id>/approve', methods=['POST'])
@role_required('exam_admin', 'sys_admin')
def approve_policy(policy_id):
    policy = ExamPolicy.query.get_or_404(policy_id)
    policy.status = 'approved'
    policy.version += 1
    db.session.commit()
    log_action(session['user_id'], f"Approved & Locked Policy: {policy.name}", "ExamPolicy", policy_id)
    flash(f'Policy "{policy.name}" approved and locked.', 'success')
    return redirect(url_for('manage_policies'))


@app.route('/admin/policies/<int:policy_id>/delete', methods=['POST'])
@role_required('exam_admin', 'sys_admin')
def delete_policy(policy_id):
    policy = ExamPolicy.query.get_or_404(policy_id)
    if policy.status == 'approved':
        flash('Locked policies cannot be deleted.', 'danger')
        return redirect(url_for('manage_policies'))
    name = policy.name
    db.session.delete(policy)
    db.session.commit()
    log_action(session['user_id'], f"Deleted Policy: {name}", "ExamPolicy", policy_id)
    flash(f'Policy "{name}" deleted.', 'success')
    return redirect(url_for('manage_policies'))


# ─── Student: Exam Entry & Taking ─────────────────────────────────────────────

@app.route('/exam/<int:session_id>/start', methods=['GET', 'POST'])
@role_required('student')
def start_exam(session_id):
    """Entry point: student confirms identity, then creates an ExamAttempt."""
    exam_sess = ExamSession.query.get_or_404(session_id)

    if exam_sess.status != 'live':
        flash('This exam is not currently active.', 'warning')
        return redirect(url_for('exams'))

    # Prevent double-attempt
    existing = ExamAttempt.query.filter_by(
        session_id=session_id, student_id=session['user_id']).first()
    if existing:
        if existing.status == 'submitted':
            return redirect(url_for('exam_result', attempt_id=existing.id))
        return redirect(url_for('take_exam', attempt_id=existing.id))

    # Create attempt
    max_pts = sum(q.points for q in exam_sess.questions)
    attempt = ExamAttempt(
        session_id=session_id,
        student_id=session['user_id'],
        status='in_progress',
        max_score=max_pts
    )
    db.session.add(attempt)
    db.session.commit()
    log_action(session['user_id'], f"Started Exam: {exam_sess.title}", "ExamAttempt", attempt.id)
    return redirect(url_for('take_exam', attempt_id=attempt.id))


@app.route('/exam/take/<int:attempt_id>')
@role_required('student')
def take_exam(attempt_id):
    attempt   = ExamAttempt.query.get_or_404(attempt_id)
    exam_sess = ExamSession.query.get(attempt.session_id)

    if attempt.student_id != session['user_id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    if attempt.status == 'submitted':
        return redirect(url_for('exam_result', attempt_id=attempt_id))

    questions = exam_sess.questions if exam_sess else []
    # Parse existing answers
    saved_answers = json.loads(attempt.answers_json) if attempt.answers_json else {}

    # Remaining seconds
    elapsed  = (datetime.utcnow() - attempt.started_at).total_seconds()
    remaining_secs = max(0, exam_sess.duration_mins * 60 - int(elapsed))

    return render_template('quiz-interface.html',
                           attempt=attempt,
                           exam_sess=exam_sess,
                           questions=questions,
                           saved_answers=saved_answers,
                           remaining_secs=remaining_secs)


@app.route('/api/save_answer', methods=['POST'])
@role_required('student')
def save_answer():
    """Auto-save a single answer (called by JS on every selection)."""
    data       = request.json
    attempt_id = data.get('attempt_id')
    q_id       = str(data.get('q_id'))
    answer     = data.get('answer', '')

    attempt = ExamAttempt.query.get(attempt_id)
    if not attempt or attempt.student_id != session['user_id']:
        return jsonify({'error': 'unauthorized'}), 403

    answers = json.loads(attempt.answers_json) if attempt.answers_json else {}
    answers[q_id] = answer
    attempt.answers_json = json.dumps(answers)
    attempt.status = 'in_progress'
    db.session.commit()
    return jsonify({'saved': True}), 200


@app.route('/exam/submit/<int:attempt_id>', methods=['POST'])
@role_required('student')
def submit_exam(attempt_id):
    attempt   = ExamAttempt.query.get_or_404(attempt_id)
    exam_sess = ExamSession.query.get(attempt.session_id)

    if attempt.student_id != session['user_id']:
        return 'Unauthorized', 403
    if attempt.status == 'submitted':
        return redirect(url_for('exam_result', attempt_id=attempt_id))

    # Merge any last-submitted answers from form
    answers = json.loads(attempt.answers_json) if attempt.answers_json else {}
    for key, val in request.form.items():
        if key.startswith('q_'):
            q_id = key[2:]  # strip 'q_'
            answers[q_id] = val
    attempt.answers_json = json.dumps(answers)

    # Auto-score MCQ questions
    total_score = 0
    max_score   = 0
    for q in exam_sess.questions:
        max_score += q.points
        if q.q_type == 'multiple_choice':
            selected_choice_id = answers.get(str(q.id), '')
            if selected_choice_id:
                choice = Choice.query.get(int(selected_choice_id)) if selected_choice_id.isdigit() else None
                if choice and choice.is_correct:
                    total_score += q.points

    attempt.score        = total_score
    attempt.max_score    = max_score
    attempt.status       = 'submitted'
    attempt.submitted_at = datetime.utcnow()
    db.session.commit()

    log_action(session['user_id'],
               f"Submitted Exam: {exam_sess.title} — Score {total_score}/{max_score}",
               "ExamAttempt", attempt_id)
    flash('Exam submitted successfully!', 'success')
    return redirect(url_for('exam_result', attempt_id=attempt_id))


@app.route('/exam/result/<int:attempt_id>')
@login_required
def exam_result(attempt_id):
    attempt   = ExamAttempt.query.get_or_404(attempt_id)
    exam_sess = ExamSession.query.get(attempt.session_id)
    questions = exam_sess.questions if exam_sess else []
    answers   = json.loads(attempt.answers_json) if attempt.answers_json else {}

    # Build per-question result rows
    results = []
    for q in questions:
        selected_id  = answers.get(str(q.id), '')
        selected_txt = '—'
        is_correct   = None
        correct_txt  = ''
        if q.q_type == 'multiple_choice':
            correct_choice = next((c for c in q.choices if c.is_correct), None)
            correct_txt    = correct_choice.text if correct_choice else ''
            if selected_id and selected_id.isdigit():
                sel_choice   = Choice.query.get(int(selected_id))
                selected_txt = sel_choice.text if sel_choice else '—'
                is_correct   = sel_choice.is_correct if sel_choice else False
        else:
            selected_txt = answers.get(str(q.id), '—')
        results.append({
            'question': q,
            'selected': selected_txt,
            'correct_answer': correct_txt,
            'is_correct': is_correct,
        })

    percentage = round((attempt.score / attempt.max_score * 100), 1) if attempt.max_score else 0
    return render_template('exam_result.html',
                           attempt=attempt,
                           exam_sess=exam_sess,
                           results=results,
                           percentage=percentage)


# ─── Proctor: Live Dashboard ──────────────────────────────────────────────────

@app.route('/proctor/dashboard/<int:session_id>')
@role_required('exam_admin', 'sys_admin', 'proctor')
def proctor_dashboard(session_id):
    exam_sess   = ExamSession.query.get_or_404(session_id)
    attempts    = ExamAttempt.query.filter_by(session_id=session_id).all()
    all_attempt_ids = [a.id for a in attempts]
    flags = []
    if all_attempt_ids:
        flags = (IntegrityFlag.query
                 .filter(IntegrityFlag.attempt_id.in_(all_attempt_ids))
                 .order_by(IntegrityFlag.timestamp.desc()).all())
    return render_template('proctor_dashboard.html',
                           exam_sess=exam_sess,
                           attempts=attempts,
                           flags=flags)


# ─── Exam Admin: Post-Exam Integrity Review ───────────────────────────────────

@app.route('/admin/integrity_review')
@role_required('exam_admin', 'sys_admin')
def integrity_review():
    verifications = IdentityVerification.query.order_by(IdentityVerification.timestamp.desc()).all()
    # Attempts to review (submitted but not yet certified)
    pending_attempts = (ExamAttempt.query
                        .filter_by(status='submitted', integrity_status='pending')
                        .all())
    all_flags = IntegrityFlag.query.order_by(IntegrityFlag.timestamp.desc()).all()
    sessions  = ExamSession.query.all()
    return render_template('integrity_review.html',
                           verifications=verifications,
                           flags=all_flags,
                           pending_attempts=pending_attempts,
                           sessions=sessions)


@app.route('/admin/review_attempt/<int:attempt_id>', methods=['POST'])
@role_required('exam_admin', 'sys_admin')
def review_attempt(attempt_id):
    attempt = ExamAttempt.query.get_or_404(attempt_id)
    action  = request.form.get('action')  # 'certify', 'invalidate', 'appeal'
    reason  = request.form.get('reason', '').strip()

    if action == 'certify':
        attempt.integrity_status = 'certified'
    elif action == 'invalidate':
        attempt.integrity_status = 'invalidated'
        attempt.status = 'flagged'
    elif action == 'appeal':
        attempt.integrity_status = 'appealed'
    else:
        flash('Unknown action.', 'danger')
        return redirect(url_for('integrity_review'))

    db.session.commit()
    log_action(session['user_id'],
               f"Attempt #{attempt_id} → {action.upper()} — {reason}",
               "ExamAttempt", attempt_id, reason)
    flash(f'Attempt #{attempt_id} marked as {action.upper()}.', 'success')
    return redirect(url_for('integrity_review'))


# ─── Placement Results ────────────────────────────────────────────────────────

@app.route('/admin/placement_results')
@role_required('sys_admin', 'exam_admin')
def placement_results():
    placement_sessions = ExamSession.query.filter_by(is_placement=True).all()
    session_ids = [s.id for s in placement_sessions]
    attempts = []
    if session_ids:
        attempts = (ExamAttempt.query
                    .filter(ExamAttempt.session_id.in_(session_ids),
                            ExamAttempt.status == 'submitted')
                    .all())
    return render_template('placement_results.html',
                           sessions=placement_sessions,
                           attempts=attempts)


# ─── Student: Exam Portal (updated) ──────────────────────────────────────────

@app.route('/exams.html')
@login_required
def exams():
    user_id = session['user_id']
    # All live and scheduled sessions
    live_sessions      = ExamSession.query.filter_by(status='live').all()
    scheduled_sessions = ExamSession.query.filter_by(status='scheduled').all()

    # Previously attempted exams
    past_attempts = (ExamAttempt.query
                     .filter_by(student_id=user_id, status='submitted')
                     .all())
    attempt_session_ids = {a.session_id: a for a in past_attempts}

    return render_template('exams.html',
                           live_sessions=live_sessions,
                           scheduled_sessions=scheduled_sessions,
                           past_attempts=past_attempts,
                           attempt_map=attempt_session_ids)


# ─── Run ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=8080)
