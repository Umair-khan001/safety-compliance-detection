# Enhanced Flask Application with Authentication
from flask import Flask, render_template, Response, jsonify, request, session, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, IntegerRangeField, StringField, PasswordField, SelectField, TextAreaField
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired, DataRequired, Email, Length, EqualTo
import os
from flask_bootstrap import Bootstrap
import cv2
import time
import secrets
from dotenv import load_dotenv
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import re
from functools import wraps

# Import your existing detection functions
from hubconfCustom import video_detection, PROCESSED_OUTPUT_DIR

# Load environment variables
load_dotenv(dotenv_path='config.env')

app = Flask(__name__)
Bootstrap(app)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or secrets.token_hex(32)
app.config['UPLOAD_FOLDER'] = 'static/files'
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')

# Ensure directories exist
for directory in ['data', app.config['UPLOAD_FOLDER'], PROCESSED_OUTPUT_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(
            app.config['DATABASE_URL'],
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# Initialize database tables
def init_database():
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
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
                phone VARCHAR(20),
                company VARCHAR(200),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # User activity logs table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_activity_logs (
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
        """)
        
        # Detection sessions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS detection_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                session_type VARCHAR(20) CHECK (session_type IN ('webcam', 'video_upload')),
                video_filename VARCHAR(255),
                confidence_threshold DECIMAL(3,2),
                total_detections INTEGER DEFAULT 0,
                safe_detections INTEGER DEFAULT 0,
                unsafe_detections INTEGER DEFAULT 0,
                session_duration INTEGER,
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'failed')),
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP NULL
            );
        """)
        
        # Create indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_activity_user_id ON user_activity_logs(user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_detection_user_id ON detection_sessions(user_id);")
        
        conn.commit()
        
        # Create default admin user if none exists
        cur.execute("SELECT COUNT(*) FROM users WHERE role = 'admin';")
        admin_count = cur.fetchone()['count']
        
        if admin_count == 0:
            admin_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
            cur.execute("""
                INSERT INTO users (email, username, password_hash, first_name, last_name, role, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, ('admin@safetysystem.com', 'admin', admin_password.decode('utf-8'), 
                  'System', 'Administrator', 'admin', 'approved'))
            conn.commit()
            print("Default admin user created: admin@safetysystem.com / admin123")
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

# Forms
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

class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    conf_slide = IntegerRangeField('Confidence:  ', default=25, validators=[InputRequired()])
    submit = SubmitField("Run")

class ProfileUpdateForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('Phone Number', validators=[Length(max=20)])
    company = StringField('Company/Organization', validators=[Length(max=200)])
    submit = SubmitField('Update Profile')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password', 
                                   validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

# Helper functions
def log_user_activity(user_id, activity_type, description, video_filename=None, detection_results=None):
    """Log user activity to database"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO user_activity_logs 
            (user_id, activity_type, description, video_filename, detection_results, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s, %s)        """, (user_id, activity_type, description, video_filename, 
              detection_results, request.environ.get('HTTP_X_REAL_IP', request.remote_addr),
              request.headers.get('User-Agent')))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error logging activity: {e}")

# Detection Session Management Functions
def create_detection_session(user_id, session_type, video_filename=None, confidence_threshold=0.25):
    """Create a new detection session and return session ID"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO detection_sessions 
            (user_id, session_type, video_filename, confidence_threshold, status, started_at)
            VALUES (%s, %s, %s, %s, 'active', %s)
            RETURNING id
        """, (user_id, session_type, video_filename, confidence_threshold, datetime.now()))
        
        session_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()
        return session_id
    except Exception as e:
        print(f"Error creating detection session: {e}")
        return None

def update_detection_session(session_id, total_detections=0, safe_detections=0, unsafe_detections=0, 
                           status='completed', session_duration=None):
    """Update detection session with results"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE detection_sessions 
            SET total_detections = %s, safe_detections = %s, unsafe_detections = %s,
                status = %s, session_duration = %s, completed_at = %s
            WHERE id = %s
        """, (total_detections, safe_detections, unsafe_detections, status, 
              session_duration, datetime.now(), session_id))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating detection session: {e}")
        return False

def get_session_stats():
    """Get current detection counts for session tracking"""
    global detect_count, safe_count
    try:
        total = int(detect_count) if detect_count else 0
        safe = int(safe_count) if safe_count else 0
        unsafe = total - safe if total >= safe else 0
        return total, safe, unsafe
    except:
        return 0, 0, 0

def get_current_user():
    """Get current user from session (cached version for performance)"""
    if 'user_id' not in session:
        return None
    
    # Use cached user data if available and recent
    if 'user_cache' in session and 'user_cache_time' in session:
        cache_age = time.time() - session['user_cache_time']
        if cache_age < 300:  # Cache for 5 minutes
            return session['user_cache']
    
    # Fetch fresh user data
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            user_dict = dict(user)
            # Cache the user data
            session['user_cache'] = user_dict
            session['user_cache_time'] = time.time()
            return user_dict
        return None
    except Exception as e:
        print(f"Error getting current user: {e}")
        return None

def login_required_fast(f):
    """Fast login check for video feeds - only checks session"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return "Unauthorized", 401
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if user['status'] != 'approved':
            flash('Your account is not approved yet.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or user['role'] != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Global variables for detection counts
detect_count = "0"
safe_count = "0"

# Generate frames function (your existing function)
def generate_frames(path_x='', conf_=0.25, use_cuda=False, user_id=None, session_id=None):
    global detect_count, safe_count

    webcam_frame_idx = 0 # Initialize webcam frame counter
    out = None # Initialize VideoWriter to None
    session_start_time = time.time()
    detection_session_id = session_id

    try:
        # If path_x is 0, then use webcam mode.
        if path_x == 0:
            # Create webcam detection session
            if user_id and not detection_session_id:
                detection_session_id = create_detection_session(
                    user_id=user_id,
                    session_type='webcam',
                    video_filename=None,
                    confidence_threshold=conf_
                )
            
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("Error: Could not open webcam.")
                if detection_session_id:
                    update_detection_session(detection_session_id, status='failed')
                return # Exit if webcam cannot be opened

            # Get webcam frame properties for VideoWriter
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = 20 # Default FPS for webcam output video

            # Generate a timestamp for webcam session to name saved frames and video
            webcam_session_timestamp = int(time.time())
            output_video_path = os.path.join(PROCESSED_OUTPUT_DIR, f'webcam_processed_{webcam_session_timestamp}.mp4')
            fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Codec for MP4
            out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

            webcam_frame_counter = 0

            try:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        print("Error: Could not read frame from webcam.")
                        break

                    # Process the current frame (pass is_webcam=True and current_frame_num)
                    # video_detection now takes the frame directly for webcam
                    yolo_output_gen = video_detection(source_input=frame, # Pass the frame
                                                      conf_=conf_,
                                                      is_webcam=True,
                                                      use_cuda=use_cuda,
                                                      current_frame_num=webcam_frame_idx)

                    try:
                        # Generator now yields frame, total_detections, safe_detections
                        detection_frame, d_count, s_count = next(yolo_output_gen)
                        detect_count = str(d_count)
                        safe_count = str(s_count)

                        # Save the processed frame as JPG
                        frame_filename = os.path.join(PROCESSED_OUTPUT_DIR, f'webcam_{webcam_session_timestamp}_frame_{webcam_frame_counter:06d}.jpg')
                        cv2.imwrite(frame_filename, detection_frame)

                        # Write the processed frame to the output video file
                        if out is not None:
                             out.write(detection_frame)

                        webcam_frame_counter += 1

                        ret2, buffer = cv2.imencode('.jpg', detection_frame)
                        if not ret2:
                            print("Error: Could not encode frame to JPG.")
                            continue # Skip this frame if encoding fails

                        frame_bytes = buffer.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    except StopIteration:
                        # This might happen if video_detection finishes unexpectedly for a frame
                        print("StopIteration from yolo_output_gen in webcam.")
                        break
                    except Exception as e:
                        print(f"Error during webcam frame processing: {e}")
                        # Optionally, yield an error frame or message
                        break # Or continue, depending on desired error handling

                    webcam_frame_idx += 1 # Increment after processing the frame
            finally:
                cap.release()
                
                # Update webcam session with final results
                if detection_session_id:
                    total, safe, unsafe = get_session_stats()
                    session_duration = int(time.time() - session_start_time)
                    update_detection_session(
                        detection_session_id,
                        total_detections=total,
                        safe_detections=safe,
                        unsafe_detections=unsafe,
                        status='completed',
                        session_duration=session_duration
                    )
        else:
            # Process the uploaded video (path_x is file path)
            video = cv2.VideoCapture(path_x)
            if not video.isOpened():
                print(f"Error: Could not open video file {path_x}")
                if detection_session_id:
                    update_detection_session(detection_session_id, status='failed')
                return

            nframes = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = video.get(cv2.CAP_PROP_FPS)

            # Define the codec and create VideoWriter object
            # Using XVID as it's generally compatible. 'mp4v' or 'avc1' might also work depending on system.
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            # Generate a timestamp and base filename for the video
            video_timestamp = int(time.time())
            original_filename = os.path.splitext(os.path.basename(path_x))[0]
            output_video_path = os.path.join(PROCESSED_OUTPUT_DIR, f'{original_filename}_processed_{video_timestamp}.mp4')
            out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

            frame_counter = 0

            try:
                for detection_frame, d_count, s_count in video_detection(source_input=path_x, # Pass the video path
                                                                          conf_=conf_,
                                                                          is_webcam=False,
                                                                          use_cuda=use_cuda): # current_frame_num is handled internally for videos
                    detect_count = str(d_count)
                    safe_count = str(s_count)

                    # Save the processed frame as JPG
                    frame_filename = os.path.join(PROCESSED_OUTPUT_DIR, f'{original_filename}_{video_timestamp}_frame_{frame_counter:06d}.jpg')
                    cv2.imwrite(frame_filename, detection_frame)

                    # Write the processed frame to the output video file
                    if out is not None:
                        out.write(detection_frame)

                    frame_counter += 1

                    ref, buffer = cv2.imencode('.jpg', detection_frame)
                    frame = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            finally:
                video.release()
                
                # Update video upload session with final results
                if detection_session_id:
                    total, safe, unsafe = get_session_stats()
                    session_duration = int(time.time() - session_start_time)
                    update_detection_session(
                        detection_session_id,
                        total_detections=total,
                        safe_detections=safe,
                        unsafe_detections=unsafe,
                        status='completed',
                        session_duration=session_duration
                    )
            
    except Exception as e:
        print(f"Error in generate_frames: {e}")
        # Mark session as failed if there was an error
        if detection_session_id:
            update_detection_session(detection_session_id, status='failed')
    finally:
        # Ensure resources are released
        if out is not None:
            out.release()

# Detection Session Management Functions
def create_detection_session(user_id, session_type, video_filename=None, confidence_threshold=0.25):
    """Create a new detection session and return session ID"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO detection_sessions 
            (user_id, session_type, video_filename, confidence_threshold, status, started_at)
            VALUES (%s, %s, %s, %s, 'active', %s)
            RETURNING id
        """, (user_id, session_type, video_filename, confidence_threshold, datetime.now()))
        
        session_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()
        return session_id
    except Exception as e:
        print(f"Error creating detection session: {e}")
        return None

def update_detection_session(session_id, total_detections=0, safe_detections=0, unsafe_detections=0, 
                           status='completed', session_duration=None):
    """Update detection session with results"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE detection_sessions 
            SET total_detections = %s, safe_detections = %s, unsafe_detections = %s,
                status = %s, session_duration = %s, completed_at = %s
            WHERE id = %s
        """, (total_detections, safe_detections, unsafe_detections, status, 
              session_duration, datetime.now(), session_id))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating detection session: {e}")
        return False

def get_session_stats():
    """Get current detection counts for session tracking"""
    global detect_count, safe_count
    try:
        total = int(detect_count) if detect_count else 0
        safe = int(safe_count) if safe_count else 0
        unsafe = total - safe if total >= safe else 0
        return total, safe, unsafe
    except:
        return 0, 0, 0

# Routes
@app.route("/", methods=['GET','POST'])
@app.route("/home", methods=['GET','POST'])
def home():
    session.clear()
    return render_template('root.html')

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        user = get_current_user()
        if user and user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('front'))
    
    form = LoginForm()
    if form.validate_on_submit():
        conn = get_db_connection()
        if not conn:
            flash('Database connection error. Please try again.', 'danger')
            return render_template('login.html', form=form)
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE email = %s", (form.email.data,))
            user = cur.fetchone()
            
            if user and bcrypt.checkpw(form.password.data.encode('utf-8'), user['password_hash'].encode('utf-8')):
                if user['status'] == 'approved':
                    session['user_id'] = user['id']
                      # Update last login
                    cur.execute("UPDATE users SET last_login = %s WHERE id = %s", 
                              (datetime.now(), user['id']))
                    conn.commit()
                    
                    log_user_activity(user['id'], 'login', 'User logged in successfully')
                    
                    flash(f'Welcome back, {user["first_name"]}!', 'success')
                    
                    # Both admin and regular users go to the main app (video.html)
                    return redirect(url_for('front'))
                elif user['status'] == 'pending':
                    flash('Your account is pending admin approval.', 'warning')
                elif user['status'] == 'rejected':
                    flash('Your account has been rejected. Please contact support.', 'danger')
                elif user['status'] == 'suspended':
                    flash('Your account has been suspended. Please contact support.', 'danger')
            else:
                flash('Invalid email or password.', 'danger')
            
            cur.close()
            conn.close()
        except Exception as e:
            flash('Login error. Please try again.', 'danger')
            print(f"Login error: {e}")
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        conn = get_db_connection()
        if not conn:
            flash('Database connection error. Please try again.', 'danger')
            return render_template('register.html', form=form)
        
        try:
            cur = conn.cursor()
            
            # Check if user already exists
            cur.execute("SELECT id FROM users WHERE email = %s OR username = %s", 
                       (form.email.data, form.username.data))
            existing_user = cur.fetchone()
            
            if existing_user:
                flash('Email or username already exists.', 'danger')
                return render_template('register.html', form=form)
            
            # Create new user
            password_hash = bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt())
            
            cur.execute("""
                INSERT INTO users (email, username, password_hash, first_name, last_name, phone, company)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (form.email.data, form.username.data, password_hash.decode('utf-8'),
                  form.first_name.data, form.last_name.data, form.phone.data, form.company.data))
            
            conn.commit()
            cur.close()
            conn.close()
            
            flash('Registration successful! Please wait for admin approval.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            flash('Registration error. Please try again.', 'danger')
            print(f"Registration error: {e}")
    
    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    if 'user_id' in session:
        log_user_activity(session['user_id'], 'logout', 'User logged out')
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# Main Application Routes (Protected)
@app.route('/FrontPage', methods=['GET','POST'])
@login_required
def front():
    user = get_current_user()
    form = UploadFileForm()
    if form.validate_on_submit():
        file = form.file.data
        conf_ = form.conf_slide.data

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        session['video_path'] = file_path
        session['conf_'] = conf_
        
        # Create detection session for video upload
        session_id = create_detection_session(
            user_id=user['id'],
            session_type='video_upload',
            video_filename=filename,
            confidence_threshold=round(float(conf_)/100, 2)
        )
        session['detection_session_id'] = session_id
        
        # Log user activity
        log_user_activity(user['id'], 'video_upload', f'Uploaded video: {filename}', filename)

        return render_template('video.html', form=form, user=user)
    return render_template('video.html', form=form, user=user)

@app.route('/video')
@login_required_fast
def video():
    video_path = session.get('video_path', None)
    conf_val = session.get('conf_', 25) # Default confidence if not set
    use_cuda_val = session.get('use_cuda', False)
    session_id = session.get('detection_session_id')
    user_id = session.get('user_id')

    if not video_path: # Or some other condition if you want to allow direct access
        # Handle case where video_path is not set, e.g., redirect to upload page
        return "Error: No video path set in session. Please upload a video first."

    return Response(generate_frames(path_x=video_path,
                                   conf_=round(float(conf_val)/100, 2),
                                   use_cuda=use_cuda_val,
                                   user_id=user_id,
                                   session_id=session_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/webcam_feed')
@login_required_fast
def webcam_feed():
    conf_val = session.get('conf_', 25) # Use session confidence for webcam too, or a fixed one
    use_cuda_val = session.get('use_cuda', False)
    user_id = session.get('user_id')
    # For webcam, pass 0 as path_x to signal webcam mode.
    return Response(generate_frames(path_x=0,
                                   conf_=round(float(conf_val)/100, 2),
                                   use_cuda=use_cuda_val,
                                   user_id=user_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Missing routes from original flaskApp.py
@app.route('/graphData')
@login_required_fast
def graph_data():
    # Return both detection counts for the graph.
    return jsonify(total=detect_count, safe=safe_count)

@app.route('/detectionCount', methods=['GET'])
@login_required_fast
def total_detection_count():
    global detect_count
    return jsonify(detectCount=detect_count)

@app.route('/safeCount', methods=['GET'])
@login_required_fast
def safe_person_count():
    global safe_count
    return jsonify(safecount=safe_count)

@app.route('/tracker_logs')
@login_required
def tracker_logs():
    output_file_path = os.path.join('data', 'tracking_results.txt')
    if os.path.exists(output_file_path):
        with open(output_file_path, 'r') as f:
            logs = f.read()
    else:
        logs = "No logs available yet."
    # Return as plain text, which the browser will display.
    return Response(logs, mimetype='text/plain')

@app.route('/toggle_cuda')
@login_required
def toggle_cuda():
    import torch # Keep import here to avoid dependency if CUDA check is not used often
    use_cuda = session.get('use_cuda', False)

    if use_cuda: # If already enabled, disable it
        session['use_cuda'] = False
        print("CUDA disabled by toggle.")
        return jsonify(message="CUDA disabled", use_cuda=False)
    else: # If disabled, try to enable it
        if torch.cuda.is_available():
            session['use_cuda'] = True
            print("CUDA enabled by toggle.")
            return jsonify(message="CUDA enabled", use_cuda=True)
        else:
            session['use_cuda'] = False # Ensure it's set to False if not available
            print("CUDA not supported on this device (toggle attempt).")
            return jsonify(error="CUDA not supported on this device.", use_cuda=False)

@app.route('/reset_counts')
@login_required
def reset_counts():
    global detect_count, safe_count
    detect_count = "0"
    safe_count = "0"

    output_file_path = os.path.join('data', 'tracking_results.txt')
    if os.path.exists(output_file_path):
        try:
            with open(output_file_path, 'w') as f: # Open in write mode to clear
                # Write header again after clearing
                f.write("frame_number,obj_id,x,y,width,height,confidence,class_name,helmet_worn,mask_worn,vest_worn,compliance_status\n")
            print("Counts and logs (tracking_results.txt) reset.")
        except IOError as e:
            print(f"Error resetting logs: {e}")
            return jsonify(success=False, message=f"Error resetting logs: {e}")

    return jsonify(success=True, message="Counts and logs reset.")

# User Profile Management Routes
@app.route('/profile')
@login_required
def profile():
    """Display user profile page"""
    user = get_current_user()
    profile_form = ProfileUpdateForm(obj=type('obj', (object,), user))
    password_form = ChangePasswordForm()
    
    return render_template('profile.html', 
                         user=user, 
                         profile_form=profile_form, 
                         password_form=password_form)

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile information"""
    user = get_current_user()
    form = ProfileUpdateForm()
    
    if form.validate_on_submit():
        conn = get_db_connection()
        if not conn:
            flash('Database connection error. Please try again.', 'danger')
            return redirect(url_for('profile'))
        
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE users 
                SET first_name = %s, last_name = %s, phone = %s, company = %s, updated_at = %s
                WHERE id = %s
            """, (form.first_name.data, form.last_name.data, form.phone.data, 
                  form.company.data, datetime.now(), user['id']))
            
            conn.commit()
            cur.close()
            conn.close()
            
            # Clear user cache to force refresh
            session.pop('user_cache', None)
            session.pop('user_cache_time', None)
            
            # Log the profile update
            log_user_activity(user['id'], 'profile_update', 'User updated profile information')
            
            flash('Profile updated successfully!', 'success')
            
        except Exception as e:
            print(f"Profile update error: {e}")
            flash('Error updating profile. Please try again.', 'danger')
    else:
        # Flash form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field.replace("_", " ").title()}: {error}', 'danger')
    
    return redirect(url_for('profile'))

@app.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    user = get_current_user()
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        conn = get_db_connection()
        if not conn:
            flash('Database connection error. Please try again.', 'danger')
            return redirect(url_for('profile'))
        
        try:
            # Verify current password
            if not bcrypt.checkpw(form.current_password.data.encode('utf-8'), 
                                user['password_hash'].encode('utf-8')):
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('profile'))
            
            # Hash new password
            new_password_hash = bcrypt.hashpw(form.new_password.data.encode('utf-8'), bcrypt.gensalt())
            
            cur = conn.cursor()
            cur.execute("""
                UPDATE users 
                SET password_hash = %s, updated_at = %s
                WHERE id = %s
            """, (new_password_hash.decode('utf-8'), datetime.now(), user['id']))
            
            conn.commit()
            cur.close()
            conn.close()
            
            # Clear user cache
            session.pop('user_cache', None)
            session.pop('user_cache_time', None)
            
            # Log the password change
            log_user_activity(user['id'], 'password_change', 'User changed password')
            
            flash('Password changed successfully!', 'success')
            
        except Exception as e:
            print(f"Password change error: {e}")
            flash('Error changing password. Please try again.', 'danger')
    else:
        # Flash form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field.replace("_", " ").title()}: {error}', 'danger')
    
    return redirect(url_for('profile'))

@app.route('/api/profile', methods=['GET'])
@login_required
def api_get_profile():
    """API endpoint to get user profile data"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Return safe user data (excluding sensitive information)
    profile_data = {
        'id': user['id'],
        'email': user['email'],
        'username': user['username'],
        'first_name': user['first_name'],
        'last_name': user['last_name'],
        'phone': user['phone'],
        'company': user['company'],
        'role': user['role'],
        'status': user['status'],
        'registration_date': user['registration_date'].isoformat() if user['registration_date'] else None,
        'last_login': user['last_login'].isoformat() if user['last_login'] else None
    }
    
    return jsonify(profile_data)

@app.route('/api/profile/sessions', methods=['GET'])
@login_required
def api_get_user_sessions():
    """Get user's detection session history"""
    user = get_current_user()
    limit = int(request.args.get('limit', 20))
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, session_type, video_filename, confidence_threshold,
                   total_detections, safe_detections, unsafe_detections,
                   session_duration, status, started_at, completed_at
            FROM detection_sessions
            WHERE user_id = %s
            ORDER BY started_at DESC
            LIMIT %s
        """, (user['id'], limit))
        
        sessions = cur.fetchall()
        cur.close()
        conn.close()
        
        # Convert to list of dicts for JSON serialization
        sessions_list = [dict(session) for session in sessions]
        
        return jsonify({'sessions': sessions_list})
        
    except Exception as e:
        print(f"User sessions error: {e}")
        return jsonify({'error': 'Error loading sessions'}), 500

# Admin Routes
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    user = get_current_user()
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'danger')
        return redirect(url_for('home'))
    
    try:
        cur = conn.cursor()
          # Get statistics
        cur.execute("SELECT COUNT(*) as total FROM users WHERE role = 'customer'")
        total_users = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as pending FROM users WHERE status = 'pending'")
        pending_users = cur.fetchone()['pending']
        
        cur.execute("SELECT COUNT(*) as approved FROM users WHERE status = 'approved'")
        approved_users = cur.fetchone()['approved']
        
        cur.execute("""
            SELECT COUNT(*) as sessions 
            FROM detection_sessions 
            WHERE started_at >= NOW() - INTERVAL '30 days'
        """)
        recent_sessions = cur.fetchone()['sessions']
        
        # Get recent activity
        cur.execute("""
            SELECT u.first_name, u.last_name, a.activity_type, a.description, a.created_at
            FROM user_activity_logs a
            JOIN users u ON a.user_id = u.id
            ORDER BY a.created_at DESC
            LIMIT 10
        """)
        recent_activity = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('admin_dashboard.html', 
                             user=user,
                             total_users=total_users,
                             pending_users=pending_users,
                             approved_users=approved_users,
                             recent_sessions=recent_sessions,
                             recent_activity=recent_activity)
    except Exception as e:
        print(f"Admin dashboard error: {e}")
        flash('Error loading dashboard.', 'danger')
        return redirect(url_for('home'))

@app.route('/admin/users')
@admin_required
def admin_users():
    user = get_current_user()
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, first_name, last_name, email, username, role, status, 
                   registration_date, last_login, company
            FROM users 
            WHERE role = 'customer'
            ORDER BY registration_date DESC
        """)
        users = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('admin_users.html', user=user, users=users)
    except Exception as e:
        print(f"Admin users error: {e}")
        flash('Error loading users.', 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/api/admin/approve/<int:user_id>', methods=['POST'])
@admin_required
def api_approve_user(user_id):
    admin_user = get_current_user()
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection error'}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE users 
            SET status = 'approved', approved_date = %s, approved_by = %s 
            WHERE id = %s AND role = 'customer'
        """, (datetime.now(), admin_user['id'], user_id))
        conn.commit()
        
        # Log admin activity
        cur.execute("SELECT first_name, last_name FROM users WHERE id = %s", (user_id,))
        target_user = cur.fetchone()
        
        if target_user:
            log_user_activity(admin_user['id'], 'user_approval', 
                             f'Approved user: {target_user["first_name"]} {target_user["last_name"]}')
        
        cur.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"User approval error: {e}")
        return jsonify({'success': False, 'error': 'Error approving user'}), 500

@app.route('/api/admin/reject/<int:user_id>', methods=['POST'])
@admin_required
def api_reject_user(user_id):
    print(f"DEBUG: api_reject_user called with user_id: {user_id}")
    admin_user = get_current_user()
    print(f"DEBUG: admin_user: {admin_user}")
    conn = get_db_connection()
    if not conn:
        print("DEBUG: Database connection failed")
        return jsonify({'success': False, 'error': 'Database connection error'}), 500
    
    try:
        cur = conn.cursor()
        print(f"DEBUG: Executing UPDATE query for user_id: {user_id}")
        cur.execute("""
            UPDATE users 
            SET status = 'rejected', approved_by = %s 
            WHERE id = %s AND role = 'customer'
        """, (admin_user['id'], user_id))
        conn.commit()
        print(f"DEBUG: UPDATE query executed successfully")
        
        # Log admin activity
        cur.execute("SELECT first_name, last_name FROM users WHERE id = %s", (user_id,))
        target_user = cur.fetchone()
        print(f"DEBUG: target_user: {target_user}")
        
        if target_user:
            log_user_activity(admin_user['id'], 'user_rejection', 
                             f'Rejected user: {target_user["first_name"]} {target_user["last_name"]}')
            print(f"DEBUG: Activity logged successfully")
        
        cur.close()
        conn.close()
        print(f"DEBUG: Returning success response")
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"User rejection error: {e}")
        print(f"DEBUG: Exception details: {type(e).__name__}: {str(e)}")
        return jsonify({'success': False, 'error': 'Error rejecting user'}), 500

@app.route('/api/admin/stats')
@admin_required
def api_admin_stats():
    """Get admin dashboard statistics"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cur = conn.cursor()
        
        # Get total users
        cur.execute("SELECT COUNT(*) as count FROM users WHERE role = 'customer'")
        total_users = cur.fetchone()['count']
        
        # Get pending users
        cur.execute("SELECT COUNT(*) as count FROM users WHERE role = 'customer' AND status = 'pending'")
        pending_users = cur.fetchone()['count']
        
        # Get approved users
        cur.execute("SELECT COUNT(*) as count FROM users WHERE role = 'customer' AND status = 'approved'")
        approved_users = cur.fetchone()['count']
        
        # Get total detection sessions
        cur.execute("SELECT COUNT(*) as count FROM detection_sessions")
        total_sessions = cur.fetchone()['count']
        
        cur.close()
        conn.close()
        
        return jsonify({
            'total_users': total_users,
            'pending_users': pending_users,
            'approved_users': approved_users,
            'total_sessions': total_sessions
        })
    except Exception as e:
        print(f"API admin stats error: {e}")
        return jsonify({'error': 'Error loading statistics'}), 500

@app.route('/api/admin/users')
@admin_required
def api_admin_users():
    """Get users list with optional filtering"""
    filter_type = request.args.get('filter', 'all')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cur = conn.cursor()
        
        # Build query based on filter
        base_query = """
            SELECT id, first_name, last_name, email, username, status, 
                   registration_date, last_login, company
            FROM users 
            WHERE role = 'customer'
        """
        
        if filter_type != 'all':
            base_query += f" AND status = '{filter_type}'"
        
        base_query += " ORDER BY registration_date DESC"
        
        cur.execute(base_query)
        users = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Convert to list of dicts for JSON serialization
        users_list = [dict(user) for user in users]
        
        return jsonify({'users': users_list})
    except Exception as e:
        print(f"API admin users error: {e}")
        return jsonify({'error': 'Error loading users'}), 500

@app.route('/api/admin/suspend/<int:user_id>', methods=['POST'])
@admin_required
def api_suspend_user(user_id):
    admin_user = get_current_user()
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection error'}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE users 
            SET status = 'suspended' 
            WHERE id = %s AND role = 'customer'
        """, (user_id,))
        conn.commit()
        
        # Log admin activity
        cur.execute("SELECT first_name, last_name FROM users WHERE id = %s", (user_id,))
        target_user = cur.fetchone()
        
        if target_user:
            log_user_activity(admin_user['id'], 'user_suspension', 
                             f'Suspended user: {target_user["first_name"]} {target_user["last_name"]}')
        
        cur.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"User suspension error: {e}")
        return jsonify({'success': False, 'error': 'Error suspending user'}), 500

@app.route('/api/admin/reactivate/<int:user_id>', methods=['POST'])
@admin_required
def api_reactivate_user(user_id):
    admin_user = get_current_user()
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection error'}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE users 
            SET status = 'approved' 
            WHERE id = %s AND role = 'customer'
        """, (user_id,))
        conn.commit()
        
        # Log admin activity
        cur.execute("SELECT first_name, last_name FROM users WHERE id = %s", (user_id,))
        target_user = cur.fetchone()
        
        if target_user:
            log_user_activity(admin_user['id'], 'user_reactivation', 
                             f'Reactivated user: {target_user["first_name"]} {target_user["last_name"]}')
        
        cur.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"User reactivation error: {e}")
        return jsonify({'success': False, 'error': 'Error reactivating user'}), 500

