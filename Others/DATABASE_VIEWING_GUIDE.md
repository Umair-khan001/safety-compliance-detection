# 🗄️ Complete Database Viewing & Management Guide

Your PPE Detection System uses a PostgreSQL database hosted on Neon.tech. Here are multiple ways to view and manage your database data online.

## 🚀 Option 1: Neon Console (Recommended - Easiest)

This is the **most convenient** way to view your database.

### Steps:
1. **Go to**: https://console.neon.tech/
2. **Login** with your Neon account credentials
3. **Select your project**: "Safety-Compliance-System" or your project name
4. **Click** on the "**SQL Editor**" tab in the left sidebar
5. **Run queries** to view your data:

### 📊 Useful Queries:

**View all users:**
```sql
SELECT id, email, first_name, last_name, role, status, registration_date, company 
FROM users 
ORDER BY registration_date DESC;
```

**View pending users awaiting approval:**
```sql
SELECT id, email, first_name, last_name, registration_date, company 
FROM users 
WHERE status = 'pending' 
ORDER BY registration_date DESC;
```

**View user activity logs:**
```sql
SELECT ual.*, u.first_name, u.last_name, u.email 
FROM user_activity_logs ual 
JOIN users u ON ual.user_id = u.id 
ORDER BY ual.created_at DESC 
LIMIT 50;
```

**View detection sessions:**
```sql
SELECT ds.*, u.first_name, u.last_name 
FROM detection_sessions ds 
JOIN users u ON ds.user_id = u.id 
ORDER BY ds.started_at DESC 
LIMIT 50;
```

**Database statistics:**
```sql
SELECT 
  (SELECT COUNT(*) FROM users WHERE role = 'customer') as total_users,
  (SELECT COUNT(*) FROM users WHERE status = 'pending') as pending_users,
  (SELECT COUNT(*) FROM users WHERE status = 'approved') as approved_users,
  (SELECT COUNT(*) FROM detection_sessions) as total_sessions,
  (SELECT COUNT(*) FROM user_activity_logs) as total_logs;
```

---

## 💻 Option 2: pgAdmin (Full-featured Desktop App)

For advanced database management and visual interface.

### Installation:
1. **Download**: https://www.pgadmin.org/download/
2. **Install** and open pgAdmin
3. **Create new server connection**:

### Connection Details:
- **Name**: PPE Detection System
- **Host**: `ep-still-wind-a8csmras-pooler.eastus2.azure.neon.tech`
- **Port**: `5432`
- **Database**: `neondb`
- **Username**: `neondb_owner`
- **Password**: `npg_92UPnYfpFWXr`
- **SSL Mode**: Require

### Features:
- 🔍 Browse tables visually
- 📝 Run complex queries
- 📊 View table relationships
- 📈 Database performance monitoring
- 💾 Export data to various formats

---

## 🌐 Option 3: Online Database Viewers

### A. DB Fiddle (PostgreSQL Online)
1. **Go to**: https://www.db-fiddle.com/
2. **Select**: PostgreSQL (latest version)
3. **Connect** using your database credentials
4. **Run queries** directly in the browser

### B. SQL Online
1. **Go to**: https://sqliteonline.com/
2. **Choose**: PostgreSQL option
3. **Connect** and query your data

### C. PostgREST Admin (Web UI)
- Advanced option for REST API access to your database

---

## 🔧 Option 4: VS Code Extension (For Developers)

Perfect for developers who work in VS Code.

### Setup:
1. **Install** "PostgreSQL" extension by Chris Kolkman
2. **Open Command Palette** (Ctrl+Shift+P)
3. **Run**: "PostgreSQL: New Query"
4. **Enter connection details**:
   ```
   Host: ep-still-wind-a8csmras-pooler.eastus2.azure.neon.tech
   Port: 5432
   Database: neondb
   Username: neondb_owner
   Password: npg_92UPnYfpFWXr
   ```

### Features:
- 📝 IntelliSense for SQL
- 🔍 Browse database schema
- ⚡ Run queries with results in tabs
- 💾 Save frequently used queries

---

## 💻 Option 5: Command Line (psql)

For command-line enthusiasts.

### If you have PostgreSQL installed:
```bash
psql "postgresql://neondb_owner:npg_92UPnYfpFWXr@ep-still-wind-a8csmras-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
```

### Install PostgreSQL Client:
- **Windows**: Download from https://www.postgresql.org/download/windows/
- **Mac**: `brew install postgresql`
- **Linux**: `sudo apt-get install postgresql-client`

---

## 📱 Option 6: Database Mobile Apps

### iOS:
- **TableFlip** - PostgreSQL client for iPhone/iPad

### Android:
- **Postgres Manager** - Mobile PostgreSQL client

---

## 🎯 Quick Access via Your Admin Dashboard

Your enhanced admin dashboard now includes:

### 1. **View Database Online** Button
- Click this button in the admin dashboard
- Opens Neon Console directly

### 2. **Export Database** Feature
- Downloads database structure and statistics
- Useful for backups and analysis

### 3. **Real-time Statistics**
- User counts
- Activity logs
- Detection session data

---

## 🛡️ Security Notes

⚠️ **Important Security Tips:**

1. **Never share** your database credentials publicly
2. **Use read-only queries** when possible
3. **Backup regularly** using the export features
4. **Monitor access logs** in Neon Console
5. **Rotate passwords** periodically in Neon settings

---

## 🆘 Troubleshooting

### Connection Issues:
- ✅ Ensure you're using the correct credentials
- ✅ Check if SSL mode is set to "require"
- ✅ Verify your internet connection
- ✅ Try different connection tools

### Query Performance:
- 📊 Use LIMIT clauses for large tables
- 🔍 Add indexes for frequently queried columns
- 📈 Monitor query execution time in Neon Console

### Need Help?
- 📚 Neon Documentation: https://neon.tech/docs
- 💬 PostgreSQL Documentation: https://www.postgresql.org/docs/
- 🎯 Admin Dashboard: Use the built-in export and stats features

---

## 🎉 Pro Tips

1. **Bookmark** Neon Console for quick access
2. **Save** frequently used queries in your favorite tool
3. **Use** the admin dashboard for daily monitoring
4. **Export** data regularly for backup purposes
5. **Monitor** user activity through activity logs

**🌟 Recommended Workflow:**
1. Use **Neon Console** for quick checks and simple queries
2. Use **Admin Dashboard** for user management and statistics
3. Use **pgAdmin** for complex database operations
4. Use **Export features** for data backup and analysis
