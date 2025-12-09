# Authentication System Guide

## Overview

Registration and login functionality has been successfully added to MediGenius. Users must now register and login to access the application.

## Features

✅ **User Registration**
- Create account with username, email, and password
- Password hashing with bcrypt
- Email and username uniqueness validation
- Minimum password length: 6 characters

✅ **User Login**
- Login with username or email
- Secure password verification
- Session management
- Auto-redirect after login

✅ **Protected Routes**
- All chat features require authentication
- Automatic redirect to login if not authenticated
- User-specific chat sessions

✅ **User Management**
- View current user information
- Logout functionality
- User-specific chat history

## Database Changes

### New Table: `users`
- `id` - Primary key
- `username` - Unique username
- `email` - Unique email address
- `password_hash` - Hashed password (bcrypt)
- `created_at` - Account creation timestamp
- `last_login` - Last login timestamp

### Updated Table: `sessions`
- Added `user_id` column to link sessions to users
- Sessions are now user-specific

## API Endpoints

### Authentication Endpoints

**POST /register**
- Register a new user
- Request: `{ "username": "...", "email": "...", "password": "..." }`
- Response: `{ "success": true, "user": {...} }`

**POST /login**
- Login with username/email and password
- Request: `{ "username": "...", "password": "..." }`
- Response: `{ "success": true, "user": {...} }`

**POST /logout**
- Logout current user
- Clears session

**GET /api/user**
- Get current user information
- Requires authentication

### Protected Endpoints
All chat endpoints now require authentication:
- `/api/chat` - Send messages
- `/api/history` - Get chat history
- `/api/sessions` - Get user's chat sessions

## Usage

### For Users

1. **Register**: Visit `/register` or click "Register here" on login page
2. **Login**: Visit `/login` or access any protected route (auto-redirect)
3. **Use App**: After login, all features are available
4. **Logout**: Click the logout button in the header

### For Developers

**Initialize Authentication Database:**
```python
from auth import init_auth_db
init_auth_db()  # Called automatically on app startup
```

**Create User Programmatically:**
```python
from auth import create_user
result = create_user("username", "email@example.com", "password")
```

**Authenticate User:**
```python
from auth import authenticate_user
result = authenticate_user("username", "password")
```

## Security Features

- ✅ Password hashing with bcrypt (via passlib)
- ✅ Session-based authentication
- ✅ Protected routes with `@login_required` decorator
- ✅ User-specific data isolation
- ✅ Secure password validation

## Files Created/Modified

### New Files
- `auth.py` - Authentication utilities
- `templates/login.html` - Login page
- `templates/register.html` - Registration page

### Modified Files
- `app.py` - Added authentication routes and middleware
- `templates/index.html` - Added user info and logout button

## Testing

1. **Test Registration:**
   ```bash
   curl -X POST http://127.0.0.1:5000/register \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","email":"test@example.com","password":"test123"}'
   ```

2. **Test Login:**
   ```bash
   curl -X POST http://127.0.0.1:5000/login \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"test123"}' \
     -c cookies.txt
   ```

3. **Test Protected Route:**
   ```bash
   curl -X GET http://127.0.0.1:5000/api/user \
     -b cookies.txt
   ```

## Notes

- The authentication system uses Flask sessions
- Passwords are hashed using bcrypt (via passlib)
- User sessions are stored server-side
- Chat history is now user-specific
- The database schema is automatically updated on first run

## Troubleshooting

**Issue: "ModuleNotFoundError: No module named 'passlib'**
- Solution: `pip install passlib[bcrypt]`

**Issue: Database errors**
- Solution: Delete `chat_db/medigenius_chats.db` and restart the app (database will be recreated)

**Issue: Can't login after registration**
- Check browser console for errors
- Verify password meets requirements (6+ characters)
- Check server logs for authentication errors



