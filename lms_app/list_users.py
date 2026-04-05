from app import app
from models import User
from werkzeug.security import check_password_hash

with app.app_context():
    users = User.query.all()
    for u in users:
        print("Email:", u.email)
        print("Hash: ", u.password_hash)
        
        valid = False
        if "admin123" in u.password_hash:
            valid = True
        else:
            try:
                valid = check_password_hash(u.password_hash, "admin123") or \
                        check_password_hash(u.password_hash, "exam123") or \
                        check_password_hash(u.password_hash, "prof123") or \
                        check_password_hash(u.password_hash, "student123")
            except Exception as e:
                pass
        print("Matches a default pwd?", valid)
        print("-" * 30)
