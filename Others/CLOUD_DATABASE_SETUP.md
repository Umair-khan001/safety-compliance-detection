# Free Cloud Database Setup Guide

## Using Neon.tech (Free PostgreSQL Cloud Database)

### Step 1: Create Account
1. Go to https://neon.tech/
2. Click "Sign Up" 
3. Sign up using your GitHub, Google, or email
4. Verify your email if needed

### Step 2: Create Database
1. After login, click "Create Project"
2. Give your project a name: `Safety-Compliance-System`
3. Select region closest to you
4. Click "Create Project"

### Step 3: Get Connection String
1. On your project dashboard, you'll see "Connection Details"
2. Copy the connection string - it looks like:
   ```
   postgresql://username:password@host/database?sslmode=require
   ```
3. Keep this safe - we'll use it in the next step

### Step 4: Update Your Config
1. Open `config.env` file in your PPE folder
2. Add this line (replace with your actual connection string):
   ```
   DATABASE_URL=postgresql://your_username:your_password@your_host/your_database?sslmode=require
   ```

### Alternative: Supabase (Another Free Option)
1. Go to https://supabase.com/
2. Sign up and create new project
3. Go to Settings → Database
4. Copy the connection string
5. Use it in your `config.env` file

## That's it! Your cloud database is ready to use.
