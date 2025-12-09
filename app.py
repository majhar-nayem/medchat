from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
from flask import session
from flask import redirect
from flask import url_for
from flask import send_file
from functools import wraps
import os
import uuid
import secrets
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO

from core.langgraph_workflow import create_workflow
from core.state import initialize_conversation_state
from core.state import reset_query_state
from tools.pdf_loader import process_pdf
from tools.vector_store import get_or_create_vectorstore
from auth import (
    init_auth_db, create_user, authenticate_user, 
    get_user_by_id, get_user_sessions,
    create_patient_report, get_patient_reports, assign_report_to_doctor,
    create_prescription, get_prescriptions, get_pending_reports, get_assigned_reports
)
from email_service import (
    send_medication_reminder, create_medication_reminder,
    get_patient_reminders, update_reminder_last_sent, delete_reminder
)
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit

load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Global workflow and conversation states
workflow_app = None
conversation_states = {}

# Email reminder scheduler
scheduler = BackgroundScheduler()

def check_and_send_reminders():
    """Check for due reminders and send emails"""
    from datetime import datetime, time
    import sqlite3
    
    try:
        current_time = datetime.now().time()
        current_time_str = current_time.strftime('%H:%M')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all active reminders for current time
        cursor.execute('''
            SELECT mr.id, mr.prescription_id, mr.patient_id, mr.medication_name,
                   mr.reminder_time, mr.last_sent,
                   p.medications, p.dosage, p.instructions, p.prescription_text,
                   u.email, u.username
            FROM medication_reminders mr
            LEFT JOIN prescriptions p ON mr.prescription_id = p.id
            LEFT JOIN users u ON mr.patient_id = u.id
            WHERE mr.is_active = 1
            AND TIME(mr.reminder_time) = TIME(?)
            AND (mr.last_sent IS NULL OR DATE(mr.last_sent) != DATE('now'))
        ''', (current_time_str,))
        
        reminders = cursor.fetchall()
        conn.close()
        
        for reminder in reminders:
            reminder_id, prescription_id, patient_id, medication_name, reminder_time, last_sent, \
            medications, dosage, instructions, prescription_text, patient_email, patient_name = reminder
            
            # Send reminder email
            if send_medication_reminder(
                patient_email, patient_name, medication_name,
                dosage or '', instructions or '', prescription_text or ''
            ):
                update_reminder_last_sent(reminder_id)
    except Exception as e:
        print(f"Error in reminder scheduler: {e}")

# SQLite Database Setup
DB_PATH = './chat_db/medigenius_chats.db'

def init_db():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def save_message(session_id, role, content, source=None, user_id=None):
    """Save a message to the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ensure session exists (with user_id if provided)
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO sessions (session_id, user_id) VALUES (?, ?)
        ''', (session_id, user_id))
    except sqlite3.OperationalError:
        # Fallback if user_id column doesn't exist yet
        cursor.execute('''
            INSERT OR IGNORE INTO sessions (session_id) VALUES (?)
        ''', (session_id,))
    
    # Update last active time
    cursor.execute('''
        UPDATE sessions SET last_active = CURRENT_TIMESTAMP WHERE session_id = ?
    ''', (session_id,))
    
    # Insert message
    cursor.execute('''
        INSERT INTO messages (session_id, role, content, source)
        VALUES (?, ?, ?, ?)
    ''', (session_id, role, content, source))
    
    conn.commit()
    conn.close()

def get_chat_history(session_id):
    """Retrieve chat history for a session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT role, content, source, timestamp
        FROM messages
        WHERE session_id = ?
        ORDER BY timestamp ASC
    ''', (session_id,))
    
    messages = []
    for row in cursor.fetchall():
        messages.append({
            'role': row[0],
            'content': row[1],
            'source': row[2],
            'timestamp': row[3]
        })
    
    conn.close()
    return messages

def get_all_sessions():
    """Get all chat sessions"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.session_id, s.created_at, s.last_active, 
               (SELECT content FROM messages WHERE session_id = s.session_id 
                AND role = 'user' ORDER BY timestamp ASC LIMIT 1) as first_message
        FROM sessions s
        ORDER BY s.last_active DESC
    ''')
    
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

