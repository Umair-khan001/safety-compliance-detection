# Safety Compliance Detection System - Authentication Implementation Guide

## Project Overview
This guide provides complete implementation details for adding a robust login/registration system to your Safety Compliance Detection System with admin approval workflow.

## Database Architecture

### Recommended Database: PostgreSQL
**Why PostgreSQL?**
- Excellent for user authentication systems
- ACID compliance for data integrity
- Built-in UUID support for secure session management
- Advanced indexing for fast user lookups
- JSON support for storing user activity logs
- Robust security features
- Scalable for production deployment

### Database Schema Design

#### 1. Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'customer' CHECK (role IN ('admin', 'customer')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'suspended')),
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_date TIMESTAMP NULL,
    approved_by INTEGER REFERENCES users(id),
    last_login TIMESTAMP NULL,
    profile_image_url VARCHAR(500),
    phone VARCHAR(20),
    company VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_role ON users(role);
```

#### 2. User Sessions Table
```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_expires ON user_sessions(expires_at);
```

#### 3. User Activity Logs Table
```sql
CREATE TABLE user_activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL,
    description TEXT,
    video_filename VARCHAR(255),
    detection_results JSON,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_activity_user_id ON user_activity_logs(user_id);
CREATE INDEX idx_activity_type ON user_activity_logs(activity_type);
CREATE INDEX idx_activity_date ON user_activity_logs(created_at);
```

#### 4. Detection Sessions Table
```sql
CREATE TABLE detection_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_type VARCHAR(20) CHECK (session_type IN ('webcam', 'video_upload')),
    video_filename VARCHAR(255),
    confidence_threshold DECIMAL(3,2),
    total_detections INTEGER DEFAULT 0,
    safe_detections INTEGER DEFAULT 0,
    unsafe_detections INTEGER DEFAULT 0,
    session_duration INTEGER, -- in seconds
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'failed')),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL
);

CREATE INDEX idx_detection_user_id ON detection_sessions(user_id);
CREATE INDEX idx_detection_type ON detection_sessions(session_type);
CREATE INDEX idx_detection_date ON detection_sessions(started_at);
```

## Flask Authentication Implementation

### Required Libraries
```bash
pip install flask-login flask-bcrypt flask-wtf wtforms email-validator psycopg2-binary flask-sqlalchemy
```

### Flask App Configuration
```python
# Add to flaskApp.py imports
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from wtforms import StringField, PasswordField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo
import uuid
from datetime import datetime, timedelta

# Add to app configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access the detection system.'
```

### Database Models
```python
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    role = db.Column(db.String(20), default='customer')
    status = db.Column(db.String(20), default='pending')
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    approved_date = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    last_login = db.Column(db.DateTime)
    phone = db.Column(db.String(20))
    company = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sessions = db.relationship('UserSession', backref='user', lazy=True, cascade='all, delete-orphan')
    activity_logs = db.relationship('UserActivityLog', backref='user', lazy=True, cascade='all, delete-orphan')
    detection_sessions = db.relationship('DetectionSession', backref='user', lazy=True, cascade='all, delete-orphan')

class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserActivityLog(db.Model):
    __tablename__ = 'user_activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    video_filename = db.Column(db.String(255))
    detection_results = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DetectionSession(db.Model):
    __tablename__ = 'detection_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_type = db.Column(db.String(20), nullable=False)
    video_filename = db.Column(db.String(255))
    confidence_threshold = db.Column(db.Numeric(3,2))
    total_detections = db.Column(db.Integer, default=0)
    safe_detections = db.Column(db.Integer, default=0)
    unsafe_detections = db.Column(db.Integer, default=0)
    session_duration = db.Column(db.Integer)
    status = db.Column(db.String(20), default='active')
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
```

### Forms
```python
class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=100)])
    phone = StringField('Phone Number', validators=[Length(max=20)])
    company = StringField('Company/Organization', validators=[Length(max=200)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class UserApprovalForm(FlaskForm):
    status = SelectField('Status', choices=[('approved', 'Approve'), ('rejected', 'Reject')], 
                        validators=[DataRequired()])
    admin_notes = TextAreaField('Admin Notes', validators=[Length(max=500)])
    submit = SubmitField('Update Status')
```

### Authentication Routes
```python
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            if user.status == 'approved':
                login_user(user)
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                # Log login activity
                log_user_activity(user.id, 'login', 'User logged in successfully')
                
                # Redirect based on role
                if user.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('front'))
            elif user.status == 'pending':
                flash('Your account is pending admin approval.', 'warning')
            elif user.status == 'rejected':
                flash('Your account has been rejected. Please contact support.', 'danger')
            elif user.status == 'suspended':
                flash('Your account has been suspended. Please contact support.', 'danger')
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter((User.email == form.email.data) | 
                                        (User.username == form.username.data)).first()
        if existing_user:
            flash('Email or username already exists.', 'danger')
            return render_template('register.html', form=form)
        
        # Create new user
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            email=form.email.data,
            username=form.username.data,
            password_hash=hashed_password,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            company=form.company.data
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please wait for admin approval.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    log_user_activity(current_user.id, 'logout', 'User logged out')
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

def log_user_activity(user_id, activity_type, description, video_filename=None, detection_results=None):
    """Helper function to log user activities"""
    activity = UserActivityLog(
        user_id=user_id,
        activity_type=activity_type,
        description=description,
        video_filename=video_filename,
        detection_results=detection_results,
        ip_address=request.environ.get('HTTP_X_REAL_IP', request.remote_addr),
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(activity)
    db.session.commit()
```

### Admin Dashboard Routes
```python
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('front'))
    
    # Get pending registrations
    pending_users = User.query.filter_by(status='pending').all()
    
    # Get system statistics
    total_users = User.query.count()
    approved_users = User.query.filter_by(status='approved').count()
    recent_activity = UserActivityLog.query.order_by(UserActivityLog.created_at.desc()).limit(10).all()
    
    return render_template('admin_dashboard.html', 
                         pending_users=pending_users,
                         total_users=total_users,
                         approved_users=approved_users,
                         recent_activity=recent_activity)

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('front'))
    
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/approve_user/<int:user_id>', methods=['POST'])
@login_required
def approve_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    user = User.query.get_or_404(user_id)
    user.status = 'approved'
    user.approved_date = datetime.utcnow()
    user.approved_by = current_user.id
    
    db.session.commit()
    
    # Log admin action
    log_user_activity(current_user.id, 'user_approval', f'Approved user: {user.email}')
    
    return jsonify({'success': True, 'message': f'User {user.email} approved successfully'})

