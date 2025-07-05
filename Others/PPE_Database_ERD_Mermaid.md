# PPE Detection System - Database ERD

## Visual ERD (Mermaid.js)

Copy this code to [Mermaid Live Editor](https://mermaid.live/) for interactive diagram:

```mermaid

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

```

## How to Use:
1. Copy the mermaid code above
2. Go to https://mermaid.live/
3. Paste the code in the editor
4. View the interactive ERD diagram
5. Export as PNG, SVG, or PDF