def delete_session(session_id):
    """Delete a chat session and its messages"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
    cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
    
    conn.commit()
    conn.close()

def initialize_system():
    """Initialize system with lightweight startup for free tier"""
    global workflow_app
    
    print("Initializing MediGenius System...")
    
    # Initialize database (lightweight)
    init_db()
    init_auth_db()  # Initialize authentication database
    print("Database initialized...")
    
    # Check if we're on a memory-constrained environment (free tier)
    # Skip heavy model loading at startup to save memory
    is_memory_constrained = os.environ.get('RENDER', '').lower() == 'true'
    
    if is_memory_constrained:
        print("Running in lightweight mode - models will load on first request")
        # Don't load heavy models at startup
        workflow_app = None
        print("MediGenius Web Interface Ready! (Lightweight mode)")
        return
    
    # Full initialization for paid tiers or local
    pdf_path = './data/medical_book.pdf'
    persist_dir = './medical_db/'
    
    # Try to load existing database (lazy - don't create if not exists)
    try:
        existing_db = get_or_create_vectorstore(persist_dir=persist_dir)
        
        if not existing_db and os.path.exists(pdf_path):
            print("Creating vector database from PDF...")
            doc_splits = process_pdf(pdf_path)
            get_or_create_vectorstore(documents=doc_splits, persist_dir=persist_dir)
        elif not existing_db:
            print("No vector database and no PDF found - RAG features will be limited")
    except Exception as e:
        print(f"Warning: Could not initialize vector store: {e}")
        print("Continuing without RAG functionality...")
    
    # Create workflow (this loads models - memory intensive)
    try:
        workflow_app = create_workflow()
        print("Workflow initialized...")
    except Exception as e:
        print(f"Warning: Could not initialize workflow: {e}")
        print("Workflow will be loaded on first request...")
        workflow_app = None
    
    print("MediGenius Web Interface Ready!")

def get_workflow():
    """Lazy load workflow only when needed (for free tier)"""
    global workflow_app
    if workflow_app is None:
        print("Loading workflow (first request - this may take a moment)...")
        try:
            workflow_app = create_workflow()
            print("Workflow loaded successfully!")
        except Exception as e:
            print(f"Error loading workflow: {e}")
            raise
    return workflow_app

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' not in session:
        return render_template('landing.html')
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        # Link session to user
        user_id = session.get('user_id')
        if user_id:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    UPDATE sessions SET user_id = ? WHERE session_id = ?
                ''', (user_id, session['session_id']))
                conn.commit()
            except:
                pass
            conn.close()
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            data = request.json
            if not data:
                return jsonify({'success': False, 'error': 'Invalid request data'}), 400
                
            username = data.get('username', '').strip()
            password = data.get('password', '')
            
            if not username or not password:
                return jsonify({'success': False, 'error': 'Username and password required'}), 400
            
            result = authenticate_user(username, password)
            
            if result['success']:
                session['user_id'] = result['user_id']
                session['username'] = result['username']
                session['email'] = result['email']
                session['role'] = result.get('role', 'patient')
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'user': {
                        'username': result['username'],
                        'email': result['email'],
                        'role': result.get('role', 'patient')
                    }
                })
            else:
                return jsonify({'success': False, 'error': result.get('error', 'Invalid credentials')}), 401
        except Exception as e:
            import traceback
            print(f"Login error: {e}")
            print(traceback.format_exc())
            return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500
    
    # GET request - show login page
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.json
        username = data.get('username', '')
        email = data.get('email', '')
        password = data.get('password', '')
        role = data.get('role', 'patient')  # Default to patient
        
        if not username or not email or not password:
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
        
        # Validate role
        if role not in ['patient', 'doctor']:
            role = 'patient'
        
        result = create_user(username, email, password, role)
        
        if result['success']:
            # Auto-login after registration
            session['user_id'] = result['user_id']
            session['username'] = result['username']
            session['email'] = email
            session['role'] = role
            return jsonify({
                'success': True,
                'message': 'Registration successful',
                'user': {
                    'username': result['username'],
                    'email': email
                }
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 400
    
    # GET request - show register page
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/user', methods=['GET'])
@login_required
def get_current_user():
    """Get current logged-in user information"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    result = get_user_by_id(user_id)
    if result['success']:
        return jsonify({
            'success': True,
            'user': {
                'user_id': result['user_id'],
                'username': result['username'],
                'email': result['email'],
                'role': result.get('role', 'patient'),
                'created_at': result['created_at'],
                'last_login': result['last_login']
            }
        })
    return jsonify({'success': False, 'error': result['error']}), 404

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    global workflow_app, conversation_states
    
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        message = data.get('message', '')
        session_id = session.get('session_id')
        
        # Create session_id if it doesn't exist
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Lazy load workflow if needed (for free tier memory optimization)
        workflow = get_workflow()
        if not workflow:
            return jsonify({'error': 'System not initialized. Please try again in a moment.'}), 500
        
        # Get user_id for linking messages
        user_id = session.get('user_id')
        
        # Save user message to database
        save_message(session_id, 'user', message, user_id=user_id)
        
        # Initialize or get conversation state
        if session_id not in conversation_states:
            conversation_states[session_id] = initialize_conversation_state()
        
        conversation_state = conversation_states[session_id]
        conversation_state = reset_query_state(conversation_state)
        conversation_state["question"] = message
        
        # Check for diabetes-related queries and run detection
        from diabetes_detector import detect_diabetes_from_chat
        
        diabetes_keywords = [
            'diabetes', 'diabetic', 'blood sugar', 'glucose', 'insulin',
            'sugar level', 'high glucose', 'diabetes symptoms', 'diabetes risk'
        ]
        message_lower = message.lower()
        is_diabetes_related = any(keyword in message_lower for keyword in diabetes_keywords)
        
        diabetes_result = None
        if is_diabetes_related or any(kw in message_lower for kw in ['glucose', 'bmi', 'blood pressure', 'bp', 'age']):
            try:
                # Get conversation history for context
                chat_history = get_chat_history(session_id)
                diabetes_result = detect_diabetes_from_chat(message, chat_history)
            except Exception as e:
                print(f"Error in diabetes detection: {e}")
        
        # Process query through workflow
        result = workflow_app.invoke(conversation_state)
        conversation_states[session_id].update(result)
        
        # Get current timestamp
        timestamp = datetime.now().strftime("%I:%M %p")
        
        # Extract response and source
        response = result.get('generation', 'Unable to generate response.')
        source = result.get('source', 'Unknown')
        
        # Add diabetes detection result if available
        if diabetes_result and diabetes_result.get('success'):
            diabetes_msg = diabetes_result.get('message', '')
            if diabetes_msg and diabetes_msg not in response:
                response += f"\n\n🔍 **Diabetes Risk Assessment:** {diabetes_msg}"
                if source == 'Unknown':
                    source = 'AI Medical Knowledge + Diabetes Risk Assessment'
        
        # Save assistant response to database
        save_message(session_id, 'assistant', response, source, user_id=user_id)
        
        # Prepare response with diabetes detection info
        response_data = {
            'response': response,
            'source': source,
            'timestamp': timestamp,
            'success': bool(result.get('generation'))
        }
        
        # Add diabetes detection data if available
        if diabetes_result and diabetes_result.get('success'):
            response_data['diabetes_detection'] = {
                'has_risk': diabetes_result.get('has_risk', False),
                'probability': diabetes_result.get('probability', 0.0),
                'features': diabetes_result.get('features', {})
            }
        
        return jsonify(response_data)
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(f"Error in /api/chat: {error_msg}")
        print(traceback_str)
        return jsonify({
            'error': error_msg,
            'traceback': traceback_str if app.debug else None
        }), 500

