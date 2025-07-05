# Step-by-Step Authentication Integration

## STEP 1: Backup Your Current Project
```bash
# Create backup of your current flaskApp.py
copy flaskApp.py flaskApp_backup.py

# Backup your current video.html
copy templates\video.html templates\video_backup.html
```

## STEP 2: Install Dependencies
```bash
# Update your requirements.txt by adding these lines:
pip install flask flask-wtf wtforms psycopg2-binary werkzeug python-dotenv
```

## STEP 3: Set Up Database

### Quick Option - Use SQLite (for testing):
Create `.env` file in your project root:
```env
DATABASE_URL=sqlite:///safety_app.db
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=development
ADMIN_EMAIL=admin@safety.com
ADMIN_PASSWORD=admin123
```

### Production Option - PostgreSQL:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/safety_db
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=development
ADMIN_EMAIL=admin@safety.com
ADMIN_PASSWORD=admin123
```

## STEP 4: Replace Your Main Flask App

Replace the content of your `flaskApp.py` with the authentication-enabled version. 
Key changes to make:
1. Import authentication modules
2. Add user management routes
3. Protect your existing video detection routes with `@login_required`
4. Add database initialization

## STEP 5: Update Templates Directory

Add these new template files to your `templates/` folder:
- `login.html` - User login form
- `register.html` - User registration form  
- `admin_dashboard.html` - Admin control panel
- `admin_users.html` - User management interface

Replace your existing `templates/video.html` with the authentication-protected version.

## STEP 6: Create Required Directories
```bash
# Create uploads directory if it doesn't exist
mkdir static\uploads

# Create logs directory (optional)
mkdir logs
```

## STEP 7: Run Database Initialization

Start your Flask app - it will automatically create the required database tables:
```bash
python flaskApp.py
```

Look for these success messages:
- "Database connection successful"
- "Admin user created"
- "Tables created successfully"

## STEP 8: Test the Integration

1. Open your browser to `http://localhost:5000`
2. You should see login/registration forms instead of direct access
3. Register a new user account
4. Login with admin credentials:
   - Email: admin@safety.com
   - Password: admin123
5. Approve the new user in admin dashboard
6. Test video detection with authenticated user

## STEP 9: Verify Your Existing Features

Ensure these still work:
- Video file upload
- PPE detection processing
- Results display
- Statistics tracking
- Export functionality

## File Structure After Integration

```
your_project/
├── flaskApp.py (updated with authentication)
├── templates/
│   ├── video.html (authentication-protected)
│   ├── login.html (new)
│   ├── register.html (new)
│   ├── admin_dashboard.html (new)
│   └── admin_users.html (new)
├── static/
│   ├── uploads/ (ensure this exists)
│   └── ... (your existing static files)
├── .env (new - database config)
├── requirements.txt (updated)
└── ... (your other files remain unchanged)
```

## Key Integration Points

**Authentication Protection:**
- All video detection routes now require login
- User session management
- Admin approval workflow

**Database Integration:**
- User accounts and authentication
- Activity logging
- Session tracking

**UI Integration:**
- Login/logout in header
- User welcome messages
- Admin controls for user management

## Troubleshooting Common Issues

**Database Connection:**
- Verify .env file is in project root
- Check database credentials
- Ensure PostgreSQL service is running (if using PostgreSQL)

**Import Errors:**
- Install missing dependencies: `pip install -r requirements.txt`
- Check Python path

**Template Errors:**
- Verify all template files are in templates/ directory
- Check template syntax

**Permission Issues:**
- Ensure uploads directory is writable
- Check file permissions

## Next Steps After Integration

1. Test all existing functionality
2. Customize admin dashboard if needed
3. Configure email notifications (optional)
4. Set up production database
5. Deploy with proper security settings