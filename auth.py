"""
Authentication utilities for user registration and login
"""
import sqlite3
from passlib.context import CryptContext
from datetime import datetime
import secrets
import warnings

# Suppress bcrypt warnings
warnings.filterwarnings('ignore', category=UserWarning, module='passlib')

# Password hashing context
# Use pbkdf2_sha256 as primary (more compatible, no bcrypt version issues)
# Also support bcrypt for existing users
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"], 
    deprecated="auto",
    pbkdf2_sha256__default_rounds=29000
)

# Database path
DB_PATH = './chat_db/medigenius_chats.db'

def init_auth_db():
    """Initialize users table in database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create users table with role support
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'patient',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Add role column if it doesn't exist
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN role TEXT DEFAULT "patient"')
    except sqlite3.OperationalError:
        pass
    
    # Create patient_reports table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patient_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER,
            title TEXT NOT NULL,
            symptoms TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES users (id),
            FOREIGN KEY (doctor_id) REFERENCES users (id)
        )
    ''')
    
    # Create prescriptions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            patient_id INTEGER NOT NULL,
            prescription_text TEXT NOT NULL,
            medications TEXT,
            dosage TEXT,
            instructions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (report_id) REFERENCES patient_reports (id),
            FOREIGN KEY (doctor_id) REFERENCES users (id),
            FOREIGN KEY (patient_id) REFERENCES users (id)
        )
    ''')
    
    # Create medication_reminders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medication_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prescription_id INTEGER NOT NULL,
            patient_id INTEGER NOT NULL,
            medication_name TEXT NOT NULL,
            reminder_time TIME NOT NULL,
            frequency TEXT DEFAULT 'daily',
            is_active INTEGER DEFAULT 1,
            last_sent TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prescription_id) REFERENCES prescriptions (id),
            FOREIGN KEY (patient_id) REFERENCES users (id)
        )
    ''')
    
    # Add user_id to sessions table if it doesn't exist
    try:
        cursor.execute('ALTER TABLE sessions ADD COLUMN user_id INTEGER')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)')
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    """Hash a password"""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        print(f"Password hashing error: {e}")
        # Fallback to simple hash if bcrypt fails
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def create_user(username: str, email: str, password: str, role: str = 'patient') -> dict:
    """Create a new user account"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if username or email already exists
        cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return {'success': False, 'error': 'Username or email already exists'}
        
        # Hash password and create user
        password_hash = hash_password(password)
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        ''', (username, email, password_hash, role))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {'success': True, 'user_id': user_id, 'username': username}
    except Exception as e:
        conn.close()
        return {'success': False, 'error': str(e)}

def authenticate_user(username: str, password: str) -> dict:
    """Authenticate a user and return user info"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get user by username or email
        cursor.execute('''
            SELECT id, username, email, password_hash, role
            FROM users
            WHERE username = ? OR email = ?
        ''', (username, username))
        
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return {'success': False, 'error': 'Invalid username or password'}
        
        user_id, db_username, email, password_hash, role = user
        
        # Verify password
        try:
            if not verify_password(password, password_hash):
                conn.close()
                return {'success': False, 'error': 'Invalid username or password'}
        except Exception as e:
            print(f"Authentication error: {e}")
            conn.close()
            return {'success': False, 'error': f'Authentication error: {str(e)}'}
        
        # Update last login
        cursor.execute('''
            UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
        ''', (user_id,))
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'user_id': user_id,
            'username': db_username,
            'email': email,
            'role': role
        }
    except Exception as e:
        conn.close()
        return {'success': False, 'error': str(e)}

def get_user_by_id(user_id: int) -> dict:
    """Get user information by ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, username, email, role, created_at, last_login
            FROM users
            WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        return {
            'success': True,
            'user_id': user[0],
            'username': user[1],
            'email': user[2],
            'role': user[3],
            'created_at': user[4],
            'last_login': user[5]
        }
    except Exception as e:
        conn.close()
        return {'success': False, 'error': str(e)}

def get_user_sessions(user_id: int):
    """Get all chat sessions for a user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.session_id, s.created_at, s.last_active, 
               (SELECT content FROM messages WHERE session_id = s.session_id 
                AND role = 'user' ORDER BY timestamp ASC LIMIT 1) as first_message
        FROM sessions s
        WHERE s.user_id = ?
        ORDER BY s.last_active DESC
    ''', (user_id,))
    
    sessions = []
    for row in cursor.fetchall():
        sessions.append({
            'session_id': row[0],
            'created_at': row[1],
            'last_active': row[2],
            'preview': row[3][:50] + '...' if row[3] and len(row[3]) > 50 else row[3]
        })
    
    conn.close()
    return sessions