@app.route('/api/admin/delete/<int:user_id>', methods=['DELETE'])
@admin_required
def api_delete_user(user_id):
    admin_user = get_current_user()
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection error'}), 500
    
    try:
        cur = conn.cursor()
        
        # Get user info before deletion for logging
        cur.execute("SELECT first_name, last_name, email FROM users WHERE id = %s AND role = 'customer'", (user_id,))
        target_user = cur.fetchone()
        
        if not target_user:
            return jsonify({'success': False, 'error': 'User not found or is admin'}), 404
        
        # Delete user (this will cascade to activity logs and detection sessions)
        cur.execute("DELETE FROM users WHERE id = %s AND role = 'customer'", (user_id,))
        conn.commit()
        
        # Log admin activity
        log_user_activity(admin_user['id'], 'user_deletion', 
                         f'Deleted user: {target_user["first_name"]} {target_user["last_name"]} ({target_user["email"]})')
        
        cur.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"User deletion error: {e}")
        return jsonify({'success': False, 'error': 'Error deleting user'}), 500

@app.route('/api/admin/activity-logs')
@admin_required
def api_get_activity_logs():
    filter_type = request.args.get('filter', 'all')
    limit = int(request.args.get('limit', 50))
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cur = conn.cursor()
        
        # Build query based on filter
        base_query = """
            SELECT ual.*, u.first_name, u.last_name, u.email,
                   CONCAT(u.first_name, ' ', u.last_name) as user_name
            FROM user_activity_logs ual
            JOIN users u ON ual.user_id = u.id
        """
        
        if filter_type != 'all':
            base_query += " WHERE ual.activity_type = %s"
            cur.execute(base_query + " ORDER BY ual.created_at DESC LIMIT %s", (filter_type, limit))
        else:
            cur.execute(base_query + " ORDER BY ual.created_at DESC LIMIT %s", (limit,))
        
        logs = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Convert to list of dicts for JSON serialization
        logs_list = [dict(log) for log in logs]
        
        return jsonify({'logs': logs_list})
    except Exception as e:
        print(f"Activity logs error: {e}")
        return jsonify({'error': 'Error loading activity logs'}), 500

