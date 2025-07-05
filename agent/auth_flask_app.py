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
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, activity_type, description, video_filename, 
              detection_results, request.environ.get('HTTP_X_REAL_IP', request.remote_addr),
              request.headers.get('User-Agent')))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error logging activity: {e}")

def get_current_user():
    """Get current user from session"""
    if 'user_id' not in session:
        return None
    
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cur.fetchone()
        cur.close()
        conn.close()
        return dict(user) if user else None
    except Exception as e:
        print(f"Error getting current user: {e}")
        return None

def login_required(f):
    """Decorator to require login"""
    from functools import wraps
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
    from functools import wraps
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
                    
                    if user['role'] == 'admin':
                        return redirect(url_for('admin_dashboard'))
                    else:
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
            hashed_password = bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt())
            
            cur.execute("""
                INSERT INTO users (email, username, password_hash, first_name, last_name, phone, company)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (form.email.data, form.username.data, hashed_password.decode('utf-8'),
                  form.first_name.data, form.last_name.data, form.phone.data, form.company.data))
            
            user_id = cur.fetchone()['id']
            conn.commit()
            
            log_user_activity(user_id, 'registration', 'User registered successfully')
            
            flash('Registration successful! Please wait for admin approval before logging in.', 'success')
            cur.close()
            conn.close()
            return redirect(url_for('login'))
            
        except Exception as e:
            flash('Registration error. Please try again.', 'danger')
            print(f"Registration error: {e}")
    
    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    user = get_current_user()
    if user:
        log_user_activity(user['id'], 'logout', 'User logged out')
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Admin Routes
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'danger')
        return redirect(url_for('login'))
    
    try:
        cur = conn.cursor()
        
        # Get pending users
        cur.execute("SELECT * FROM users WHERE status = 'pending' ORDER BY registration_date DESC")
        pending_users = cur.fetchall()
        
        # Get statistics
        cur.execute("SELECT COUNT(*) as count FROM users")
        total_users = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) as count FROM users WHERE status = 'approved'")
        approved_users = cur.fetchone()['count']
        
        # Get recent activity
        cur.execute("""
            SELECT al.*, u.first_name, u.last_name 
            FROM user_activity_logs al 
            JOIN users u ON al.user_id = u.id 
            ORDER BY al.created_at DESC 
            LIMIT 10
        """)
        recent_activity = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('admin_dashboard.html',
                             pending_users=pending_users,
                             total_users=total_users,
                             approved_users=approved_users,
                             recent_activity=recent_activity)
    except Exception as e:
        flash('Error loading dashboard.', 'danger')
        print(f"Dashboard error: {e}")
        return redirect(url_for('login'))

@app.route('/admin/approve_user/<int:user_id>', methods=['POST'])
@admin_required
def approve_user(user_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cur = conn.cursor()
        current_user = get_current_user()
        
        cur.execute("""
            UPDATE users 
            SET status = 'approved', approved_date = %s, approved_by = %s 
            WHERE id = %s
        """, (datetime.now(), current_user['id'], user_id))
        
        conn.commit()
        
        # Get user details for logging
        cur.execute("SELECT email FROM users WHERE id = %s", (user_id,))
        user_email = cur.fetchone()['email']
        
        log_user_activity(current_user['id'], 'user_approval', f'Approved user: {user_email}')
        
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'User approved successfully'})
    except Exception as e:
        print(f"Approval error: {e}")
        return jsonify({'error': 'Approval failed'}), 500

@app.route('/admin/reject_user/<int:user_id>', methods=['POST'])
@admin_required
def reject_user(user_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cur = conn.cursor()
        current_user = get_current_user()
        
        cur.execute("UPDATE users SET status = 'rejected' WHERE id = %s", (user_id,))
        conn.commit()
        
        # Get user details for logging
        cur.execute("SELECT email FROM users WHERE id = %s", (user_id,))
        user_email = cur.fetchone()['email']
        
        log_user_activity(current_user['id'], 'user_rejection', f'Rejected user: {user_email}')
        
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'User rejected'})
    except Exception as e:
        print(f"Rejection error: {e}")
        return jsonify({'error': 'Rejection failed'}), 500

@app.route('/admin/users')
@admin_required
def admin_users():
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users ORDER BY created_at DESC")
        users = cur.fetchall()
        cur.close()
        conn.close()
        
        return render_template('admin_users.html', users=users)
    except Exception as e:
        flash('Error loading users.', 'danger')
        return redirect(url_for('admin_dashboard'))

# Detection System Routes (Protected)
@app.route("/", methods=['GET','POST'])
@app.route("/home", methods=['GET','POST'])
def home():
    if 'user_id' in session:
        user = get_current_user()
        if user and user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('front'))
    return redirect(url_for('login'))

@app.route('/video.html', methods=['GET','POST'])
@app.route('/FrontPage', methods=['GET','POST'])
def front():
    # Check if user is logged in
    current_user = get_current_user() if 'user_id' in session else None
    
    if current_user:
        log_user_activity(current_user['id'], 'page_access', 'Accessed detection system')
    
    form = UploadFileForm()
    if form.validate_on_submit() and current_user:
        file = form.file.data
        conf_ = form.conf_slide.data

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        session['video_path'] = file_path
        session['conf_'] = conf_
        
        log_user_activity(current_user['id'], 'video_upload', f'Uploaded video: {filename}', filename)
        
        # Create detection session
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO detection_sessions 
                    (user_id, session_type, video_filename, confidence_threshold)
                    VALUES (%s, %s, %s, %s) RETURNING id
                """, (current_user['id'], 'video_upload', filename, conf_/100))
                
                session_id = cur.fetchone()['id']
                session['detection_session_id'] = session_id
                conn.commit()
                cur.close()
                conn.close()
            except Exception as e:
                print(f"Session creation error: {e}")

        return render_template('video.html', form=form, current_user=current_user)
    return render_template('video.html', form=form, current_user=current_user)

