# Simple Database Setup Guide - Step by Step

## Easy Option: SQLite (No Installation Required)

Since you want to get started quickly, let's use SQLite first. It's a file-based database that requires no installation.

### Step 1: Update your requirements.txt
Add these lines to your `requirements.txt`:
```
Flask-Login==0.6.2
bcrypt==4.0.1
python-dotenv==1.0.0
```

### Step 2: Install new requirements
Open PowerShell in your PPE folder and run:
```powershell
pip install Flask-Login bcrypt python-dotenv
```

### Step 3: Database will be created automatically
- The database file `safety_compliance.db` will be created automatically in your PPE folder
- No manual database setup needed!

## If you want PostgreSQL later (Advanced):

### Option A: Local PostgreSQL
1. Download from: https://www.postgresql.org/download/windows/
2. Install with default settings
3. Remember the password you set
4. Create database:
   ```sql
   CREATE DATABASE safety_compliance_db;
   ```

### Option B: Free Cloud Database (Neon)
1. Go to https://neon.tech/
2. Sign up for free
3. Create new project
4. Copy the connection string they provide

---

**For now, let's start with SQLite - it's the easiest!**
