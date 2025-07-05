# Quick Start: Authentication Integration

## Files You Need to Download/Copy

From this development environment, copy these files to your project:

### 1. Main Application (Replace your flaskApp.py)
- `client/auth_flask_app.py` → Copy content to your `flaskApp.py`

### 2. Templates (Add to your templates/ folder)
- `client/templates/login.html`
- `client/templates/register.html`
- `client/templates/admin_dashboard.html` 
- `client/templates/admin_users.html`
- `client/video.html` → Replace your existing `templates/video.html`

### 3. Configuration Files
- `client/config.env` → Create as `.env` in your project root
- `updated_requirements.txt` → Add these dependencies to your existing requirements.txt

## Immediate Setup Commands

```bash
# 1. Backup your current files
copy flaskApp.py flaskApp_backup.py
copy templates\video.html templates\video_backup.html

# 2. Install new dependencies
pip install flask flask-wtf wtforms psycopg2-binary werkzeug python-dotenv

# 3. Create .env file in project root with:
DATABASE_URL=sqlite:///safety_app.db
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
ADMIN_EMAIL=admin@safety.com
ADMIN_PASSWORD=admin123

# 4. Create uploads directory
mkdir static\uploads

# 5. Run your app
python flaskApp.py
```

## What Happens After Integration

**Before:** Direct access to video detection interface
**After:** Login required → Admin approval → Access granted

**Default Admin Login:**
- Email: admin@safety.com
- Password: admin123

## Database Options

**Quick Testing (SQLite):**
```
DATABASE_URL=sqlite:///safety_app.db
```

**Production (PostgreSQL):**
```
DATABASE_URL=postgresql://username:password@localhost:5432/dbname
```

## Project Structure After Integration

```
your_project/
├── flaskApp.py (authentication-enabled)
├── .env (database config)
├── templates/
│   ├── video.html (login-protected)
│   ├── login.html
│   ├── register.html
│   ├── admin_dashboard.html
│   └── admin_users.html
├── static/
│   └── uploads/ (ensure exists)
└── requirements.txt (updated)
```

## First Time Setup Flow

1. Start application: `python flaskApp.py`
2. Visit `http://localhost:5000`
3. See login screen (not direct access)
4. Click "Register" → Create user account
5. Login as admin → Approve new users
6. Users can now access video detection

## Key Authentication Features

- User registration with admin approval
- Secure login/logout
- Protected video detection interface
- Admin dashboard for user management
- Activity logging and session tracking
- All existing PPE detection functionality preserved

The authentication system is now a protective layer around your existing video detection system, maintaining all original functionality while adding user security and access control.