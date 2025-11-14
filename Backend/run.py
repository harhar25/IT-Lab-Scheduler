import uvicorn
from app.main import app
from app.database.session import engine
from app.database import models
from app.database.crud import create_user, get_user_by_username
from app.schemas.user import UserCreate
from app.database.models import UserRole

def create_default_data():
    """Create default users and data for testing"""
    from app.database.session import SessionLocal
    
    db = SessionLocal()
    try:
        # Create default admin user
        admin_user = get_user_by_username(db, username="admin")
        if not admin_user:
            admin_user = create_user(
                db,
                UserCreate(
                    username="admin",
                    email="admin@university.edu",
                    full_name="System Administrator",
                    password="admin123",
                    role=UserRole.ADMIN
                )
            )
            print("Created admin user")
        
        # Create default instructor
        instructor = get_user_by_username(db, username="instructor1")
        if not instructor:
            instructor = create_user(
                db,
                UserCreate(
                    username="instructor1",
                    email="instructor1@university.edu",
                    full_name="Dr. John Smith",
                    password="instructor123",
                    role=UserRole.INSTRUCTOR
                )
            )
            print("Created instructor user")
        
        # Create default student
        student = get_user_by_username(db, username="student1")
        if not student:
            student = create_user(
                db,
                UserCreate(
                    username="student1",
                    email="student1@university.edu",
                    full_name="Alice Johnson",
                    password="student123",
                    role=UserRole.STUDENT
                )
            )
            print("Created student user")
        
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
                print(f"Created {lab_data['name']}")
        
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
                print(f"Created {course_data['code']}")
        
        db.commit()
        print("Default data created successfully!")
        
    except Exception as e:
        print(f"Error creating default data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Create tables
    models.Base.metadata.create_all(bind=engine)
    
    # Create default data
    create_default_data()
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )