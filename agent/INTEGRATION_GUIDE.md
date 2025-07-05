# Authentication System Integration Guide

## Current Project Structure Analysis
```
your_project/
├── flaskApp.py (existing - main app)
├── templates/ (existing)
├── static/ (existing)
├── requirements.txt (existing)
└── ... (other directories)
```

## Integration Steps

### 1. File Placement Guide

**Main Application Files:**
- Keep your existing `flaskApp.py` as the main entry point
- Replace the content with the authentication-enabled version
- The authentication app (`auth_flask_app.py`) contains the full integrated system

**Template Files to Add:**
```
templates/
├── video.html (replace existing with authenticated version)
├── login.html (new)
├── register.html (new)
├── admin_dashboard.html (new)
└── admin_users.html (new)
```

**Configuration Files:**
```
├── config.env (new - environment variables)
└── requirements.txt (update with auth dependencies)
```

### 2. Database Setup Instructions

**Option A: Local PostgreSQL (Recommended for Development)**
1. Install PostgreSQL on your system
2. Create a database: `createdb safety_compliance_db`
3. Update config.env with your database credentials
4. Run the Flask app to auto-create tables

**Option B: Use Existing Database Service**
1. If you have a PostgreSQL service, get the connection string
2. Set DATABASE_URL in your environment
3. Tables will be created automatically on first run

### 3. Environment Setup

**Install Required Packages:**
```bash
pip install flask flask-wtf wtforms psycopg2-binary werkzeug
```

**Environment Variables:**
Create a `.env` file in your project root with:
```
DATABASE_URL=postgresql://username:password@localhost:5432/safety_compliance_db
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
```

### 4. Integration Process

**Step 1:** Replace `flaskApp.py` with authentication-enabled version
**Step 2:** Add new template files to your `templates/` directory
**Step 3:** Update `requirements.txt` with authentication dependencies
**Step 4:** Set up database and environment variables
**Step 5:** Test the authentication system

### 5. File Priorities (Start with these)

1. **requirements.txt** - Update dependencies first
2. **config.env** - Set up configuration
3. **flaskApp.py** - Replace with auth-enabled version
4. **templates/video.html** - Replace with protected version
5. **templates/login.html** - Add login interface
6. **templates/register.html** - Add registration interface

### 6. Database Schema

The system will automatically create these tables:
- `users` - User accounts and authentication
- `user_activity_logs` - Activity tracking
- `detection_sessions` - Video processing sessions

### 7. Default Admin Account

After setup, you can login with:
- Email: admin@safety.com
- Password: admin123
- This admin can approve new user registrations

### 8. Testing the Integration

1. Start your Flask app: `python flaskApp.py`
2. Visit the application URL
3. You should see login/registration forms
4. Register a new user account
5. Login as admin to approve users
6. Test the video detection interface with authenticated users

## Next Steps

1. Update your requirements.txt
2. Set up the database
3. Replace your main Flask app file
4. Add the template files
5. Test the authentication flow