@app.route('/api/admin/detection-sessions')
@admin_required
def api_get_detection_sessions():
    filter_type = request.args.get('filter', 'all')
    limit = int(request.args.get('limit', 50))
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cur = conn.cursor()
        
        # Build query based on filter
        base_query = """
            SELECT ds.*, u.first_name, u.last_name, u.email,
                   CONCAT(u.first_name, ' ', u.last_name) as user_name
            FROM detection_sessions ds
            JOIN users u ON ds.user_id = u.id
        """
        
        params = []
        if filter_type == 'webcam':
            base_query += " WHERE ds.session_type = 'webcam'"
        elif filter_type == 'video_upload':
            base_query += " WHERE ds.session_type = 'video_upload'"
        elif filter_type == 'active':
            base_query += " WHERE ds.status = 'active'"
        elif filter_type == 'completed':
            base_query += " WHERE ds.status = 'completed'"
        
        if filter_type != 'all' and filter_type in ['webcam', 'video_upload', 'active', 'completed']:
            cur.execute(base_query + " ORDER BY ds.started_at DESC LIMIT %s", (limit,))
        else:
            cur.execute(base_query + " ORDER BY ds.started_at DESC LIMIT %s", (limit,))
        
        sessions = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Convert to list of dicts for JSON serialization
        sessions_list = [dict(session) for session in sessions]
        
        return jsonify({'sessions': sessions_list})
    except Exception as e:
        print(f"Detection sessions error: {e}")
        return jsonify({'error': 'Error loading detection sessions'}), 500

