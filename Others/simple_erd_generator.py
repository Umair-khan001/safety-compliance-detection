#!/usr/bin/env python3
"""
Simple ERD Generator using ASCII art and mermaid.js syntax
For PPE Detection System Database
"""

def generate_ascii_erd():
    """Generate ASCII-based ERD diagram"""
    
    erd_ascii = """
╔═══════════════════════════════════════════════════════════════════════════════════════════╗
║                           🛡️ PPE DETECTION SYSTEM - DATABASE ERD                          ║
╚═══════════════════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────┐
│             👥 USERS                │
├─────────────────────────────────────┤
│ 🔑 id                   SERIAL (PK) │
│ 📧 email                VARCHAR(UK) │
│ 👤 username             VARCHAR(UK) │
│ 🔒 password_hash        VARCHAR     │
│ 👨 first_name           VARCHAR     │
│ 👩 last_name            VARCHAR     │
│ 🎭 role                 VARCHAR     │
│ 📊 status               VARCHAR     │
│ 📅 registration_date    TIMESTAMP   │
│ ✅ approved_date        TIMESTAMP   │
│ 👨‍💼 approved_by          INT (FK)    │
│ 🕐 last_login           TIMESTAMP   │
│ 📞 phone                VARCHAR     │
│ 🏢 company              VARCHAR     │
│ 📅 created_at           TIMESTAMP   │
│ 📅 updated_at           TIMESTAMP   │
└─────────────────────────────────────┘
                    │
                    │ ╭──────────────╮
                    └─│ SELF-REF 1:N │ (approved_by)
                      ╰──────────────╯
                    │
        ┌───────────┴───────────┐
        │ 1:N                   │ 1:N
        ▼                       ▼
┌─────────────────────┐   ┌─────────────────────────┐
│  📝 USER_ACTIVITY   │   │    🎥 DETECTION         │
│      LOGS           │   │       SESSIONS          │
├─────────────────────┤   ├─────────────────────────┤
│ 🔑 id       SERIAL  │   │ 🔑 id               SERIAL │
│ 👤 user_id  INT(FK) │   │ 👤 user_id          INT(FK)│
│ 🎯 activity_type    │   │ 🎭 session_type     VARCHAR│
│ 📝 description      │   │ 🎥 video_filename   VARCHAR│
│ 🎥 video_filename   │   │ 🎯 confidence_thresh DECIMAL│
│ 🔍 detection_results│   │ 📊 total_detections  INTEGER│
│ 🌐 ip_address       │   │ ✅ safe_detections   INTEGER│
│ 🖥️ user_agent       │   │ ❌ unsafe_detections INTEGER│
│ 📅 created_at       │   │ ⏱️ session_duration  INTEGER│
└─────────────────────┘   │ 📊 status            VARCHAR│
                          │ 🕐 started_at        TIMESTAMP│
                          │ 🏁 completed_at      TIMESTAMP│
                          └─────────────────────────┘

╔═══════════════════════════════════════════════════════════════════════════════════════════╗
║                                    RELATIONSHIP DETAILS                                   ║
╠═══════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                           ║
║  🔗 USERS ↔ USERS (Self-Reference)                                                       ║
║     • Type: One-to-Many (1:N)                                                            ║
║     • Field: approved_by → users.id                                                      ║
║     • Purpose: Admin users approve customer registrations                                ║
║                                                                                           ║
║  🔗 USERS ↔ USER_ACTIVITY_LOGS                                                           ║
║     • Type: One-to-Many (1:N)                                                            ║
║     • Field: user_id → users.id                                                          ║
║     • Purpose: Track all user actions and system events                                  ║
║     • Cascade: DELETE CASCADE                                                            ║
║                                                                                           ║
║  🔗 USERS ↔ DETECTION_SESSIONS                                                           ║
║     • Type: One-to-Many (1:N)                                                            ║
║     • Field: user_id → users.id                                                          ║
║     • Purpose: Track PPE detection sessions (webcam/upload)                              ║
║     • Cascade: DELETE CASCADE                                                            ║
║                                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════════════════════╝

╔═══════════════════════════════════════════════════════════════════════════════════════════╗
║                                  BUSINESS RULES & CONSTRAINTS                            ║
╚═══════════════════════════════════════════════════════════════════════════════════════════╝

📋 CHECK CONSTRAINTS:
   • users.role IN ('admin', 'customer')
   • users.status IN ('pending', 'approved', 'rejected', 'suspended')
   • detection_sessions.session_type IN ('webcam', 'video_upload')
   • detection_sessions.status IN ('active', 'completed', 'failed')

🚀 PERFORMANCE INDEXES:
   • idx_users_email ON users(email)
   • idx_users_status ON users(status)
   • idx_activity_user_id ON user_activity_logs(user_id)
   • idx_detection_user_id ON detection_sessions(user_id)

🛡️ SECURITY FEATURES:
   • Password hashing with bcrypt
   • Role-based access control (RBAC)
   • Complete audit trail logging
   • Referential integrity protection

📈 SCALABILITY:
   • JSON storage for flexible detection results
   • Optimized queries with strategic indexes
   • Cascade deletes for data cleanup
   • Timestamp tracking on all entities

══════════════════════════════════════════════════════════════════════════════════════════════
Database: PostgreSQL | Host: Neon.tech | Tables: 3 | Relationships: 3 | Indexes: 4
══════════════════════════════════════════════════════════════════════════════════════════════
"""
    return erd_ascii

