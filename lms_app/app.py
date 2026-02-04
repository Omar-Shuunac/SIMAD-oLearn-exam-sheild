from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'simad_olearn_secure_key'

# Database Configuration - New Neon PostgreSQL instance
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_fXqno0th9eLi@ep-square-pine-aijrixgc-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Fix for "SSL connection closed unexpectedly" (common with Neon/Serverless)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 280,   # Recycle connections before they time out (Neon default is ~300s)
    "pool_pre_ping": True, # Check connection health before using it
}

from models import db, User, Course, ExamPolicy, ExamSession, AuditLog, ExamAttempt, IntegrityFlag, Question, Choice, Enrollment, IdentityVerification
db.init_app(app)

# --- Helper: Audit Logging ---
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

# --- Exam Shield API ---

@app.route('/api/log_flag', methods=['POST'])
def log_flag():
    if 'user_id' not in session: return "Unauthorized", 401
    
    data = request.json
    attempt_id = data.get('attempt_id')
    flag_type = data.get('flag_type')
    severity = data.get('severity', 'medium')
    
    flag = IntegrityFlag(
        attempt_id=attempt_id,
        flag_type=flag_type,
        severity=severity
    )
    db.session.add(flag)
    db.session.commit()
    return {"status": "shared"}, 200

@app.route('/api/upload_identity', methods=['POST'])
def upload_identity():
    if 'user_id' not in session: return "Unauthorized", 401
    
    uid = session['user_id']
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    upload_dir = 'lms_app/uploads/identity'
    
    # Save Photo if exists (base64 from canvas usually via request.form)
    photo_data = request.form.get('photo')
    if photo_data:
        import base64
        try:
            head, data = photo_data.split(',', 1)
            file_ext = head.split(';')[0].split('/')[1]
            with open(f"{upload_dir}/{uid}_{timestamp}.{file_ext}", "wb") as f:
                f.write(base64.b64decode(data))
        except: pass

    # Save Video if exists (blob via request.files)
    video_url = ""
    photo_url = ""
    if photo_data: photo_url = f"{upload_dir}/{uid}_{timestamp}.jpeg"
    if 'video' in request.files:
        video = request.files['video']
        video_url = f"{upload_dir}/{uid}_{timestamp}.webm"
        video.save(video_url)

    # Save Record to Neon DB (NEW)
    verify_record = IdentityVerification(
        user_id=uid,
        photo_url=photo_url,
        video_url=video_url,
        status='verified'
    )
    db.session.add(verify_record)
    db.session.commit()

    log_action(uid, f"Identity Verification Captured (Record ID: {verify_record.id})", "Verification", verify_record.id)
    return {"status": "identity_stored_locally_and_mapped_in_neon"}, 200

# --- Routes ---

@app.route('/styles.css')
def styles():
    return app.send_static_file('styles.css')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.password_hash == password:
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['role'] = user.role
            log_action(user.id, "User Login")
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@app.route('/index.html')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    role = session.get('role')
    if role == 'sys_admin':
        stats = {
            'total_users': User.query.count(),
            'total_courses': Course.query.count(),
            'audit_logs': AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()
        }
        recent_users = User.query.order_by(User.id.desc()).limit(5).all()
        return render_template('sys_admin_dashboard.html', stats=stats, recent_users=recent_users)
    elif role == 'exam_admin':
        exam_stats = {
            'active_policies': ExamPolicy.query.count(),
            'scheduled_sessions': ExamSession.query.count(),
            'pending_reviews': ExamAttempt.query.filter_by(integrity_status='pending').count()
        }
        return render_template('exam_admin_dashboard.html', stats=exam_stats)
    elif role == 'instructor':
        courses = Course.query.filter_by(instructor_id=session['user_id']).all()
        return render_template('instructor_dashboard.html', courses=courses)
    else:
        enrollments = Enrollment.query.filter_by(user_id=session['user_id']).all()
        return render_template('index.html', user=session['user_name'], enrollments=enrollments)