@app.route('/api/admin/export-data')
@admin_required
def api_export_data():
    import csv
    import io
    from flask import make_response
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cur = conn.cursor()
        
        # Create CSV output
        output = io.StringIO()
        
        # Export users data
        cur.execute("""
            SELECT id, email, username, first_name, last_name, role, status, 
                   registration_date, last_login, company
            FROM users ORDER BY registration_date DESC
        """)
        users = cur.fetchall()
        
        if users:
            # Write users data
            output.write("=== USERS DATA ===\n")
            fieldnames = ['id', 'email', 'username', 'first_name', 'last_name', 'role', 'status', 
                         'registration_date', 'last_login', 'company']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for user in users:
                # Convert Row object to dict and handle None values
                user_dict = {}
                for key in fieldnames:
                    value = user[key] if key in user.keys() else ''
                    # Convert datetime objects to strings
                    if hasattr(value, 'strftime'):
                        value = value.strftime('%Y-%m-%d %H:%M:%S')
                    elif value is None:
                        value = ''
                    user_dict[key] = str(value)
                writer.writerow(user_dict)
            output.write("\n\n")
        
        # Export activity logs (simplified)
        try:
            cur.execute("""
                SELECT ual.id, ual.user_id, u.first_name, u.last_name, u.email, 
                       ual.activity_type, ual.description, ual.video_filename, 
                       ual.ip_address, ual.created_at
                FROM user_activity_logs ual
                JOIN users u ON ual.user_id = u.id
                ORDER BY ual.created_at DESC
                LIMIT 1000
            """)
            logs = cur.fetchall()
            
            if logs:
                output.write("=== ACTIVITY LOGS ===\n")
                fieldnames = ['id', 'user_id', 'first_name', 'last_name', 'email', 'activity_type', 
                             'description', 'video_filename', 'ip_address', 'created_at']
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                for log in logs:
                    log_dict = {}
                    for key in fieldnames:
                        value = log[key] if key in log.keys() else ''
                        if hasattr(value, 'strftime'):
                            value = value.strftime('%Y-%m-%d %H:%M:%S')
                        elif value is None:
                            value = ''
                        log_dict[key] = str(value)
                    writer.writerow(log_dict)
                output.write("\n\n")
        except Exception as e:
            print(f"Activity logs export error: {e}")
            output.write("=== ACTIVITY LOGS ===\n")
            output.write("Error loading activity logs\n\n")
        
        # Export detection sessions (simplified)
        try:
            cur.execute("""
                SELECT ds.id, ds.user_id, u.first_name, u.last_name, u.email, 
                       ds.session_type, ds.video_filename, ds.safe_detections, 
                       ds.unsafe_detections, ds.total_detections, ds.status, 
                       ds.started_at, ds.completed_at
                FROM detection_sessions ds
                JOIN users u ON ds.user_id = u.id
                ORDER BY ds.started_at DESC
                LIMIT 1000
            """)
            sessions = cur.fetchall()
            
            if sessions:
                output.write("=== DETECTION SESSIONS ===\n")
                fieldnames = ['id', 'user_id', 'first_name', 'last_name', 'email', 'session_type', 
                             'video_filename', 'safe_detections', 'unsafe_detections', 'total_detections',
                             'status', 'started_at', 'completed_at']
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                for session in sessions:
                    session_dict = {}
                    for key in fieldnames:
                        value = session[key] if key in session.keys() else ''
                        if hasattr(value, 'strftime'):
                            value = value.strftime('%Y-%m-%d %H:%M:%S')
                        elif value is None:
                            value = ''
                        session_dict[key] = str(value)
                    writer.writerow(session_dict)
                output.write("\n\n")
        except Exception as e:
            print(f"Detection sessions export error: {e}")
            output.write("=== DETECTION SESSIONS ===\n")
            output.write("Error loading detection sessions\n\n")
        
        cur.close()
        conn.close()
        
        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=ppe_system_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        # Log export activity
        try:
            admin_user = get_current_user()
            if admin_user:
                log_user_activity(admin_user['id'], 'data_export', 'Exported system data to CSV')
        except Exception as e:
            print(f"Activity logging error: {e}")
        
        return response
        
    except Exception as e:
        print(f"Data export error: {e}")
        if conn:
            conn.close()
        return jsonify({'error': f'Error exporting data: {str(e)}'}), 500

