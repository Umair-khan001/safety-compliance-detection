#!/usr/bin/env python3
"""
Simplified Authentication Test for Safety Compliance Detection System
"""

from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, IntegerRangeField
from wtforms.validators import DataRequired, Email, Length, EqualTo, InputRequired
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Database configuration
def get_db_connection():
    try:
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        else:
            conn = psycopg2.connect(
                host=os.getenv('PGHOST', 'localhost'),
                database=os.getenv('PGDATABASE', 'postgres'),
                user=os.getenv('PGUSER', 'postgres'),
                password=os.getenv('PGPASSWORD', ''),
                port=os.getenv('PGPORT', 5432),
                cursor_factory=RealDictCursor
            )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# Initialize database
def init_database():
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Create users table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                username VARCHAR(100) UNIQUE NOT NULL,
                phone VARCHAR(20),
                company VARCHAR(200),
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'user',
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_date TIMESTAMP,
                approved_by INTEGER
            )
        ''')
        
        # Create admin user if not exists
        cur.execute("SELECT * FROM users WHERE email = %s", ('admin@safety.com',))
        if not cur.fetchone():
            admin_hash = generate_password_hash('admin123')
            cur.execute('''
                INSERT INTO users (first_name, last_name, email, username, password_hash, role, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', ('Admin', 'User', 'admin@safety.com', 'admin', admin_hash, 'admin', 'approved'))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

# Forms
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=100)])
    phone = StringField('Phone Number', validators=[Length(max=20)])
    company = StringField('Company/Organization', validators=[Length(max=200)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    conf_slide = IntegerRangeField('Confidence:  ', default=25, validators=[InputRequired()])
    submit = SubmitField("Run")

# Helper functions
def get_current_user():
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

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('video_page'))
    
    form = LoginForm()
    if form.validate_on_submit():
        conn = get_db_connection()
        if not conn:
            flash('Database connection error.', 'danger')
            return render_template('login.html', form=form)
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE email = %s", (form.email.data,))
            user = cur.fetchone()
            
            if user and check_password_hash(user['password_hash'], form.password.data):
                if user['status'] != 'approved':
                    flash('Your account is pending approval.', 'warning')
                else:
                    session['user_id'] = user['id']
                    flash('Login successful!', 'success')
                    return redirect(url_for('video_page'))
            else:
                flash('Invalid email or password.', 'danger')
            
            cur.close()
            conn.close()
        except Exception as e:
            flash('Login error occurred.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('video_page'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        conn = get_db_connection()
        if not conn:
            flash('Database connection error.', 'danger')
            return render_template('register.html', form=form)
        
        try:
            cur = conn.cursor()
            
            # Check if user already exists
            cur.execute("SELECT id FROM users WHERE email = %s OR username = %s", 
                       (form.email.data, form.username.data))
            if cur.fetchone():
                flash('User with this email or username already exists.', 'danger')
                return render_template('register.html', form=form)
            
            # Create new user
            password_hash = generate_password_hash(form.password.data)
            cur.execute('''
                INSERT INTO users (first_name, last_name, email, username, phone, company, password_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (form.first_name.data, form.last_name.data, form.email.data, 
                  form.username.data, form.phone.data, form.company.data, password_hash))
            
            conn.commit()
            cur.close()
            conn.close()
            
            flash('Registration successful! Please wait for admin approval.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            flash('Registration error occurred.', 'danger')
    
    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@app.route('/video.html')
def video_page():
    current_user = get_current_user()
    form = UploadFileForm()
    return render_template('video.html', form=form, current_user=current_user)

if __name__ == '__main__':
    init_database()
    app.run(debug=True, host='0.0.0.0', port=8080)