@app.route('/admin/reject_user/<int:user_id>', methods=['POST'])
@login_required
def reject_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    user = User.query.get_or_404(user_id)
    user.status = 'rejected'
    
    db.session.commit()
    
    # Log admin action
    log_user_activity(current_user.id, 'user_rejection', f'Rejected user: {user.email}')
    
    return jsonify({'success': True, 'message': f'User {user.email} rejected'})
```

### Protected Routes Modification
```python
# Modify existing routes to require authentication
@app.route('/FrontPage', methods=['GET','POST'])
@login_required
def front():
    if current_user.status != 'approved':
        flash('Your account is not approved yet.', 'warning')
        return redirect(url_for('login'))
    
    # Log access
    log_user_activity(current_user.id, 'page_access', 'Accessed detection system')
    
    form = UploadFileForm()
    if form.validate_on_submit():
        file = form.file.data
        conf_ = form.conf_slide.data

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        session['video_path'] = file_path
        session['conf_'] = conf_
        
        # Log video upload
        log_user_activity(current_user.id, 'video_upload', f'Uploaded video: {filename}', filename)
        
        # Create detection session
        detection_session = DetectionSession(
            user_id=current_user.id,
            session_type='video_upload',
            video_filename=filename,
            confidence_threshold=conf_/100
        )
        db.session.add(detection_session)
        db.session.commit()
        
        session['detection_session_id'] = detection_session.id

        return render_template('video.html', form=form)
    return render_template('video.html', form=form)
```

## Web UI Database Management Tools

### Recommended Tools:

1. **pgAdmin** (Recommended)
   - Full-featured PostgreSQL administration
   - Web-based interface
   - User management, query editor, monitoring
   - Install: https://www.pgadmin.org/

2. **Adminer** (Lightweight)
   - Single PHP file
   - Works with multiple database systems
   - Simple setup: Download adminer.php to web directory

3. **DBeaver** (Desktop Application)
   - Free universal database tool
   - Advanced query capabilities
   - Data visualization

## Security Best Practices

### Password Security
```python
# Use strong password hashing
BCRYPT_LOG_ROUNDS = 12  # Increase for better security

# Password validation
def validate_password_strength(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"
```

### Session Security
```python
# Session configuration
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent XSS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
```

### Rate Limiting
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Apply to login route
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    # ... existing login code
```

## Implementation Steps

### Step 1: Database Setup
1. Create PostgreSQL database
2. Run schema creation scripts
3. Create initial admin user

### Step 2: Flask App Modifications
1. Install required packages
2. Add authentication models
3. Update routes with authentication
4. Create login/registration templates

### Step 3: Admin Panel
1. Create admin dashboard templates
2. Implement user management functions
3. Add activity monitoring

### Step 4: Security Implementation
1. Add password validation
2. Implement session management
3. Add rate limiting
4. Setup HTTPS (production)

### Step 5: Testing
1. Test registration flow
2. Test admin approval process
3. Test protected routes
4. Test session management

## File Structure
```
project/
├── flaskApp.py (modified)
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── admin_dashboard.html
│   ├── admin_users.html
│   └── video.html (modified)
├── static/
│   ├── css/
│   └── js/
├── config.env (updated)
└── requirements.txt (updated)
```

This documentation provides a complete roadmap for implementing a robust authentication system that integrates seamlessly with your existing Safety Compliance Detection System while maintaining security best practices and consistent styling.