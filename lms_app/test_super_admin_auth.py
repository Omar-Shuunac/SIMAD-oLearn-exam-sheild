"""
test_super_admin_auth.py
═══════════════════════════════════════════════════════════════════════════════
Authorization boundary test suite.
Verifies that 'sys_admin' (and lower roles) cannot access 'super_admin'
configuration endpoints. Run with:

    python test_super_admin_auth.py

Expected: All SA endpoints return 302 redirect for non-super-admin users.
"""

import requests
import sys

BASE_URL = "http://127.0.0.1:8080"
PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"

SA_ENDPOINTS = [
    "/sa/hub",
    "/sa/sessions",
    "/sa/roles",
    "/sa/proctoring",
    "/sa/question_bank",
    "/sa/audit",
    "/sa/audit/export",
    "/sa/reports/integrity",
    "/sa/reports/health",
]


def login_as(session, email, password):
    """Authenticate and obtain a session cookie."""
    r = session.post(f"{BASE_URL}/login", data={"email": email, "password": password}, allow_redirects=True)
    return r


def test_role_blocked(role_email, role_password, role_label):
    """Assert that a given role cannot access any SA endpoint."""
    print(f"\n{'='*60}")
    print(f"  Testing: {role_label} ({role_email})")
    print(f"{'='*60}")
    
    s = requests.Session()
    login_as(s, role_email, role_password)

    all_passed = True
    for endpoint in SA_ENDPOINTS:
        r = s.get(f"{BASE_URL}{endpoint}", allow_redirects=False)
        # Super Admin endpoints must redirect (302) or deny (403) for non-SA roles
        blocked = r.status_code in (302, 403)
        status = PASS if blocked else FAIL
        if not blocked:
            all_passed = False
        print(f"  {status}  GET {endpoint}  → HTTP {r.status_code}")
    
    return all_passed


def test_unauthenticated():
    """Unauthenticated users must be redirected from all SA endpoints."""
    print(f"\n{'='*60}")
    print("  Testing: Unauthenticated (no session)")
    print(f"{'='*60}")
    s = requests.Session()
    all_passed = True
    for endpoint in SA_ENDPOINTS:
        r = s.get(f"{BASE_URL}{endpoint}", allow_redirects=False)
        blocked = r.status_code in (302, 403)
        status = PASS if blocked else FAIL
        if not blocked:
            all_passed = False
        print(f"  {status}  GET {endpoint}  → HTTP {r.status_code}")
    return all_passed


if __name__ == "__main__":
    results = []
    
    # --- Unauthenticated ---
    results.append(test_unauthenticated())
    
    # --- sys_admin (should be BLOCKED from SA endpoints) ---
    # Change these credentials to match your actual sys_admin user
    results.append(test_role_blocked(
        role_email="admin@simad.edu.so",
        role_password="admin123",
        role_label="sys_admin"
    ))

    # --- student (should be BLOCKED) ---
    results.append(test_role_blocked(
        role_email="student@simad.edu.so",
        role_password="student123",
        role_label="student"
    ))

    print(f"\n{'='*60}")
    if all(results):
        print(f"  {PASS}  ALL AUTHORIZATION TESTS PASSED")
        print("  Super Admin boundary is correctly enforced.")
        sys.exit(0)
    else:
        print(f"  {FAIL}  SOME TESTS FAILED — Review output above.")
        sys.exit(1)
