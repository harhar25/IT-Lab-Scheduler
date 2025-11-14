#!/usr/bin/env python3
import sys
import os
import sqlite3
from pathlib import Path

def setup_database():
    """Set up the SQLite database with initial data"""
    
    # Ensure backend directory exists
    backend_dir = Path("backend")
    backend_dir.mkdir(exist_ok=True)
    
    # Create database directory
    db_path = backend_dir / "it_lab_scheduler.db"
    
    print("Setting up IT Lab Scheduler Database...")
    
    # Import and create tables
    sys.path.insert(0, str(backend_dir))
    
    try:
        from app.database.session import engine
        from app.database import models
        from app.database.crud import create_user, get_user_by_username
        from app.schemas.user import UserCreate
        from app.database.models import UserRole
        
        # Create tables
        models.Base.metadata.create_all(bind=engine)
        print("✓ Database tables created")
        
        # Create default data
        from app.database.session import SessionLocal
        db = SessionLocal()
        
        try:
            # Default admin user
            if not get_user_by_username(db, username="admin"):
                create_user(
                    db,
                    UserCreate(
                        username="admin",
                        email="admin@university.edu",
                        full_name="System Administrator",
                        password="admin123",
                        role=UserRole.ADMIN
                    )
                )
                print("✓ Admin user created")
            
            # Default instructor
            if not get_user_by_username(db, username="instructor1"):
                create_user(
                    db,
                    UserCreate(
                        username="instructor1",
                        email="instructor1@university.edu",
                        full_name="Dr. John Smith",
                        password="instructor123",
                        role=UserRole.INSTRUCTOR
                    )
                )
                print("✓ Instructor user created")
            
            # Default student
            if not get_user_by_username(db, username="student1"):
                create_user(
                    db,
                    UserCreate(
                        username="student1",
                        email="student1@university.edu",
                        full_name="Alice Johnson",
                        password="student123",
                        role=UserRole.STUDENT
                    )
                )
                print("✓ Student user created")
            
            # Create default labs
            labs_data = [
                {"name": "Lab A", "capacity": 30, "equipment": "30 PCs, Projector, Whiteboard"},
                {"name": "Lab B", "capacity": 25, "equipment": "25 Macs, Projector"},
                {"name": "Lab C", "capacity": 40, "equipment": "40 PCs, Smart Board"},
                {"name": "Lab D", "capacity": 20, "equipment": "20 PCs, VR Equipment"}
            ]
            
            for lab_data in labs_data:
                existing_lab = db.query(models.Lab).filter(models.Lab.name == lab_data["name"]).first()
                if not existing_lab:
                    lab = models.Lab(**lab_data)
                    db.add(lab)
                    print(f"✓ Lab {lab_data['name']} created")
            
            # Create default courses
            courses_data = [
                {"code": "CS101", "name": "Introduction to Computer Science", "credits": 3},
                {"code": "IT202", "name": "Web Development Fundamentals", "credits": 3},
                {"code": "CS305", "name": "Data Structures and Algorithms", "credits": 4},
                {"code": "IT410", "name": "Advanced Database Systems", "credits": 4}
            ]
            
            for course_data in courses_data:
                existing_course = db.query(models.Course).filter(models.Course.code == course_data["code"]).first()
                if not existing_course:
                    course = models.Course(**course_data)
                    db.add(course)
                    print(f"✓ Course {course_data['code']} created")
            
            db.commit()
            print("✓ Default data created successfully!")
            
        except Exception as e:
            print(f"✗ Error creating default data: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        print(f"✗ Setup failed: {e}")
        return False
    
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import sqlalchemy
        import uvicorn
        print("✓ All dependencies are available")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please install requirements: pip install -r backend/requirements.txt")
        return False

if __name__ == "__main__":
    print("IT Lab Scheduler - Setup")
    print("=" * 40)
    
    if check_dependencies():
        if setup_database():
            print("\n🎉 Setup completed successfully!")
            print("\nTo run the application:")
            print("1. Start backend: uvicorn app.main:app --reload --port 8000")
            print("2. Open browser: http://localhost:8000")
            print("\nDefault credentials:")
            print("Admin: admin / admin123")
            print("Instructor: instructor1 / instructor123")
            print("Student: student1 / student123")
        else:
            print("\n❌ Setup failed!")
            sys.exit(1)
    else:
        sys.exit(1)