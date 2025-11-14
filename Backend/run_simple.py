import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import sqlite3
import os

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# FastAPI app
app = FastAPI(title="IT Lab Scheduler", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
def init_db():
    conn = sqlite3.connect('it_lab_scheduler.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS labs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            capacity INTEGER NOT NULL,
            equipment TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            credits INTEGER DEFAULT 3,
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')
    
    # Create default data
    create_default_data(cursor)
    
    conn.commit()
    conn.close()

def create_default_data(cursor):
    # Default users (password is hashed "password123")
    hashed_password = pwd_context.hash("password123")
    users = [
        ("admin", "admin@university.edu", hashed_password, "System Administrator", "admin"),
        ("instructor1", "instructor1@university.edu", hashed_password, "Dr. John Smith", "instructor"),
        ("student1", "student1@university.edu", hashed_password, "Alice Johnson", "student")
    ]
    
    for user in users:
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, email, hashed_password, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        ''', user)
    
    # Default labs
    labs = [
        ("Lab A", "Main computer lab", 30, "30 PCs, Projector, Whiteboard"),
        ("Lab B", "Mac lab", 25, "25 Macs, Projector"),
        ("Lab C", "Advanced computing lab", 40, "40 PCs, Smart Board"),
        ("Lab D", "VR lab", 20, "20 PCs, VR Equipment")
    ]
    
    for lab in labs:
        cursor.execute('''
            INSERT OR IGNORE INTO labs (name, description, capacity, equipment)
            VALUES (?, ?, ?, ?)
        ''', lab)
    
    # Default courses
    courses = [
        ("CS101", "Introduction to Computer Science", "Basic programming concepts", 3),
        ("IT202", "Web Development Fundamentals", "HTML, CSS, JavaScript", 3),
        ("CS305", "Data Structures and Algorithms", "Advanced data structures", 4),
        ("IT410", "Advanced Database Systems", "Database design and optimization", 4)
    ]
    
    for course in courses:
        cursor.execute('''
            INSERT OR IGNORE INTO courses (code, name, description, credits)
            VALUES (?, ?, ?, ?)
        ''', course)

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool

# Routes
@app.get("/")
async def root():
    return {"message": "IT Lab Scheduler API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/v1/login", response_model=Token)
async def login(login_data: LoginRequest):
    conn = sqlite3.connect('it_lab_scheduler.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE username = ?', (login_data.username,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_dict = {
        "id": user[0],
        "username": user[1],
        "email": user[2],
        "hashed_password": user[3],
        "full_name": user[4],
        "role": user[5],
        "is_active": user[6]
    }
    
    if not pwd_context.verify(login_data.password, user_dict["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
    token_data = {"sub": user_dict["username"], "role": user_dict["role"]}
    access_token = jwt.encode(token_data, "secret-key", algorithm="HS256")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_dict["id"],
            "username": user_dict["username"],
            "email": user_dict["email"],
            "full_name": user_dict["full_name"],
            "role": user_dict["role"],
            "is_active": user_dict["is_active"]
        }
    }

@app.get("/api/v1/labs")
async def get_labs():
    conn = sqlite3.connect('it_lab_scheduler.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM labs WHERE is_active = TRUE')
    labs = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": lab[0],
            "name": lab[1],
            "description": lab[2],
            "capacity": lab[3],
            "equipment": lab[4]
        }
        for lab in labs
    ]

@app.get("/api/v1/courses")
async def get_courses():
    conn = sqlite3.connect('it_lab_scheduler.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM courses WHERE is_active = TRUE')
    courses = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": course[0],
            "code": course[1],
            "name": course[2],
            "description": course[3],
            "credits": course[4]
        }
        for course in courses
    ]

@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats():
    conn = sqlite3.connect('it_lab_scheduler.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM labs WHERE is_active = TRUE')
    total_labs = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = TRUE')
    total_users = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_labs": total_labs,
        "total_sessions": 0,  # Would come from reservations table
        "pending_requests": 0,  # Would come from reservations table
        "total_users": total_users
    }

@app.get("/app")
async def web_interface():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>IT Lab Scheduler</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            .header { 
                text-align: center; 
                margin-bottom: 30px;
                background: linear-gradient(135deg, #2c3e50, #3498db);
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin: -30px -30px 30px -30px;
            }
            .card { 
                background: #f8f9fa; 
                padding: 20px; 
                border-radius: 8px; 
                margin: 15px 0;
                border-left: 4px solid #3498db;
            }
            .grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                gap: 20px; 
                margin: 20px 0; 
            }
            .login-form {
                max-width: 400px;
                margin: 50px auto;
                padding: 30px;
                background: white;
                border-radius: 10px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
                color: #2c3e50;
            }
            input, select {
                width: 100%;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 16px;
                box-sizing: border-box;
            }
            button {
                width: 100%;
                padding: 12px;
                background: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
            }
            button:hover {
                background: #2980b9;
            }
            .demo {
                background: #e8f4fd;
                padding: 15px;
                border-radius: 5px;
                margin-top: 20px;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 IT Laboratory Utilization Schedule System</h1>
                <p>Backend Server Running Successfully!</p>
            </div>

            <div class="grid">
                <div class="card">
                    <h3>📊 API Endpoints</h3>
                    <p><strong>Health Check:</strong> <code>GET /health</code></p>
                    <p><strong>Login:</strong> <code>POST /api/v1/login</code></p>
                    <p><strong>Labs:</strong> <code>GET /api/v1/labs</code></p>
                    <p><strong>Courses:</strong> <code>GET /api/v1/courses</code></p>
                    <p><strong>Dashboard Stats:</strong> <code>GET /api/v1/dashboard/stats</code></p>
                </div>

                <div class="card">
                    <h3>🔧 System Status</h3>
                    <p><strong>Database:</strong> ✅ Connected</p>
                    <p><strong>API Server:</strong> ✅ Running</p>
                    <p><strong>Default Data:</strong> ✅ Loaded</p>
                    <p><strong>Authentication:</strong> ✅ Ready</p>
                </div>

                <div class="card">
                    <h3>👥 Default Users</h3>
                    <p><strong>Admin:</strong> admin / password123</p>
                    <p><strong>Instructor:</strong> instructor1 / password123</p>
                    <p><strong>Student:</strong> student1 / password123</p>
                </div>
            </div>

            <div class="login-form">
                <h3>🔐 Test Login</h3>
                <form onsubmit="testLogin(event)">
                    <div class="form-group">
                        <label>Username:</label>
                        <input type="text" id="username" value="admin" required>
                    </div>
                    <div class="form-group">
                        <label>Password:</label>
                        <input type="password" id="password" value="password123" required>
                    </div>
                    <button type="submit">Test Login</button>
                </form>
                <div class="demo">
                    <strong>Demo Credentials:</strong><br>
                    Use any of the default users above
                </div>
                <div id="result" style="margin-top: 15px;"></div>
            </div>
        </div>

        <script>
            async function testLogin(event) {
                event.preventDefault();
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                const result = document.getElementById('result');

                try {
                    const response = await fetch('/api/v1/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            username: username,
                            password: password
                        })
                    });

                    if (response.ok) {
                        const data = await response.json();
                        result.innerHTML = `<div style="color: green; background: #d4edda; padding: 10px; border-radius: 5px;">
                            <strong>✅ Login Successful!</strong><br>
                            Welcome ${data.user.full_name} (${data.user.role})
                        </div>`;
                    } else {
                        const error = await response.json();
                        result.innerHTML = `<div style="color: red; background: #f8d7da; padding: 10px; border-radius: 5px;">
                            <strong>❌ Login Failed:</strong> ${error.detail}
                        </div>`;
                    }
                } catch (error) {
                    result.innerHTML = `<div style="color: red; background: #f8d7da; padding: 10px; border-radius: 5px;">
                        <strong>❌ Network Error:</strong> Please check if server is running
                    </div>`;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    # Initialize database
    print("🚀 Starting IT Lab Scheduler...")
    print("📦 Initializing database...")
    init_db()
    print("✅ Database initialized successfully!")
    print("🌐 Starting web server...")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🖥️  Web Interface: http://localhost:8000/app")
    print("🔑 Test Login: admin / password123")
    print("\nPress Ctrl+C to stop the server")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")