@app.route('/api/admin/system-stats')
@admin_required
def api_system_stats():
    """Get system statistics for admin dashboard"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cur = conn.cursor()
        
        # Get total videos processed (from detection sessions)
        cur.execute("SELECT COUNT(*) as count FROM detection_sessions WHERE session_type = 'video_upload'")
        videos_processed = cur.fetchone()['count']
        
        # Get total detections
        cur.execute("SELECT COALESCE(SUM(total_detections), 0) as total FROM detection_sessions")
        total_detections_result = cur.fetchone()['total']
        total_detections = total_detections_result if total_detections_result else 0
        
        # Get database size (approximate)
        try:
            cur.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as db_size
            """)
            db_size_result = cur.fetchone()
            db_size = db_size_result['db_size'] if db_size_result else "Unknown"
        except:
            db_size = "PostgreSQL"
        
        cur.close()
        conn.close()
        
        # Server uptime (approximate - since app start)
        try:
            import psutil
            # Try to get system uptime
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            uptime_hours = int(uptime_seconds // 3600)
            uptime_days = uptime_hours // 24
            uptime_hours = uptime_hours % 24
            
            if uptime_days > 0:
                server_uptime = f"{uptime_days}d {uptime_hours}h"
            else:
                server_uptime = f"{uptime_hours}h"
        except ImportError:
            # Fallback if psutil not available
            server_uptime = "Available"
        except Exception:
            server_uptime = "Unknown"
        
        return jsonify({
            'server_uptime': server_uptime,
            'videos_processed': videos_processed,
            'total_detections': total_detections,
            'database_size': db_size
        })
        
    except Exception as e:
        print(f"System stats error: {e}")
        return jsonify({
            'server_uptime': 'Available',
            'videos_processed': 0,
            'total_detections': 0,
            'database_size': 'Unknown'        }), 200  # Return partial data instead of error

@app.route('/api/admin/cleanup', methods=['POST'])
@admin_required
def api_cleanup_database():
    """Clean up old activity logs and detection sessions"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cur = conn.cursor()
        
        # Delete activity logs older than 30 days
        cur.execute("""
            DELETE FROM user_activity_logs 
            WHERE created_at < NOW() - INTERVAL '30 days'
        """)
        deleted_logs = cur.rowcount
        
        # Delete detection sessions older than 30 days
        cur.execute("""
            DELETE FROM detection_sessions 
            WHERE started_at < NOW() - INTERVAL '30 days'
        """)
        deleted_sessions = cur.rowcount
        
        # Commit the changes
        conn.commit()
        
        cur.close()
        conn.close()
        
        # Log the cleanup activity
        try:
            admin_user = get_current_user()
            if admin_user:
                log_user_activity(admin_user['id'], 'database_cleanup', 
                                f'Cleaned up {deleted_logs} activity logs and {deleted_sessions} detection sessions older than 30 days')
        except Exception as e:
            print(f"Activity logging error during cleanup: {e}")
        
        message = f"Successfully cleaned up {deleted_logs} activity logs and {deleted_sessions} detection sessions older than 30 days."
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        print(f"Database cleanup error: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'error': f'Cleanup failed: {str(e)}'}), 500

@app.route('/api/admin/create-sample-data', methods=['POST'])
@admin_required
def api_create_sample_data():
    """Create sample detection sessions for testing"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cur = conn.cursor()
        
        # Get current admin user
        admin_user = get_current_user()
        if not admin_user:
            return jsonify({'error': 'Admin user not found'}), 400
        
        # Create sample detection sessions
        sample_sessions = [
            {
                'session_type': 'video_upload',
                'video_filename': 'sample_construction_site.mp4',
                'safe_detections': 15,
                'unsafe_detections': 3,
                'total_detections': 18,
                'status': 'completed'
            },
            {
                'session_type': 'webcam',
                'video_filename': None,
                'safe_detections': 8,
                'unsafe_detections': 1,
                'total_detections': 9,
                'status': 'completed'
            },
            {
                'session_type': 'video_upload',
                'video_filename': 'warehouse_safety_check.mp4',
                'safe_detections': 22,
                'unsafe_detections': 0,
                'total_detections': 22,
                'status': 'completed'
            },
            {
                'session_type': 'video_upload',
                'video_filename': 'factory_inspection.mp4',
                'safe_detections': 12,
                'unsafe_detections': 5,
                'total_detections': 17,
                'status': 'completed'
            }
        ]
        
        created_count = 0
        for session in sample_sessions:
            cur.execute("""
                INSERT INTO detection_sessions 
                (user_id, session_type, video_filename, safe_detections, unsafe_detections, 
                 total_detections, status, started_at, completed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 
                        NOW() - INTERVAL '%s hours', NOW() - INTERVAL '%s hours')
            """, (
                admin_user['id'],
                session['session_type'],
                session['video_filename'],
                session['safe_detections'],
                session['unsafe_detections'],
                session['total_detections'],
                session['status'],
                created_count * 6 + 24,  # Spread sessions over past day
                created_count * 6 + 23   # 1 hour duration each
            ))
            created_count += 1
        
        conn.commit()
        cur.close()
        conn.close()
        
        # Log the sample data creation
        try:
            log_user_activity(admin_user['id'], 'sample_data_creation', 
                            f'Created {created_count} sample detection sessions for testing')
        except Exception as e:
            print(f"Activity logging error during sample data creation: {e}")
        
        return jsonify({'success': True, 'created_count': created_count})
        
    except Exception as e:
        print(f"Sample data creation error: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'error': f'Failed to create sample data: {str(e)}'}), 500

# Initialize database on app start
def create_tables():
    if not init_database():
        print("Warning: Database initialization failed")

if __name__ == "__main__":
    # Initialize database when the app starts
    create_tables()
    app.run(debug=True, host="0.0.0.0", port=5000)