def create_patient_report(patient_id: int, title: str, symptoms: str, description: str = '') -> dict:
    """Create a new patient report"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO patient_reports (patient_id, title, symptoms, description, status)
            VALUES (?, ?, ?, ?, 'pending')
        ''', (patient_id, title, symptoms, description))
        
        report_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {'success': True, 'report_id': report_id}
    except Exception as e:
        conn.close()
        return {'success': False, 'error': str(e)}

def get_patient_reports(patient_id: int = None, doctor_id: int = None, status: str = None):
    """Get patient reports - can filter by patient, doctor, or status"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = '''
        SELECT pr.id, pr.patient_id, pr.doctor_id, pr.title, pr.symptoms, pr.description,
               pr.status, pr.created_at, pr.updated_at,
               u1.username as patient_name, u1.email as patient_email,
               u2.username as doctor_name
        FROM patient_reports pr
        LEFT JOIN users u1 ON pr.patient_id = u1.id
        LEFT JOIN users u2 ON pr.doctor_id = u2.id
        WHERE 1=1
    '''
    params = []
    
    if patient_id:
        query += ' AND pr.patient_id = ?'
        params.append(patient_id)
    
    if doctor_id:
        query += ' AND pr.doctor_id = ?'
        params.append(doctor_id)
    
    if status:
        query += ' AND pr.status = ?'
        params.append(status)
    
    query += ' ORDER BY pr.created_at DESC'
    
    cursor.execute(query, params)
    reports = []
    for row in cursor.fetchall():
        reports.append({
            'id': row[0],
            'patient_id': row[1],
            'doctor_id': row[2],
            'title': row[3],
            'symptoms': row[4],
            'description': row[5],
            'status': row[6],
            'created_at': row[7],
            'updated_at': row[8],
            'patient_name': row[9],
            'patient_email': row[10],
            'doctor_name': row[11]
        })
    
    conn.close()
    return reports

def assign_report_to_doctor(report_id: int, doctor_id: int) -> dict:
    """Assign a patient report to a doctor"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE patient_reports
            SET doctor_id = ?, status = 'assigned', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (doctor_id, report_id))
        
        conn.commit()
        conn.close()
        return {'success': True}
    except Exception as e:
        conn.close()
        return {'success': False, 'error': str(e)}

def create_prescription(report_id: int, doctor_id: int, patient_id: int, 
                       prescription_text: str, medications: str = '', 
                       dosage: str = '', instructions: str = '') -> dict:
    """Create a prescription for a patient report"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO prescriptions (report_id, doctor_id, patient_id, prescription_text, 
                                     medications, dosage, instructions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (report_id, doctor_id, patient_id, prescription_text, medications, dosage, instructions))
        
        # Update report status to 'prescribed'
        cursor.execute('''
            UPDATE patient_reports
            SET status = 'prescribed', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (report_id,))
        
        prescription_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {'success': True, 'prescription_id': prescription_id}
    except Exception as e:
        conn.close()
        return {'success': False, 'error': str(e)}

def get_prescriptions(patient_id: int = None, doctor_id: int = None):
    """Get prescriptions - can filter by patient or doctor"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = '''
        SELECT p.id, p.report_id, p.doctor_id, p.patient_id, p.prescription_text,
               p.medications, p.dosage, p.instructions, p.created_at,
               u1.username as doctor_name, u2.username as patient_name,
               pr.title as report_title
        FROM prescriptions p
        LEFT JOIN users u1 ON p.doctor_id = u1.id
        LEFT JOIN users u2 ON p.patient_id = u2.id
        LEFT JOIN patient_reports pr ON p.report_id = pr.id
        WHERE 1=1
    '''
    params = []
    
    if patient_id:
        query += ' AND p.patient_id = ?'
        params.append(patient_id)
    
    if doctor_id:
        query += ' AND p.doctor_id = ?'
        params.append(doctor_id)
    
    query += ' ORDER BY p.created_at DESC'
    
    cursor.execute(query, params)
    prescriptions = []
    for row in cursor.fetchall():
        prescriptions.append({
            'id': row[0],
            'report_id': row[1],
            'doctor_id': row[2],
            'patient_id': row[3],
            'prescription_text': row[4],
            'medications': row[5],
            'dosage': row[6],
            'instructions': row[7],
            'created_at': row[8],
            'doctor_name': row[9],
            'patient_name': row[10],
            'report_title': row[11]
        })
    
    conn.close()
    return prescriptions

def get_pending_reports():
    """Get all pending reports (not yet assigned to a doctor)"""
    return get_patient_reports(status='pending')

def get_assigned_reports(doctor_id: int):
    """Get reports assigned to a specific doctor"""
    return get_patient_reports(doctor_id=doctor_id, status='assigned')

