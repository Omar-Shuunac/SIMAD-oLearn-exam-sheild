from app import app
from models import db
from sqlalchemy import inspect
import json

def generate_report():
    report = {
        "Routes (Capabilities)": {},
        "Database Models (Data Structures)": []
    }
    
    # Introspect Routes
    with app.app_context():
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                route_path = str(rule)
                methods = list(rule.methods - {'HEAD', 'OPTIONS'})
                if route_path not in report["Routes (Capabilities)"]:
                    report["Routes (Capabilities)"][route_path] = methods
                else:
                    report["Routes (Capabilities)"][route_path].extend(methods)
                    
        # Introspect Tables
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        for t in tables:
            columns = len(inspector.get_columns(t))
            report["Database Models (Data Structures)"].append({
                "Table": t,
                "Columns": columns
            })
            
    out = []
    out.append("\n" + "="*50)
    out.append(" 🚀 MVP SYSTEM SCAN REPORT 🚀")
    out.append("="*50 + "\n")
    
    out.append("=== DATABASE TABLES (The Brain) ===")
    for t in report["Database Models (Data Structures)"]:
        out.append(f"✅ {t['Table']} (Fields: {t['Columns']})")
    
    out.append("\n=== ACTIVE ROUTES (The Actions) ===")
    auth_routes = []
    admin_routes = []
    instructor_routes = []
    student_routes = []
    
    for route, methods in report["Routes (Capabilities)"].items():
        meth = ",".join(set(methods))
        if 'login' in route or 'register' in route or 'logout' in route:
            auth_routes.append(f"{meth}: {route}")
        elif 'admin' in route:
            admin_routes.append(f"{meth}: {route}")
        elif 'instructor' in route:
            instructor_routes.append(f"{meth}: {route}")
        else:
            student_routes.append(f"{meth}: {route}")
            
    out.append("\n[AUTHENTICATION / CORE]")
    for r in sorted(auth_routes): out.append("  - " + r)
    
    out.append("\n[SYSTEM / EXAM ADMIN]")
    for r in sorted(admin_routes): out.append("  - " + r)
        
    out.append("\n[INSTRUCTOR (COURSE/MODULE CRUD)]")
    for r in sorted(instructor_routes): out.append("  - " + r)
        
    out.append("\n[STUDENT / GENERAL VIEW]")
    for r in sorted(student_routes): out.append("  - " + r)

    with open("mvp_report.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(out))

if __name__ == "__main__":
    try:
        generate_report()
    except Exception as e:
        print(f"Error generating report: {e}")