def generate_mermaid_erd():
    """Generate Mermaid.js ERD syntax for online rendering"""
    
    mermaid_code = """
erDiagram
    USERS {
        serial id PK
        varchar email UK
        varchar username UK
        varchar password_hash
        varchar first_name
        varchar last_name
        varchar role
        varchar status
        timestamp registration_date
        timestamp approved_date
        integer approved_by FK
        timestamp last_login
        varchar phone
        varchar company
        timestamp created_at
        timestamp updated_at
    }
    
    USER_ACTIVITY_LOGS {
        serial id PK
        integer user_id FK
        varchar activity_type
        text description
        varchar video_filename
        json detection_results
        inet ip_address
        text user_agent
        timestamp created_at
    }
    
    DETECTION_SESSIONS {
        serial id PK
        integer user_id FK
        varchar session_type
        varchar video_filename
        decimal confidence_threshold
        integer total_detections
        integer safe_detections
        integer unsafe_detections
        integer session_duration
        varchar status
        timestamp started_at
        timestamp completed_at
    }
    
    USERS ||--o{ USER_ACTIVITY_LOGS : "user_id"
    USERS ||--o{ DETECTION_SESSIONS : "user_id"
    USERS ||--o{ USERS : "approved_by (self-ref)"
"""
    return mermaid_code

def save_erd_files():
    """Save ERD diagrams to files"""
    
    # Save ASCII ERD
    with open('PPE_Database_ERD_ASCII.txt', 'w', encoding='utf-8') as f:
        f.write(generate_ascii_erd())
    
    # Save Mermaid ERD
    with open('PPE_Database_ERD_Mermaid.md', 'w', encoding='utf-8') as f:
        f.write("# PPE Detection System - Database ERD\n\n")
        f.write("## Visual ERD (Mermaid.js)\n\n")
        f.write("Copy this code to [Mermaid Live Editor](https://mermaid.live/) for interactive diagram:\n\n")
        f.write("```mermaid\n")
        f.write(generate_mermaid_erd())
        f.write("\n```\n\n")
        f.write("## How to Use:\n")
        f.write("1. Copy the mermaid code above\n")
        f.write("2. Go to https://mermaid.live/\n")
        f.write("3. Paste the code in the editor\n")
        f.write("4. View the interactive ERD diagram\n")
        f.write("5. Export as PNG, SVG, or PDF\n")
    
    print("✅ ERD files created successfully!")
    print("📄 Files generated:")
    print("   • PPE_Database_ERD_ASCII.txt (Text-based diagram)")
    print("   • PPE_Database_ERD_Mermaid.md (Interactive diagram code)")
    print("\n🔗 For interactive diagram:")
    print("   1. Open PPE_Database_ERD_Mermaid.md")
    print("   2. Copy the mermaid code")
    print("   3. Visit: https://mermaid.live/")
    print("   4. Paste and view your ERD!")

if __name__ == "__main__":
    # Print ASCII ERD to console
    print(generate_ascii_erd())
    
    # Save all ERD files
    save_erd_files()
