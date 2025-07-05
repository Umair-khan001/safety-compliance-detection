# 🛡️ PPE Detection System - Complete ERD Package

## 📊 Database Summary

Your PPE Detection System uses a **PostgreSQL database** with **3 main tables** and **3 key relationships**:

### 📋 Tables Overview:
1. **👥 USERS** - User accounts & authentication
2. **📝 USER_ACTIVITY_LOGS** - Audit trail & activity tracking  
3. **🎥 DETECTION_SESSIONS** - PPE detection results & analytics

---

## 🎨 ERD Files Generated

I've created multiple ERD formats for you:

### 📄 **Text-Based ERDs:**
- `DATABASE_ERD.md` - Comprehensive documentation
- `PPE_Database_ERD_ASCII.txt` - ASCII art diagram

### 🖼️ **Visual ERDs:**
- `PPE_Database_ERD.png` - High-resolution image (300 DPI)
- `PPE_Database_ERD.pdf` - Vector format for printing

### 🌐 **Interactive ERD:**
- `PPE_Database_ERD_Mermaid.md` - Code for interactive diagram

---

## 🚀 How to View Interactive ERD

1. **Open** `PPE_Database_ERD_Mermaid.md`
2. **Copy** the mermaid code block
3. **Visit** https://mermaid.live/
4. **Paste** the code in the editor
5. **View** your beautiful interactive ERD!
6. **Export** as PNG, SVG, or PDF

---

## 🔗 Database Relationships

### 1. **Users ↔ Users (Self-Reference)**
- **Type:** One-to-Many (1:N)
- **Purpose:** Admin approval system
- **Field:** `approved_by` → `users.id`

### 2. **Users ↔ Activity Logs**
- **Type:** One-to-Many (1:N)  
- **Purpose:** Track all user actions
- **Field:** `user_id` → `users.id`
- **Cascade:** DELETE CASCADE

### 3. **Users ↔ Detection Sessions**
- **Type:** One-to-Many (1:N)
- **Purpose:** PPE detection tracking
- **Field:** `user_id` → `users.id`  
- **Cascade:** DELETE CASCADE

---

## 🎯 Key Features

### 🔐 **Security:**
- Password hashing with bcrypt
- Role-based access (admin/customer)
- Complete audit trail logging

### 📈 **Performance:**
- Strategic indexes on frequently queried fields
- JSON storage for flexible detection results
- Optimized CASCADE deletes

### 🛡️ **Data Integrity:**
- Foreign key constraints
- Check constraints for valid values
- Referential integrity protection

---

## 📊 Table Details

### 👥 **USERS Table (16 columns)**
```
Primary Key: id (SERIAL)
Unique Keys: email, username  
Role System: admin/customer
Status Flow: pending → approved/rejected/suspended
```

### 📝 **USER_ACTIVITY_LOGS Table (9 columns)**
```
Tracks: Login, logout, detection sessions, admin actions
Storage: JSON for flexible detection results
Monitoring: IP address, user agent tracking
```

### 🎥 **DETECTION_SESSIONS Table (12 columns)**  
```
Session Types: webcam, video_upload
Metrics: total/safe/unsafe detection counts
Analytics: session duration, confidence thresholds
```

---

## 🌐 Database Access

- **Host:** Neon.tech (PostgreSQL Cloud)
- **Console:** https://console.neon.tech/
- **Admin Panel:** Built into your Flask app
- **Connection:** Already configured in `config.env`

---

## 🎉 Summary

Your database is professionally designed with:
- ✅ **3 well-structured tables**
- ✅ **Proper relationships & constraints**  
- ✅ **Security & audit features**
- ✅ **Performance optimizations**
- ✅ **Scalability considerations**

Perfect for a production PPE detection system! 🚀
