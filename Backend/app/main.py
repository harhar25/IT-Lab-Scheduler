from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import json
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"

# Create FastAPI app
app = FastAPI(
    title="IT Lab Scheduler",
    version="1.0.0",
    description="IT Laboratory Utilization Schedule System"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database initialization
def init_db():
    conn = sqlite3.connect('lab_scheduler.db')
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instructor_id INTEGER NOT NULL,
            lab_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            section TEXT NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            duration INTEGER NOT NULL,
            notes TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (instructor_id) REFERENCES users (id),
            FOREIGN KEY (lab_id) REFERENCES labs (id),
            FOREIGN KEY (course_id) REFERENCES courses (id)
        )
    ''')
    
    # Insert default data
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Default users with hashed passwords
        users = [
            ('admin', 'admin@university.edu', pwd_context.hash('admin123'), 'System Administrator', 'admin'),
            ('instructor1', 'instructor1@university.edu', pwd_context.hash('instructor123'), 'Dr. John Smith', 'instructor'),
            ('student1', 'student1@university.edu', pwd_context.hash('student123'), 'Alice Johnson', 'student')
        ]
        cursor.executemany('''
            INSERT INTO users (username, email, hashed_password, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        ''', users)
        
        # Default labs
        labs = [
            ('Lab A', 'Main Computer Lab', 30, '30 PCs, Projector, Whiteboard'),
            ('Lab B', 'Mac Lab', 25, '25 Macs, Projector'),
            ('Lab C', 'Advanced Computing Lab', 40, '40 PCs, Smart Board'),
            ('Lab D', 'VR Lab', 20, '20 PCs, VR Equipment')
        ]
        cursor.executemany('''
            INSERT INTO labs (name, description, capacity, equipment)
            VALUES (?, ?, ?, ?)
        ''', labs)
        
        # Default courses
        courses = [
            ('CS101', 'Introduction to Computer Science', 'Basic programming concepts', 3),
            ('IT202', 'Web Development Fundamentals', 'HTML, CSS, JavaScript', 3),
            ('CS305', 'Data Structures and Algorithms', 'Advanced data structures', 4),
            ('IT410', 'Advanced Database Systems', 'Database design and optimization', 4)
        ]
        cursor.executemany('''
            INSERT INTO courses (code, name, description, credits)
            VALUES (?, ?, ?, ?)
        ''', courses)
        
        # Sample reservations
        sample_reservations = [
            (2, 1, 1, 'CS101-A', '2024-01-15 09:00:00', '2024-01-15 11:00:00', 2, 'Regular class', 'approved'),
            (2, 2, 2, 'IT202-B', '2024-01-16 14:00:00', '2024-01-16 16:00:00', 2, 'Lab session', 'approved'),
            (2, 3, 3, 'CS305-C', '2024-01-17 10:00:00', '2024-01-17 12:00:00', 2, None, 'pending'),
        ]
        cursor.executemany('''
            INSERT INTO reservations (instructor_id, lab_id, course_id, section, start_time, end_time, duration, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_reservations)
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class ReservationRequest(BaseModel):
    lab_id: int
    course_id: int
    section: str
    start_time: str
    end_time: str
    duration: int
    notes: Optional[str] = None

class ReservationResponse(BaseModel):
    id: int
    lab_id: int
    course_id: int
    section: str
    start_time: str
    end_time: str
    duration: int
    notes: Optional[str]
    status: str
    instructor_name: str
    lab_name: str
    course_name: str

# Utility functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.JWTError:
        return None

# API Routes
@app.get("/")
async def root():
    return {"message": "IT Laboratory Utilization Schedule System API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/v1/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    conn = sqlite3.connect('lab_scheduler.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username, email, hashed_password, full_name, role, is_active FROM users WHERE username = ?", 
        (login_data.username,)
    )
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    user_id, username, email, hashed_password, full_name, role, is_active = user
    
    if not pwd_context.verify(login_data.password, hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    access_token = create_access_token(
        data={"sub": username, "role": role, "user_id": user_id}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "username": username,
            "email": email,
            "full_name": full_name,
            "role": role,
            "is_active": bool(is_active)
        }
    }

@app.get("/api/v1/labs")
async def get_labs():
    conn = sqlite3.connect('lab_scheduler.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, capacity, equipment FROM labs WHERE is_active = 1")
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
    conn = sqlite3.connect('lab_scheduler.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, code, name, description, credits FROM courses WHERE is_active = 1")
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

@app.get("/api/v1/reservations")
async def get_reservations():
    conn = sqlite3.connect('lab_scheduler.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.id, r.lab_id, r.course_id, r.section, r.start_time, r.end_time, 
               r.duration, r.notes, r.status, u.full_name, l.name, c.name
        FROM reservations r
        JOIN users u ON r.instructor_id = u.id
        JOIN labs l ON r.lab_id = l.id
        JOIN courses c ON r.course_id = c.id
        ORDER BY r.start_time DESC
        LIMIT 10
    ''')
    reservations = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": res[0],
            "lab_id": res[1],
            "course_id": res[2],
            "section": res[3],
            "start_time": res[4],
            "end_time": res[5],
            "duration": res[6],
            "notes": res[7],
            "status": res[8],
            "instructor_name": res[9],
            "lab_name": res[10],
            "course_name": res[11]
        }
        for res in reservations
    ]

@app.post("/api/v1/reservations")
async def create_reservation(reservation: ReservationRequest, token: str = Depends(lambda: None)):
    # In a real app, you'd validate the JWT token here
    conn = sqlite3.connect('lab_scheduler.db')
    cursor = conn.cursor()
    
    # For demo, use instructor1 as the instructor
    instructor_id = 2
    
    cursor.execute('''
        INSERT INTO reservations (instructor_id, lab_id, course_id, section, start_time, end_time, duration, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (instructor_id, reservation.lab_id, reservation.course_id, reservation.section, 
          reservation.start_time, reservation.end_time, reservation.duration, reservation.notes))
    
    reservation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"message": "Reservation created successfully", "reservation_id": reservation_id}

@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats():
    conn = sqlite3.connect('lab_scheduler.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM labs WHERE is_active = 1")
    total_labs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM reservations")
    total_sessions = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM reservations WHERE status = 'pending'")
    pending_requests = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
    total_users = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_labs": total_labs,
        "total_sessions": total_sessions,
        "pending_requests": pending_requests,
        "total_users": total_users
    }

@app.put("/api/v1/reservations/{reservation_id}")
async def update_reservation_status(reservation_id: int, status: str):
    conn = sqlite3.connect('lab_scheduler.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE reservations SET status = ? WHERE id = ?
    ''', (status, reservation_id))
    
    conn.commit()
    conn.close()
    
    return {"message": f"Reservation {reservation_id} status updated to {status}"}

# Web Interface with Full Features
@app.get("/app")
async def web_interface():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>IT Lab Scheduler</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            :root {
                --primary: #2c3e50;
                --secondary: #3498db;
                --success: #2ecc71;
                --warning: #f39c12;
                --danger: #e74c3c;
                --light: #ecf0f1;
                --dark: #34495e;
            }
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, var(--primary), var(--secondary));
                color: white;
                padding: 40px;
                text-align: center;
            }
            .header h1 {
                font-size: 2.5rem;
                margin-bottom: 10px;
            }
            .nav-tabs {
                display: flex;
                background: var(--dark);
                padding: 0;
                margin: 0;
                list-style: none;
            }
            .nav-tabs li {
                flex: 1;
            }
            .nav-tabs button {
                width: 100%;
                padding: 20px;
                background: none;
                border: none;
                color: white;
                font-size: 16px;
                cursor: pointer;
                transition: background 0.3s;
            }
            .nav-tabs button:hover {
                background: rgba(255,255,255,0.1);
            }
            .nav-tabs button.active {
                background: var(--secondary);
                border-bottom: 3px solid white;
            }
            .tab-content {
                padding: 40px;
                display: none;
            }
            .tab-content.active {
                display: block;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .card {
                background: var(--light);
                padding: 25px;
                border-radius: 10px;
                border-left: 5px solid var(--secondary);
            }
            .card h3 {
                color: var(--primary);
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }
            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                border-top: 4px solid var(--secondary);
            }
            .stat-card.warning { border-top-color: var(--warning); }
            .stat-card.success { border-top-color: var(--success); }
            .stat-card.danger { border-top-color: var(--danger); }
            .stat-number {
                font-size: 2.5rem;
                font-weight: bold;
                color: var(--primary);
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: var(--primary);
            }
            input, select, textarea {
                width: 100%;
                padding: 12px 15px;
                border: 2px solid #e1e8ed;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            input:focus, select:focus, textarea:focus {
                outline: none;
                border-color: var(--secondary);
            }
            button {
                padding: 12px 25px;
                background: var(--secondary);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
                transition: background 0.3s;
            }
            button:hover {
                background: #2980b9;
            }
            .btn-success { background: var(--success); }
            .btn-success:hover { background: #27ae60; }
            .btn-danger { background: var(--danger); }
            .btn-danger:hover { background: #c0392b; }
            .btn-warning { background: var(--warning); }
            .btn-warning:hover { background: #e67e22; }
            .table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            .table th, .table td {
                padding: 12px 15px;
                text-align: left;
                border-bottom: 1px solid #e1e8ed;
            }
            .table th {
                background: var(--light);
                font-weight: 600;
            }
            .status {
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 0.8rem;
                font-weight: 500;
            }
            .status.approved {
                background: rgba(46, 204, 113, 0.2);
                color: var(--success);
            }
            .status.pending {
                background: rgba(243, 156, 18, 0.2);
                color: var(--warning);
            }
            .status.declined {
                background: rgba(231, 76, 60, 0.2);
                color: var(--danger);
            }
            .notification {
                padding: 15px;
                border-radius: 8px;
                margin: 15px 0;
                text-align: center;
                font-weight: 600;
            }
            .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1><i class="fas fa-laptop-code"></i> IT Laboratory Utilization Schedule System</h1>
                <p>Professional Lab Management Solution</p>
            </div>
            
            <ul class="nav-tabs">
                <li><button onclick="showTab('dashboard')" class="active"><i class="fas fa-tachometer-alt"></i> Dashboard</button></li>
                <li><button onclick="showTab('schedule')"><i class="fas fa-calendar-alt"></i> Schedule</button></li>
                <li><button onclick="showTab('reservations')"><i class="fas fa-plus-circle"></i> Reservations</button></li>
                <li><button onclick="showTab('labs')"><i class="fas fa-laptop-house"></i> Labs</button></li>
                <li><button onclick="showTab('login')"><i class="fas fa-sign-in-alt"></i> Login</button></li>
            </ul>
            
            <!-- Dashboard Tab -->
            <div id="dashboard" class="tab-content active">
                <h2><i class="fas fa-tachometer-alt"></i> Dashboard Overview</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number" id="total-labs">0</div>
                        <p>Total Labs</p>
                    </div>
                    <div class="stat-card success">
                        <div class="stat-number" id="total-sessions">0</div>
                        <p>Scheduled Sessions</p>
                    </div>
                    <div class="stat-card warning">
                        <div class="stat-number" id="pending-requests">0</div>
                        <p>Pending Requests</p>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="total-users">0</div>
                        <p>Registered Users</p>
                    </div>
                </div>
                
                <div class="grid">
                    <div class="card">
                        <h3><i class="fas fa-clock"></i> Recent Reservations</h3>
                        <div id="recent-reservations">Loading...</div>
                    </div>
                    <div class="card">
                        <h3><i class="fas fa-chart-bar"></i> Quick Actions</h3>
                        <div style="display: flex; flex-direction: column; gap: 10px;">
                            <button onclick="showTab('reservations')"><i class="fas fa-plus"></i> New Reservation</button>
                            <button onclick="showTab('schedule')"><i class="fas fa-calendar"></i> View Schedule</button>
                            <button onclick="loadLabs()"><i class="fas fa-list"></i> Manage Labs</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Schedule Tab -->
            <div id="schedule" class="tab-content">
                <h2><i class="fas fa-calendar-alt"></i> Lab Schedule</h2>
                <div class="card">
                    <h3><i class="fas fa-filter"></i> Filters</h3>
                    <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                        <select id="lab-filter">
                            <option value="">All Labs</option>
                        </select>
                        <select id="status-filter">
                            <option value="">All Status</option>
                            <option value="approved">Approved</option>
                            <option value="pending">Pending</option>
                        </select>
                        <button onclick="loadReservations()">Apply Filters</button>
                    </div>
                </div>
                <div id="schedule-content">Loading schedule...</div>
            </div>
            
            <!-- Reservations Tab -->
            <div id="reservations" class="tab-content">
                <h2><i class="fas fa-plus-circle"></i> Make Reservation</h2>
                <div class="card">
                    <form onsubmit="createReservation(event)">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                            <div class="form-group">
                                <label for="reservation-lab">Lab *</label>
                                <select id="reservation-lab" required>
                                    <option value="">Select Lab</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="reservation-course">Course *</label>
                                <select id="reservation-course" required>
                                    <option value="">Select Course</option>
                                </select>
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="reservation-section">Section *</label>
                            <input type="text" id="reservation-section" placeholder="e.g., CS101-A" required>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px;">
                            <div class="form-group">
                                <label for="reservation-date">Date *</label>
                                <input type="date" id="reservation-date" required>
                            </div>
                            <div class="form-group">
                                <label for="reservation-start">Start Time *</label>
                                <input type="time" id="reservation-start" required>
                            </div>
                            <div class="form-group">
                                <label for="reservation-duration">Duration (hours) *</label>
                                <select id="reservation-duration" required>
                                    <option value="1">1 hour</option>
                                    <option value="2">2 hours</option>
                                    <option value="3">3 hours</option>
                                </select>
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="reservation-notes">Notes (Optional)</label>
                            <textarea id="reservation-notes" rows="3" placeholder="Additional information..."></textarea>
                        </div>
                        <button type="submit"><i class="fas fa-paper-plane"></i> Submit Reservation</button>
                    </form>
                    <div id="reservation-result"></div>
                </div>
            </div>
            
            <!-- Labs Tab -->
            <div id="labs" class="tab-content">
                <h2><i class="fas fa-laptop-house"></i> Available Labs</h2>
                <div id="labs-content">Loading labs...</div>
            </div>
            
            <!-- Login Tab -->
            <div id="login" class="tab-content">
                <h2><i class="fas fa-sign-in-alt"></i> System Login</h2>
                <div class="card" style="max-width: 400px; margin: 0 auto;">
                    <form onsubmit="handleLogin(event)">
                        <div class="form-group">
                            <label for="login-username">Username</label>
                            <input type="text" id="login-username" value="admin" required>
                        </div>
                        <div class="form-group">
                            <label for="login-password">Password</label>
                            <input type="password" id="login-password" value="admin123" required>
                        </div>
                        <div class="form-group">
                            <label for="login-role">Role</label>
                            <select id="login-role">
                                <option value="student">Student</option>
                                <option value="instructor">Instructor</option>
                                <option value="admin" selected>Administrator</option>
                            </select>
                        </div>
                        <button type="submit"><i class="fas fa-sign-in-alt"></i> Login</button>
                    </form>
                    <div id="login-result"></div>
                    <div style="margin-top: 20px; padding: 15px; background: #e8f4fd; border-radius: 5px;">
                        <h4><i class="fas fa-info-circle"></i> Demo Credentials</h4>
                        <p><strong>Admin:</strong> admin / admin123</p>
                        <p><strong>Instructor:</strong> instructor1 / instructor123</p>
                        <p><strong>Student:</strong> student1 / student123</p>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // Tab management
            function showTab(tabName) {
                document.querySelectorAll('.tab-content').forEach(tab => {
                    tab.classList.remove('active');
                });
                document.querySelectorAll('.nav-tabs button').forEach(btn => {
                    btn.classList.remove('active');
                });
                document.getElementById(tabName).classList.add('active');
                event.target.classList.add('active');
                
                // Load tab-specific data
                if (tabName === 'dashboard') loadDashboard();
                if (tabName === 'labs') loadLabs();
                if (tabName === 'schedule') loadReservations();
            }

            // API functions
            async function apiCall(endpoint, options = {}) {
                try {
                    const response = await fetch(endpoint, {
                        headers: {
                            'Content-Type': 'application/json',
                            ...options.headers
                        },
                        ...options
                    });
                    return await response.json();
                } catch (error) {
                    showNotification('API Error: ' + error.message, 'error');
                    throw error;
                }
            }

            function showNotification(message, type = 'info') {
                const notification = document.createElement('div');
                notification.className = `notification ${type}`;
                notification.innerHTML = message;
                notification.style.margin = '10px 0';
                
                const container = document.querySelector('.tab-content.active');
                container.insertBefore(notification, container.firstChild);
                
                setTimeout(() => notification.remove(), 5000);
            }

            // Dashboard functions
            async function loadDashboard() {
                try {
                    const [stats, reservations] = await Promise.all([
                        apiCall('/api/v1/dashboard/stats'),
                        apiCall('/api/v1/reservations')
                    ]);
                    
                    // Update stats
                    document.getElementById('total-labs').textContent = stats.total_labs;
                    document.getElementById('total-sessions').textContent = stats.total_sessions;
                    document.getElementById('pending-requests').textContent = stats.pending_requests;
                    document.getElementById('total-users').textContent = stats.total_users;
                    
                    // Update recent reservations
                    const reservationsHtml = reservations.length > 0 ? 
                        `<table class="table">
                            <thead>
                                <tr>
                                    <th>Lab</th>
                                    <th>Course</th>
                                    <th>Instructor</th>
                                    <th>Time</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${reservations.map(res => `
                                    <tr>
                                        <td>${res.lab_name}</td>
                                        <td>${res.course_name}</td>
                                        <td>${res.instructor_name}</td>
                                        <td>${new Date(res.start_time).toLocaleString()}</td>
                                        <td><span class="status ${res.status}">${res.status}</span></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>` :
                        '<p>No reservations found.</p>';
                    
                    document.getElementById('recent-reservations').innerHTML = reservationsHtml;
                    
                } catch (error) {
                    showNotification('Failed to load dashboard data', 'error');
                }
            }

            // Labs functions
            async function loadLabs() {
                try {
                    const labs = await apiCall('/api/v1/labs');
                    const labsHtml = `
                        <div class="grid">
                            ${labs.map(lab => `
                                <div class="card">
                                    <h3><i class="fas fa-laptop"></i> ${lab.name}</h3>
                                    <p><strong>Capacity:</strong> ${lab.capacity} seats</p>
                                    <p><strong>Equipment:</strong> ${lab.equipment}</p>
                                    <p>${lab.description}</p>
                                </div>
                            `).join('')}
                        </div>
                    `;
                    document.getElementById('labs-content').innerHTML = labsHtml;
                    
                    // Also populate lab dropdowns
                    populateLabDropdowns(labs);
                } catch (error) {
                    showNotification('Failed to load labs', 'error');
                }
            }

            function populateLabDropdowns(labs) {
                const labSelects = ['lab-filter', 'reservation-lab'];
                labSelects.forEach(selectId => {
                    const select = document.getElementById(selectId);
                    // Clear existing options (keep first option)
                    while (select.children.length > 1) {
                        select.removeChild(select.lastChild);
                    }
                    labs.forEach(lab => {
                        const option = document.createElement('option');
                        option.value = lab.id;
                        option.textContent = lab.name;
                        select.appendChild(option);
                    });
                });
            }

            // Reservations functions
            async function loadReservations() {
                try {
                    const reservations = await apiCall('/api/v1/reservations');
                    const scheduleHtml = `
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Lab</th>
                                    <th>Course</th>
                                    <th>Section</th>
                                    <th>Instructor</th>
                                    <th>Date & Time</th>
                                    <th>Duration</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${reservations.map(res => `
                                    <tr>
                                        <td>${res.lab_name}</td>
                                        <td>${res.course_name}</td>
                                        <td>${res.section}</td>
                                        <td>${res.instructor_name}</td>
                                        <td>${new Date(res.start_time).toLocaleString()}</td>
                                        <td>${res.duration} hours</td>
                                        <td><span class="status ${res.status}">${res.status}</span></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    `;
                    document.getElementById('schedule-content').innerHTML = scheduleHtml;
                } catch (error) {
                    showNotification('Failed to load reservations', 'error');
                }
            }

            async function createReservation(event) {
                event.preventDefault();
                
                const reservationData = {
                    lab_id: parseInt(document.getElementById('reservation-lab').value),
                    course_id: parseInt(document.getElementById('reservation-course').value),
                    section: document.getElementById('reservation-section').value,
                    start_time: document.getElementById('reservation-date').value + 'T' + document.getElementById('reservation-start').value + ':00',
                    end_time: calculateEndTime(),
                    duration: parseInt(document.getElementById('reservation-duration').value),
                    notes: document.getElementById('reservation-notes').value
                };
                
                try {
                    const result = await apiCall('/api/v1/reservations', {
                        method: 'POST',
                        body: JSON.stringify(reservationData)
                    });
                    
                    showNotification('Reservation submitted successfully! ID: ' + result.reservation_id, 'success');
                    document.getElementById('reservation-form').reset();
                    loadReservations(); // Refresh the schedule
                    
                } catch (error) {
                    showNotification('Failed to create reservation', 'error');
                }
            }

            function calculateEndTime() {
                const date = document.getElementById('reservation-date').value;
                const startTime = document.getElementById('reservation-start').value;
                const duration = parseInt(document.getElementById('reservation-duration').value);
                
                const start = new Date(date + 'T' + startTime);
                const end = new Date(start.getTime() + duration * 60 * 60 * 1000);
                
                return end.toISOString().slice(0, 16).replace('T', ' ') + ':00';
            }

            // Login function
            async function handleLogin(event) {
                event.preventDefault();
                
                const loginData = {
                    username: document.getElementById('login-username').value,
                    password: document.getElementById('login-password').value
                };
                
                try {
                    const result = await apiCall('/api/v1/login', {
                        method: 'POST',
                        body: JSON.stringify(loginData)
                    });
                    
                    showNotification(`Login successful! Welcome ${result.user.full_name} (${result.user.role})`, 'success');
                    localStorage.setItem('auth_token', result.access_token);
                    localStorage.setItem('user_data', JSON.stringify(result.user));
                    
                } catch (error) {
                    showNotification('Login failed: ' + (error.detail || error.message), 'error');
                }
            }

            // Load courses for reservation form
            async function loadCourses() {
                try {
                    const courses = await apiCall('/api/v1/courses');
                    const select = document.getElementById('reservation-course');
                    // Clear existing options (keep first option)
                    while (select.children.length > 1) {
                        select.removeChild(select.lastChild);
                    }
                    courses.forEach(course => {
                        const option = document.createElement('option');
                        option.value = course.id;
                        option.textContent = `${course.code} - ${course.name}`;
                        select.appendChild(option);
                    });
                } catch (error) {
                    console.error('Failed to load courses:', error);
                }
            }

            // Set default date to tomorrow
            function setDefaultDate() {
                const tomorrow = new Date();
                tomorrow.setDate(tomorrow.getDate() + 1);
                document.getElementById('reservation-date').valueAsDate = tomorrow;
            }

            // Initialize the application
            async function initApp() {
                await loadDashboard();
                await loadLabs();
                await loadCourses();
                await loadReservations();
                setDefaultDate();
            }

            // Start the application
            initApp();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    print("🚀 IT Lab Scheduler is running!")
    print("📊 Web Interface: http://localhost:8000/app")
    print("🔗 API Documentation: http://localhost:8000/docs")
    print("🔑 Demo Login: admin / admin123")
    uvicorn.run(app, host="0.0.0.0", port=8000)