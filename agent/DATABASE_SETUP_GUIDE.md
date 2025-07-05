# Database Setup Guide for Authentication System

## Option 1: Local PostgreSQL Setup (Recommended for Development)

### Windows Installation:
1. Download PostgreSQL from https://www.postgresql.org/download/windows/
2. Run the installer and follow setup wizard
3. Remember the password you set for the 'postgres' user
4. Default port is 5432

### Create Database:
```bash
# Open Command Prompt or PowerShell
psql -U postgres -h localhost

# Create database
CREATE DATABASE safety_compliance_db;

# Create user (optional)
CREATE USER safety_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE safety_compliance_db TO safety_user;

# Exit
\q
```

### Connection String:
```
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/safety_compliance_db
```

## Option 2: Cloud Database (Production Ready)

### Using Neon (Free PostgreSQL):
1. Go to https://neon.tech/
2. Sign up for free account
3. Create new project
4. Copy connection string provided
5. Use this in your .env file

### Using Supabase:
1. Go to https://supabase.com/
2. Create new project
3. Go to Settings > Database
4. Copy connection string
5. Use this in your .env file

## Option 3: Docker PostgreSQL (Quick Setup)

```bash
# Pull PostgreSQL image
docker pull postgres:15

# Run PostgreSQL container
docker run --name safety-postgres \
  -e POSTGRES_DB=safety_compliance_db \
  -e POSTGRES_USER=safety_user \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  -d postgres:15

# Connection string
DATABASE_URL=postgresql://safety_user:your_password@localhost:5432/safety_compliance_db
```

## Environment Configuration

Create `.env` file in your project root:
```env
# Database
DATABASE_URL=postgresql://your_username:your_password@localhost:5432/safety_compliance_db

# Flask Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
FLASK_ENV=development
FLASK_DEBUG=True

# Upload Settings
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=16777216

# Default Admin
ADMIN_EMAIL=admin@safety.com
ADMIN_PASSWORD=admin123
```

## Database Tables

The system automatically creates these tables on first run:
- `users` - User accounts and authentication data
- `user_activity_logs` - Activity tracking
- `detection_sessions` - Video processing sessions

## Verification Steps

1. Start your Flask app
2. Check console for "Database connection successful"
3. Try to access the application
4. Register a new user account
5. Login as admin to verify database is working

## Troubleshooting

### Connection Issues:
- Verify PostgreSQL service is running
- Check firewall settings
- Confirm database exists
- Validate credentials

### Permission Issues:
- Ensure user has database privileges
- Check PostgreSQL authentication method (pg_hba.conf)

### Port Issues:
- Default PostgreSQL port is 5432
- Check if port is already in use
- Modify connection string if using different port