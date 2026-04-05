"""
Phase 1 Database Migration Script
==================================
Run this ONCE to:
  1. Create new tables (Announcement, ModuleView) in PostgreSQL
  2. Hash any existing plain-text passwords using werkzeug

Usage:
    cd lms_app
    python ../migrate_phase1.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lms_app'))

from app import app
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash

def is_already_hashed(pw):
    """Detect if a password is already a werkzeug hash (starts with 'pbkdf2:' or 'scrypt:')."""
    return pw and (pw.startswith('pbkdf2:') or pw.startswith('scrypt:') or pw.startswith('sha256:'))

with app.app_context():
    print("Creating new tables (Announcement, ModuleView) if not exist...")
    db.create_all()
    print("✅ Tables created / verified.")

    print("\nChecking existing user passwords...")
    users = User.query.all()
    migrated = 0
    for user in users:
        if not is_already_hashed(user.password_hash):
            plain = user.password_hash  # treat stored value as a plain-text password
            user.password_hash = generate_password_hash(plain)
            migrated += 1
            print(f"  Hashing password for: {user.email}")

    if migrated:
        db.session.commit()
        print(f"\n✅ Migrated {migrated} user password(s) to secure hashes.")
    else:
        print("  All passwords already hashed — nothing to migrate.")

    print("\n✅ Phase 1 migration complete.")