# --- Instructor: Quiz Creation ---

@app.route('/instructor/create_quiz', methods=['GET', 'POST'])
def create_quiz():
    if session.get('role') != 'instructor': return "Unauthorized", 403
    if request.method == 'POST':
        title = request.form.get('title')
        q_text = request.form.get('question_text')
        q_type = request.form.get('q_type', 'multiple_choice')
        points = int(request.form.get('points', 10))
        
        # 1. Create session
        new_exam = ExamSession(title=title, start_time=datetime.utcnow(), end_time=datetime.utcnow())
        db.session.add(new_exam); db.session.flush()
        
        # 2. Add question with type logic
        q = Question(session_id=new_exam.id, text=q_text, q_type=q_type, points=points)
        db.session.add(q)
        db.session.flush()

        # 3. Add Choices if MCQ
        if q_type == 'multiple_choice':
            for i in range(1, 4):
                choice_text = request.form.get(f'choice_{i}')
                if choice_text:
                    c = Choice(question_id=q.id, text=choice_text, is_correct=(i==1))
                    db.session.add(c)
        
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('create_quiz.html')

# --- Admin: Integrity Review ---

@app.route('/admin/integrity_review')
def integrity_review():
    if session.get('role') != 'exam_admin': return "Unauthorized", 403
    
    # Fetch Identity records and join with users to show names
    verifications = IdentityVerification.query.order_by(IdentityVerification.timestamp.desc()).all()
    # Fetch general flags
    flags = IntegrityFlag.query.all()
    
    return render_template('integrity_review.html', verifications=verifications, flags=flags)

# --- Admin: Policies ---

@app.route('/admin/policies')
def manage_policies():
    if session.get('role') != 'exam_admin': return "Unauthorized", 403
    policies = ExamPolicy.query.all()
    return render_template('admin_policies.html', policies=policies)

# --- Admin: IAM ---

@app.route('/admin/add_user', methods=['POST'])
def admin_add_user():
    if session.get('role') not in ['sys_admin', 'exam_admin']: return "Unauthorized", 403
    name = request.form.get('name'); email = request.form.get('email')
    password = request.form.get('password'); role = request.form.get('role')
    reason = request.form.get('reason', 'Account rollout')
    if User.query.filter_by(email=email).first(): return "Exists", 400
    new_user = User(name=name, email=email, password_hash=password, role=role)
    db.session.add(new_user); db.session.commit()
    log_action(session['user_id'], f"Created User: {email}", "User", new_user.id, reason)
    return redirect(url_for('dashboard'))

# --- Protected LMS Pages ---

@app.route('/courses.html')
def courses():
    if 'user_id' not in session: return redirect(url_for('login'))
    enrollments = Enrollment.query.filter_by(user_id=session['user_id']).all()
    return render_template('courses.html', user=session['user_name'], enrollments=enrollments)

@app.route('/course-detail.html')
def course_detail():
    if 'user_id' not in session: return redirect(url_for('login'))
    course_id = request.args.get('id')
    course = None
    if course_id:
        course = Course.query.get(course_id)
    
    # If no ID or course not found, just get the first one for demo safety
    if not course:
        course = Course.query.first()
        
    return render_template('course-detail.html', user=session['user_name'], course=course)

@app.route('/exams.html')
def exams():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('exams.html')

@app.route('/shield-check.html')
def shield_check():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('shield-check.html')

@app.route('/shield-verify.html')
def shield_verify():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('shield-verify.html')

@app.route('/quiz-interface.html')
def quiz_interface():
    if 'user_id' not in session: return redirect(url_for('login'))
    # Dynamic questions
    questions = Question.query.all() # Simple all for prototype
    return render_template('quiz-interface.html', questions=questions)

@app.route('/support.html')
def support():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('support.html')

@app.route('/settings.html')
def settings():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('settings.html')

if __name__ == '__main__':
    app.run(debug=True, port=8080)
