"""
Email service for sending medication reminders
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Email configuration from environment variables
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
FROM_EMAIL = os.getenv('FROM_EMAIL', SMTP_USERNAME)

def send_medication_reminder(patient_email: str, patient_name: str, medication_name: str, 
                            dosage: str, instructions: str, prescription_text: str) -> bool:
    """Send medication reminder email to patient"""
    
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("Warning: SMTP credentials not configured. Email reminders disabled.")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'MediGenius - Medication Reminder: {medication_name}'
        msg['From'] = FROM_EMAIL
        msg['To'] = patient_email
        
        # Create HTML email body
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: white;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .reminder-box {{
                    background: #e8f5e9;
                    border-left: 4px solid #4CAF50;
                    padding: 15px;
                    margin: 20px 0;
                }}
                .medication-name {{
                    font-size: 1.5em;
                    font-weight: bold;
                    color: #2e7d32;
                    margin-bottom: 10px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    color: #666;
                    font-size: 0.9em;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🩺 MediGenius</h1>
                    <p>Medication Reminder</p>
                </div>
                <div class="content">
                    <h2>Hello {patient_name},</h2>
                    <p>This is a reminder to take your medication:</p>
                    
                    <div class="reminder-box">
                        <div class="medication-name">{medication_name}</div>
                        {f'<p><strong>Dosage:</strong> {dosage}</p>' if dosage else ''}
                        {f'<p><strong>Instructions:</strong> {instructions}</p>' if instructions else ''}
                    </div>
                    
                    {f'<p><strong>Prescription Details:</strong><br>{prescription_text}</p>' if prescription_text else ''}
                    
                    <p style="margin-top: 20px;">
                        <strong>Remember:</strong> It's important to take your medication as prescribed by your doctor.
                    </p>
                    
                    <div class="footer">
                        <p>This is an automated reminder from MediGenius.</p>
                        <p>If you have any questions, please consult with your healthcare provider.</p>
                        <p style="margin-top: 20px;">
                            <a href="http://localhost:5001/prescriptions" class="button">View Prescriptions</a>
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create plain text version
        text_body = f"""
MediGenius - Medication Reminder

Hello {patient_name},

This is a reminder to take your medication:

Medication: {medication_name}
{f'Dosage: {dosage}' if dosage else ''}
{f'Instructions: {instructions}' if instructions else ''}

{f'Prescription Details: {prescription_text}' if prescription_text else ''}

Remember: It's important to take your medication as prescribed by your doctor.

This is an automated reminder from MediGenius.
If you have any questions, please consult with your healthcare provider.
        """
        
        # Attach parts
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"Medication reminder email sent to {patient_email}")
        return True
        
    except Exception as e:
        print(f"Error sending medication reminder email: {e}")
        return False

def create_medication_reminder(prescription_id: int, patient_id: int, medication_name: str,
                              reminder_time: str, frequency: str = 'daily') -> dict:
    """Create a medication reminder entry"""
    import sqlite3
    from auth import DB_PATH
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO medication_reminders 
            (prescription_id, patient_id, medication_name, reminder_time, frequency, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (prescription_id, patient_id, medication_name, reminder_time, frequency))
        
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {'success': True, 'reminder_id': reminder_id}
    except Exception as e:
        conn.close()
        return {'success': False, 'error': str(e)}

def get_patient_reminders(patient_id: int):
    """Get all reminders for a patient"""
    import sqlite3
    from auth import DB_PATH
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT mr.id, mr.prescription_id, mr.medication_name, mr.reminder_time,
               mr.frequency, mr.is_active, mr.last_sent, mr.created_at,
               p.medications, p.dosage, p.instructions, p.prescription_text,
               u.email as patient_email, u.username as patient_name
        FROM medication_reminders mr
        LEFT JOIN prescriptions p ON mr.prescription_id = p.id
        LEFT JOIN users u ON mr.patient_id = u.id
        WHERE mr.patient_id = ? AND mr.is_active = 1
        ORDER BY mr.reminder_time ASC
    ''', (patient_id,))
    
    reminders = []
    for row in cursor.fetchall():
        reminders.append({
            'id': row[0],
            'prescription_id': row[1],
            'medication_name': row[2],
            'reminder_time': row[3],
            'frequency': row[4],
            'is_active': bool(row[5]),
            'last_sent': row[6],
            'created_at': row[7],
            'medications': row[8],
            'dosage': row[9],
            'instructions': row[10],
            'prescription_text': row[11],
            'patient_email': row[12],
            'patient_name': row[13]
        })
    
    conn.close()
    return reminders

def update_reminder_last_sent(reminder_id: int):
    """Update the last_sent timestamp for a reminder"""
    import sqlite3
    from auth import DB_PATH
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE medication_reminders
        SET last_sent = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (reminder_id,))
    
    conn.commit()
    conn.close()

def delete_reminder(reminder_id: int, patient_id: int) -> dict:
    """Delete or deactivate a reminder"""
    import sqlite3
    from auth import DB_PATH
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE medication_reminders
            SET is_active = 0
            WHERE id = ? AND patient_id = ?
        ''', (reminder_id, patient_id))
        
        conn.commit()
        conn.close()
        return {'success': True}
    except Exception as e:
        conn.close()
        return {'success': False, 'error': str(e)}