@app.route('/api/history', methods=['GET'])
@login_required
def get_history():
    """Get chat history for current session"""
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'messages': []})
    
    messages = get_chat_history(session_id)
    return jsonify({'messages': messages, 'success': True})

@app.route('/api/sessions', methods=['GET'])
@login_required
def get_sessions():
    """Get all chat sessions for current user"""
    user_id = session.get('user_id')
    sessions = get_user_sessions(user_id)
    return jsonify({'sessions': sessions, 'success': True})

@app.route('/api/session/<session_id>', methods=['GET'])
def load_session(session_id):
    """Load a specific chat session"""
    session['session_id'] = session_id
    messages = get_chat_history(session_id)
    return jsonify({
        'messages': messages,
        'session_id': session_id,
        'success': True
    })

@app.route('/api/session/<session_id>', methods=['DELETE'])
def delete_chat_session(session_id):
    """Delete a chat session"""
    delete_session(session_id)
    
    # If current session was deleted, create new one
    if session.get('session_id') == session_id:
        session['session_id'] = str(uuid.uuid4())
    
    return jsonify({'message': 'Session deleted', 'success': True})

@app.route('/api/clear', methods=['POST'])
def clear():
    """Clear current conversation (in memory only, doesn't delete from DB)"""
    session_id = session.get('session_id')
    if session_id in conversation_states:
        conversation_states[session_id] = initialize_conversation_state()
    return jsonify({'message': 'Conversation cleared', 'success': True})

