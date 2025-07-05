# 🗄️ PPE Detection System - Entity Relationship Diagram (ERD)

## Database Schema Overview

This document provides a comprehensive ERD for the Safety Compliance Detection System database.

## ERD Text Representation

```
┌─────────────────────────────────┐
│            USERS                │
├─────────────────────────────────┤
│ PK  id                 SERIAL   │
│ UK  email              VARCHAR  │
│ UK  username           VARCHAR  │
│     password_hash      VARCHAR  │
│     first_name         VARCHAR  │
│     last_name          VARCHAR  │
│     role               VARCHAR  │
│     status             VARCHAR  │
│     registration_date  TIMESTAMP│
│     approved_date      TIMESTAMP│
│ FK  approved_by        INTEGER  │
│     last_login         TIMESTAMP│
│     phone              VARCHAR  │
│     company            VARCHAR  │
│     created_at         TIMESTAMP│
│     updated_at         TIMESTAMP│
└─────────────────────────────────┘
                │
                │ 1:N (approved_by)
                │ ┌─────────────────┐
                └─│ Self-Reference  │
                  └─────────────────┘
                │
        ┌───────┴───────┐
        │ 1:N           │ 1:N
        ▼               ▼
┌─────────────────┐ ┌─────────────────────────┐
│ USER_ACTIVITY   │ │   DETECTION_SESSIONS    │
│     LOGS        │ │                         │
├─────────────────┤ ├─────────────────────────┤
│ PK id    SERIAL │ │ PK id               SERIAL │
│ FK user_id INT  │ │ FK user_id          INTEGER│
│ activity_type   │ │ session_type        VARCHAR│
│ description     │ │ video_filename      VARCHAR│
│ video_filename  │ │ confidence_threshold DECIMAL│
│ detection_res   │ │ total_detections    INTEGER│
│ ip_address      │ │ safe_detections     INTEGER│
│ user_agent      │ │ unsafe_detections   INTEGER│
│ created_at      │ │ session_duration    INTEGER│
└─────────────────┘ │ status              VARCHAR│
                    │ started_at          TIMESTAMP│
                    │ completed_at        TIMESTAMP│
                    └─────────────────────────┘
```

## Detailed Entity Relationships

### 1. USERS Entity
- **Primary Key**: id (SERIAL)
- **Unique Keys**: email, username
- **Self-Reference**: approved_by → users.id (admin approval)

### 2. USER_ACTIVITY_LOGS Entity
- **Primary Key**: id (SERIAL)
- **Foreign Key**: user_id → users.id (CASCADE DELETE)

### 3. DETECTION_SESSIONS Entity
- **Primary Key**: id (SERIAL)
- **Foreign Key**: user_id → users.id (CASCADE DELETE)

## Relationship Types

### 1. Users ↔ Users (Self-Reference)
- **Type**: One-to-Many (1:N)
- **Description**: Admin users can approve multiple customer users
- **Implementation**: approved_by field references users.id

### 2. Users ↔ User Activity Logs
- **Type**: One-to-Many (1:N)
- **Description**: One user can have multiple activity log entries
- **Cascade**: DELETE CASCADE (logs deleted when user is deleted)

### 3. Users ↔ Detection Sessions
- **Type**: One-to-Many (1:N)
- **Description**: One user can have multiple detection sessions
- **Cascade**: DELETE CASCADE (sessions deleted when user is deleted)

## Database Constraints

### Check Constraints
```sql
-- Users table
role IN ('admin', 'customer')
status IN ('pending', 'approved', 'rejected', 'suspended')

-- Detection Sessions table
session_type IN ('webcam', 'video_upload')
status IN ('active', 'completed', 'failed')
```

### Indexes (Performance Optimization)
```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_activity_user_id ON user_activity_logs(user_id);
CREATE INDEX idx_detection_user_id ON detection_sessions(user_id);
```

## Business Rules

1. **User Registration**: New users start with status='pending'
2. **Admin Approval**: Only admin users can approve new registrations
3. **Role Hierarchy**: Admin users have elevated privileges
4. **Activity Tracking**: All user actions are logged
5. **Session Management**: Detection sessions track PPE compliance
6. **Data Integrity**: Cascading deletes maintain referential integrity

## Data Flow

```
1. User Registration → users table (status: pending)
2. Admin Approval → users table (status: approved, approved_by set)
3. User Login → user_activity_logs (activity: login)
4. PPE Detection → detection_sessions (new session created)
5. Detection Results → detection_sessions (results updated)
6. User Actions → user_activity_logs (all activities tracked)
```

## Security Features

- **Password Hashing**: bcrypt for secure password storage
- **Role-Based Access**: Admin vs Customer permissions
- **Audit Trail**: Complete activity logging
- **Data Protection**: Foreign key constraints prevent orphaned data

## Scalability Considerations

- **Indexes**: Optimized for common queries
- **JSON Storage**: Flexible detection_results storage
- **Timestamps**: All tables include creation/update tracking
- **Cascade Deletes**: Efficient data cleanup

This ERD design supports a robust, secure, and scalable PPE detection system with comprehensive user management and activity tracking.
