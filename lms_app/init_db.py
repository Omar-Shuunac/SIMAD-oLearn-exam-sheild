from app import app
from models import db, User, ExamPolicy, Course, Enrollment, ExamSession, Question, Choice, ExamAttempt, IntegrityFlag, Module, Assignment
from datetime import datetime
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        # Recreate Tables
        db.drop_all()
        db.create_all()
        
        # 0. Global Super Admin (super_admin)
        if not User.query.filter_by(role='super_admin').first():
            super_admin = User(
                name='SIMAD Super Authority',
                email='super.admin@simad.edu.so',
                password_hash=generate_password_hash('superadmin123', method='pbkdf2:sha256'),
                role='super_admin'
            )
            db.session.add(super_admin)
            print("Created Super Admin (Login with super.admin@simad.edu.so / superadmin123)")

        # 1. Platform/System Admin (sys_admin)
        if not User.query.filter_by(role='sys_admin').first():
            sys_admin = User(
                name='SIMAD System Admin',
                email='sys.admin@simad.edu.so',
                password_hash=generate_password_hash('admin123', method='pbkdf2:sha256'),
                role='sys_admin'
            )
            db.session.add(sys_admin)
            print("Created Sys Admin")

        # 2. Exam Office Admin (exam_admin)
        if not User.query.filter_by(role='exam_admin').first():
            exam_admin = User(
                name='SIMAD Exam Officer',
                email='exam.office@simad.edu.so',
                password_hash=generate_password_hash('exam123', method='pbkdf2:sha256'),
                role='exam_admin'
            )
            db.session.add(exam_admin)
            print("Created Exam Admin")

        # 3. Standard Instructor & Student for testing
        instructor = User.query.filter_by(role='instructor').first()
        if not instructor:
            instructor = User(name='Prof. Hassan', email='prof@simad.edu.so', password_hash=generate_password_hash('prof123', method='pbkdf2:sha256'), role='instructor')
            db.session.add(instructor)
            db.session.flush()

        student = User.query.filter_by(role='student').first()
        if not student:
            student = User(name='Mohamed Osman', email='student@simad.edu.so', password_hash=generate_password_hash('student123', method='pbkdf2:sha256'), role='student')
            db.session.add(student)

        # 4. Sample Course & Quiz
        if not Course.query.filter_by(code='CS-302').first():
            course = Course(code='CS-302', title='Advanced Database Systems', instructor_id=instructor.id)
            db.session.add(course)
            db.session.flush()
            
            # Enrollment for student
            enroll = Enrollment(user_id=student.id, course_id=course.id)
            db.session.add(enroll)

            # Exam Session
            exam = ExamSession(title='Final Exam: Sharding & CAP', course_id=course.id, start_time=datetime.utcnow(), end_time=datetime.utcnow())
            db.session.add(exam)
            db.session.flush()

            # Add real modules
            m1 = Module(course_id=course.id, title='Lecture 1.1: Distributed Systems Intro', content_type='video')
            m2 = Module(course_id=course.id, title='Lecture 1.2: The CAP Theorem', content_type='text')
            db.session.add_all([m1, m2])

            # Add real assignments
            a1 = Assignment(course_id=course.id, title='Lab 1: Sharding Exercises', due_date=datetime.utcnow())
            db.session.add(a1)

            # Dynamic Questions: Variety Pack
            q1 = Question(session_id=exam.id, text='Explain the difference between Vertical and Horizontal Scaling.', points=10, q_type='short_answer')
            
            q2 = Question(session_id=exam.id, text='Which property of the CAP theorem is prioritized by Cassandra by default?', points=15, q_type='multiple_choice')
            db.session.add_all([q1, q2])
            db.session.flush()

            # MCQ Choices for q2
            c1 = Choice(question_id=q2.id, text='Consistency', is_correct=False)
            c2 = Choice(question_id=q2.id, text='Availability', is_correct=True)
            c3 = Choice(question_id=q2.id, text='Partition Tolerance', is_correct=False)
            db.session.add_all([c1, c2, c3])
            
            # Matching Sample
            q3 = Question(session_id=exam.id, text='Match the technology to its architectural style.', points=20, q_type='matching')
            db.session.add(q3)

        db.session.commit()
        print("Database initialized with courses, modules, and questions!")

if __name__ == '__main__':
    init_db()