@app.route('/api/new-chat', methods=['POST'])
def new_chat():
    """Create a new chat session"""
    new_session_id = str(uuid.uuid4())
    session['session_id'] = new_session_id
    return jsonify({
        'message': 'New chat created',
        'session_id': new_session_id,
        'success': True
    })

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'MediGenius'})

# Doctor Registration Route
@app.route('/register-doctor', methods=['GET', 'POST'])
def register_doctor():
    if request.method == 'POST':
        data = request.json
        username = data.get('username', '')
        email = data.get('email', '')
        password = data.get('password', '')
        
        if not username or not email or not password:
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
        
        result = create_user(username, email, password, role='doctor')
        
        if result['success']:
            session['user_id'] = result['user_id']
            session['username'] = result['username']
            session['email'] = email
            session['role'] = 'doctor'
            return jsonify({
                'success': True,
                'message': 'Doctor registration successful',
                'user': {
                    'username': result['username'],
                    'email': email,
                    'role': 'doctor'
                }
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 400
    
    # GET request - show doctor registration page
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('register_doctor.html')

# Patient Report Routes
@app.route('/submit-report', methods=['GET', 'POST'])
@login_required
def submit_report():
    if request.method == 'POST':
        if session.get('role') != 'patient':
            return jsonify({'success': False, 'error': 'Only patients can submit reports'}), 403
        
        data = request.json
        title = data.get('title', '')
        symptoms = data.get('symptoms', '')
        description = data.get('description', '')
        
        if not title or not symptoms:
            return jsonify({'success': False, 'error': 'Title and symptoms are required'}), 400
        
        result = create_patient_report(session['user_id'], title, symptoms, description)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Report submitted successfully',
                'report_id': result['report_id']
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 400
    
    # GET request - show report submission page
    if session.get('role') != 'patient':
        return redirect(url_for('index'))
    return render_template('submit_report.html')

@app.route('/api/my-reports', methods=['GET'])
@login_required
def get_my_reports():
    """Get reports for the current user"""
    user_id = session.get('user_id')
    role = session.get('role')
    
    if role == 'patient':
        reports = get_patient_reports(patient_id=user_id)
    elif role == 'doctor':
        reports = get_patient_reports(doctor_id=user_id)
    else:
        return jsonify({'success': False, 'error': 'Invalid role'}), 403
    
    return jsonify({'success': True, 'reports': reports})

# Doctor Dashboard Routes
@app.route('/doctor-dashboard', methods=['GET'])
@login_required
def doctor_dashboard():
    """Doctor dashboard to view and manage patient reports"""
    if session.get('role') != 'doctor':
        return redirect(url_for('index'))
    return render_template('doctor_dashboard.html')

@app.route('/api/pending-reports', methods=['GET'])
@login_required
def get_pending_reports_api():
    """Get all pending reports (for doctors)"""
    if session.get('role') != 'doctor':
        return jsonify({'success': False, 'error': 'Only doctors can access this'}), 403
    
    reports = get_pending_reports()
    return jsonify({'success': True, 'reports': reports})

@app.route('/api/assigned-reports', methods=['GET'])
@login_required
def get_assigned_reports_api():
    """Get reports assigned to the current doctor"""
    if session.get('role') != 'doctor':
        return jsonify({'success': False, 'error': 'Only doctors can access this'}), 403
    
    reports = get_assigned_reports(session['user_id'])
    return jsonify({'success': True, 'reports': reports})

@app.route('/api/assign-report/<int:report_id>', methods=['POST'])
@login_required
def assign_report(report_id):
    """Assign a report to the current doctor"""
    if session.get('role') != 'doctor':
        return jsonify({'success': False, 'error': 'Only doctors can assign reports'}), 403
    
    result = assign_report_to_doctor(report_id, session['user_id'])
    
    if result['success']:
        return jsonify({'success': True, 'message': 'Report assigned successfully'})
    else:
        return jsonify({'success': False, 'error': result['error']}), 400

# Prescription Routes
@app.route('/api/prescribe/<int:report_id>', methods=['POST'])
@login_required
def create_prescription_api(report_id):
    """Create a prescription for a patient report"""
    if session.get('role') != 'doctor':
        return jsonify({'success': False, 'error': 'Only doctors can create prescriptions'}), 403
    
    data = request.json
    prescription_text = data.get('prescription_text', '')
    medications = data.get('medications', '')
    dosage = data.get('dosage', '')
    instructions = data.get('instructions', '')
    
    if not prescription_text:
        return jsonify({'success': False, 'error': 'Prescription text is required'}), 400
    
    # Get report to find patient_id
    reports = get_patient_reports()
    report = next((r for r in reports if r['id'] == report_id), None)
    
    if not report:
        return jsonify({'success': False, 'error': 'Report not found'}), 404
    
    if report['doctor_id'] != session['user_id']:
        return jsonify({'success': False, 'error': 'You can only prescribe for your assigned reports'}), 403
    
    result = create_prescription(
        report_id, session['user_id'], report['patient_id'],
        prescription_text, medications, dosage, instructions
    )
    
    if result['success']:
        return jsonify({
            'success': True,
            'message': 'Prescription created successfully',
            'prescription_id': result['prescription_id']
        })
    else:
        return jsonify({'success': False, 'error': result['error']}), 400

@app.route('/api/my-prescriptions', methods=['GET'])
@login_required
def get_my_prescriptions():
    """Get prescriptions for the current user"""
    try:
        user_id = session.get('user_id')
        role = session.get('role')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        if not role:
            print(f"ERROR: User {user_id} has no role")
            return jsonify({'success': False, 'error': 'User role not found'}), 403
        
        print(f"Getting prescriptions for user_id={user_id}, role={role}")
        
        try:
            if role == 'patient':
                prescriptions = get_prescriptions(patient_id=user_id)
            elif role == 'doctor':
                prescriptions = get_prescriptions(doctor_id=user_id)
            else:
                print(f"ERROR: Invalid role '{role}' for user {user_id}")
                return jsonify({'success': False, 'error': f'Invalid role: {role}'}), 403
            
            prescription_count = len(prescriptions) if prescriptions else 0
            print(f"Found {prescription_count} prescriptions for user_id={user_id}, role={role}")
            
            # Ensure we return an array
            result = {'success': True, 'prescriptions': prescriptions if prescriptions else []}
            print(f"Returning response with {len(result['prescriptions'])} prescriptions")
            return jsonify(result)
        except Exception as e:
            print(f"ERROR in get_prescriptions call: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    except Exception as e:
        import traceback
        error_msg = f"Error in get_my_prescriptions: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

@app.route('/prescriptions', methods=['GET'])
@login_required
def view_prescriptions():
    """View prescriptions page for patients"""
    if session.get('role') != 'patient':
        return redirect(url_for('index'))
    return render_template('prescriptions.html')

@app.route('/api/prescription/<int:prescription_id>', methods=['GET'])
@login_required
def get_prescription_details(prescription_id):
    """Get details of a specific prescription"""
    user_id = session.get('user_id')
    role = session.get('role')
    
    prescriptions = get_prescriptions(patient_id=user_id if role == 'patient' else None,
                                     doctor_id=user_id if role == 'doctor' else None)
    
    prescription = next((p for p in prescriptions if p['id'] == prescription_id), None)
    
    if not prescription:
        return jsonify({'success': False, 'error': 'Prescription not found'}), 404
    
    # Check if user has access
    if role == 'patient' and prescription['patient_id'] != user_id:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    if role == 'doctor' and prescription['doctor_id'] != user_id:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    return jsonify({'success': True, 'prescription': prescription})

@app.route('/api/prescription/<int:prescription_id>/download', methods=['GET'])
@login_required
def download_prescription_pdf(prescription_id):
    """Download prescription as PDF"""
    user_id = session.get('user_id')
    role = session.get('role')
    
    prescriptions = get_prescriptions(patient_id=user_id if role == 'patient' else None,
                                     doctor_id=user_id if role == 'doctor' else None)
    
    prescription = next((p for p in prescriptions if p['id'] == prescription_id), None)
    
    if not prescription:
        return jsonify({'success': False, 'error': 'Prescription not found'}), 404
    
    # Check if user has access
    if role == 'patient' and prescription['patient_id'] != user_id:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    if role == 'doctor' and prescription['doctor_id'] != user_id:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    # Generate PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#4CAF50'),
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Build PDF content
    elements.append(Paragraph("MediGenius", title_style))
    elements.append(Paragraph("Medical Prescription", styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Patient Information
    elements.append(Paragraph("<b>Patient Information</b>", heading_style))
    patient_info = [
        ['Patient Name:', prescription.get('patient_name', 'N/A')],
        ['Prescription Date:', prescription.get('created_at', 'N/A')]
    ]
    patient_table = Table(patient_info, colWidths=[2*inch, 4*inch])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(patient_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Prescription Details
    elements.append(Paragraph("<b>Prescription Details</b>", heading_style))
    elements.append(Paragraph(prescription.get('prescription_text', 'N/A'), styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Medications
    if prescription.get('medications'):
        elements.append(Paragraph("<b>Medications</b>", heading_style))
        elements.append(Paragraph(prescription.get('medications', 'N/A'), styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
    
    # Dosage
    if prescription.get('dosage'):
        elements.append(Paragraph("<b>Dosage</b>", heading_style))
        elements.append(Paragraph(prescription.get('dosage', 'N/A'), styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
    
    # Instructions
    if prescription.get('instructions'):
        elements.append(Paragraph("<b>Instructions</b>", heading_style))
        elements.append(Paragraph(prescription.get('instructions', 'N/A'), styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
    
    # Doctor Information
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Prescribed By</b>", heading_style))
    doctor_info = [
        ['Doctor Name:', prescription.get('doctor_name', 'N/A')],
        ['Report Title:', prescription.get('report_title', 'N/A')]
    ]
    doctor_table = Table(doctor_info, colWidths=[2*inch, 4*inch])
    doctor_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f5e9')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(doctor_table)
    
    # Footer
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("<i>This is a computer-generated prescription. Please consult with your healthcare provider for any questions.</i>", 
                              ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=1)))
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF data
    buffer.seek(0)
    
    # Create filename
    filename = f"prescription_{prescription_id}_{prescription.get('patient_name', 'patient').replace(' ', '_')}.pdf"
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

# Medication Reminder Routes
@app.route('/api/reminders', methods=['GET'])
@login_required
def get_reminders():
    """Get medication reminders for current patient"""
    if session.get('role') != 'patient':
        return jsonify({'success': False, 'error': 'Only patients can access reminders'}), 403
    
    reminders = get_patient_reminders(session['user_id'])
    return jsonify({'success': True, 'reminders': reminders})

@app.route('/api/reminders', methods=['POST'])
@login_required
def create_reminder():
    """Create a medication reminder"""
    if session.get('role') != 'patient':
        return jsonify({'success': False, 'error': 'Only patients can create reminders'}), 403
    
    data = request.json
    prescription_id = data.get('prescription_id')
    medication_name = data.get('medication_name', '')
    reminder_time = data.get('reminder_time', '')
    frequency = data.get('frequency', 'daily')
    
    if not prescription_id or not medication_name or not reminder_time:
        return jsonify({'success': False, 'error': 'Prescription ID, medication name, and reminder time are required'}), 400
    
    result = create_medication_reminder(
        prescription_id, session['user_id'], medication_name, reminder_time, frequency
    )
    
    if result['success']:
        return jsonify({
            'success': True,
            'message': 'Reminder created successfully',
            'reminder_id': result['reminder_id']
        })
    else:
        return jsonify({'success': False, 'error': result['error']}), 400

@app.route('/api/reminders/<int:reminder_id>', methods=['DELETE'])
@login_required
def delete_reminder_route(reminder_id):
    """Delete a medication reminder"""
    if session.get('role') != 'patient':
        return jsonify({'success': False, 'error': 'Only patients can delete reminders'}), 403
    
    result = delete_reminder(reminder_id, session['user_id'])
    
    if result['success']:
        return jsonify({'success': True, 'message': 'Reminder deleted successfully'})
    else:
        return jsonify({'success': False, 'error': result.get('error', 'Failed to delete reminder')}), 400

@app.route('/medication-reminders', methods=['GET'])
@login_required
def medication_reminders_page():
    """Medication reminders management page"""
    if session.get('role') != 'patient':
        return redirect(url_for('index'))
    return render_template('medication_reminders.html')

@app.route('/api/submit-conversation', methods=['POST'])
@login_required
def submit_conversation():
    """Submit current conversation as a patient report"""
    if session.get('role') != 'patient':
        return jsonify({'success': False, 'error': 'Only patients can submit conversations'}), 403
    
    data = request.json
    session_id = session.get('session_id')
    title = data.get('title', '')
    
    if not session_id:
        return jsonify({'success': False, 'error': 'No active conversation'}), 400
    
    # Get conversation history
    messages = get_chat_history(session_id)
    
    if not messages:
        return jsonify({'success': False, 'error': 'No messages in conversation'}), 400
    
    # Extract user messages (symptoms/questions) and AI responses
    # messages is a list of dicts with 'role' and 'content' keys
    user_messages = [msg['content'] for msg in messages if msg.get('role') == 'user']
    ai_responses = [msg['content'] for msg in messages if msg.get('role') == 'assistant']
    
    if not user_messages:
        return jsonify({'success': False, 'error': 'No user messages found'}), 400
    
    # Combine user messages as symptoms
    symptoms = '\n\n'.join([f"Question {i+1}: {msg}" for i, msg in enumerate(user_messages)])
    
    # Combine AI responses as additional description
    description = '\n\n'.join([f"AI Response {i+1}: {msg}" for i, msg in enumerate(ai_responses)])
    
    # Use provided title or generate one
    if not title:
        # Generate title from first user message
        first_message = user_messages[0]
        title = first_message[:50] + '...' if len(first_message) > 50 else first_message
    
    # Create patient report
    result = create_patient_report(
        session['user_id'],
        title,
        symptoms,
        description
    )
    
    if result['success']:
        return jsonify({
            'success': True,
            'message': 'Conversation submitted successfully. A doctor will review it soon.',
            'report_id': result['report_id']
        })
    else:
        return jsonify({'success': False, 'error': result['error']}), 400

if __name__ == '__main__':
    initialize_system()
    # Bind to 0.0.0.0 to make it accessible from outside the container
    # In production, gunicorn will handle this
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)