# Keep your existing detection routes with authentication
@app.route('/video')
@login_required
def video():
    video_path = session.get('video_path', None)
    conf_val = session.get('conf_', 25)
    use_cuda_val = session.get('use_cuda', False)

    if not video_path:
        return "Error: No video path set in session. Please upload a video first."

    return Response(generate_frames(path_x=video_path,
                                   conf_=round(float(conf_val)/100, 2),
                                   use_cuda=use_cuda_val),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/webcam_feed')
@login_required
def webcam_feed():
    conf_val = session.get('conf_', 25)
    use_cuda_val = session.get('use_cuda', False)
    return Response(generate_frames(path_x=0,
                                   conf_=round(float(conf_val)/100, 2),
                                   use_cuda=use_cuda_val),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Keep all your existing detection functions unchanged
def generate_frames(path_x='', conf_=0.25, use_cuda=False):
    global detect_count, safe_count

    webcam_frame_idx = 0
    out = None

    try:
        if path_x == 0:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("Error: Could not open webcam.")
                return

            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = 20

            webcam_session_timestamp = int(time.time())
            output_video_path = os.path.join(PROCESSED_OUTPUT_DIR, f'webcam_processed_{webcam_session_timestamp}.mp4')
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

            webcam_frame_counter = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Could not read frame from webcam.")
                    break

                yolo_output_gen = video_detection(source_input=frame,
                                                  conf_=conf_,
                                                  is_webcam=True,
                                                  use_cuda=use_cuda,
                                                  current_frame_num=webcam_frame_idx)

                try:
                    detection_frame, d_count, s_count = next(yolo_output_gen)
                    detect_count = str(d_count)
                    safe_count = str(s_count)

                    frame_filename = os.path.join(PROCESSED_OUTPUT_DIR, f'webcam_{webcam_session_timestamp}_frame_{webcam_frame_counter:06d}.jpg')
                    cv2.imwrite(frame_filename, detection_frame)

                    if out is not None:
                         out.write(detection_frame)

                    webcam_frame_counter += 1

                    ret2, buffer = cv2.imencode('.jpg', detection_frame)
                    if not ret2:
                        print("Error: Could not encode frame to JPG.")
                        continue

                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                except StopIteration:
                    print("StopIteration from yolo_output_gen in webcam.")
                    break
                except Exception as e:
                    print(f"Error during webcam frame processing: {e}")
                    break

                webcam_frame_idx += 1
            cap.release()
        else:
            video = cv2.VideoCapture(path_x)
            if not video.isOpened():
                print(f"Error: Could not open video file {path_x}")
                return

            nframes = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = video.get(cv2.CAP_PROP_FPS)

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_timestamp = int(time.time())
            original_filename = os.path.splitext(os.path.basename(path_x))[0]
            output_video_path = os.path.join(PROCESSED_OUTPUT_DIR, f'{original_filename}_processed_{video_timestamp}.mp4')
            out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

            frame_counter = 0

            for detection_frame, d_count, s_count in video_detection(source_input=path_x,
                                                                      conf_=conf_,
                                                                      is_webcam=False,
                                                                      use_cuda=use_cuda):
                detect_count = str(d_count)
                safe_count = str(s_count)

                frame_filename = os.path.join(PROCESSED_OUTPUT_DIR, f'{original_filename}_{video_timestamp}_frame_{frame_counter:06d}.jpg')
                cv2.imwrite(frame_filename, detection_frame)
                frame_counter += 1

                if out is not None:
                    out.write(detection_frame)

                ret, buffer = cv2.imencode('.jpg', detection_frame)
                if not ret:
                    print("Error: Could not encode video frame to JPG.")
                    continue

                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            video.release()

    finally:
        if out is not None:
            out.release()
            print(f"Processed video saved to: {output_video_path}")

# Keep all your existing API routes
@app.route('/graphData')
@login_required
def graph_data():
    return jsonify(total=detect_count, safe=safe_count)

@app.route('/detectionCount', methods=['GET'])
@login_required
def total_detection_count():
    global detect_count
    return jsonify(detectCount=detect_count)

@app.route('/safeCount', methods=['GET'])
@login_required
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
    return Response(logs, mimetype='text/plain')

@app.route('/toggle_cuda')
@login_required
def toggle_cuda():
    import torch
    use_cuda = session.get('use_cuda', False)

    if use_cuda:
        session['use_cuda'] = False
        print("CUDA disabled by toggle.")
        return jsonify(message="CUDA disabled", use_cuda=False)
    else:
        if torch.cuda.is_available():
            session['use_cuda'] = True
            print("CUDA enabled by toggle.")
            return jsonify(message="CUDA enabled", use_cuda=True)
        else:
            session['use_cuda'] = False
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
            with open(output_file_path, 'w') as f:
                f.write("frame_number,obj_id,x,y,width,height,confidence,class_name,helmet_worn,mask_worn,vest_worn,compliance_status\n")
            print("Counts and logs (tracking_results.txt) reset.")
        except IOError as e:
            print(f"Error resetting logs: {e}")
            return jsonify(success=False, message=f"Error resetting logs: {e}")

    return jsonify(success=True, message="Counts and logs reset.")

if __name__ == "__main__":
    # Initialize database on startup
    if init_database():
        print("Database initialized successfully")
    else:
        print("Database initialization failed")
    
    app.run(debug=True)