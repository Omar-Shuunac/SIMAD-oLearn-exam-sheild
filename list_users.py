import sys
import os
sys.path.insert(0, os.path.abspath('lms_app'))
from app import app
from models import db, User

with app.app_context():
    users = User.query.all()
    if not users:
        print("No users found in database.")
    for u in users:
        print(f"Email: {u.email} | Password: {u.password_hash} | Role: {u.role}")
