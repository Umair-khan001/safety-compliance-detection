@startuml Use_Case_Diagram_PPE_Detection

!theme vibrant
left to right direction

title PPE Safety Compliance Detection System - Use Case Diagram

actor Admin as admin
actor "Registered User" as regUser
actor Guest as guest

rectangle "User Management" {
  admin -- (Manage User Accounts)
  (Manage User Accounts) .> (Approve/Reject Registration) : <<includes>>
  (Manage User Accounts) .> (Suspend/Activate User) : <<includes>>
  (Manage UserAccounts) .> (View User Details) : <<includes>>
  (Manage User Accounts) .> (Edit User Roles) : <<includes>>
  
  guest -- (Register for Account)
  (Register for Account) --|> regUser : (becomes)
}

rectangle "System Monitoring & Analytics" {
  admin -- (View Admin Dashboard)
  admin -- (View User Activity Logs)
  admin -- (View All Detection Sessions)
}

rectangle "PPE Detection Core Features" {
  regUser -- (Perform Detection via Webcam)
  regUser -- (Perform Detection via Video Upload)
  (Perform Detection via Webcam) ..> (Log Detection Session) : <<includes>>
  (Perform Detection via Video Upload) ..> (Log Detection Session) : <<includes>>
  (Perform Detection via Webcam) ..> (Display Detection Results) : <<includes>>
  (Perform Detection via Video Upload) ..> (Display Detection Results) : <<includes>>
  regUser -- (View Own Detection History)
}

rectangle "Account Management (User)" {
  regUser -- (Login to System)
  (Login to System) <.. guest : (must register first)
  regUser -- (Logout from System)
  regUser -- (Manage Own Profile)
  regUser -- (Change Password)
}

rectangle "General Access" {
    guest -- (View Public Information)
}

note "System uses a PostgreSQL database on Neon.tech" as DbNote
note "Authentication via email/password, bcrypt hashing" as AuthNote
note "Admins manage users and monitor system-wide activity." as AdminNote
admin .. AdminNote
note "Registered Users perform detections and manage their history." as UserNote
regUser .. UserNote

@enduml

## How to Use This PlantUML Code:

1.  **Copy the Code:** Select all the text starting from `@startuml` to `@enduml`.
2.  **Go to an Online PlantUML Editor:**
    *   PlantUML Online Server: [http://www.plantuml.com/plantuml](http://www.plantuml.com/plantuml)
    *   Draw.io: Create a new diagram, click `+` > `Advanced` > `PlantUML`.
    *   Other Markdown editors with PlantUML support (like some VS Code extensions).
3.  **Paste the Code:** Paste the copied code into the editor.
4.  **Generate Diagram:** The diagram should render automatically or after clicking a "Submit" or "Render" button.
5.  **Export:** You can usually export the diagram as a PNG, SVG, or other formats.

## Diagram Overview:

This Use Case Diagram illustrates the interactions between different actors (Admin, Registered User, Guest) and the PPE Safety Compliance Detection System.

### Actors:
*   **Admin:** Manages the system, users, and overall activity.
*   **Registered User:** Authenticated user who can perform PPE detections and manage their account.
*   **Guest:** Unauthenticated visitor who can view public information and register.

### Key Use Case Packages:
*   **User Management:** Admin functions for handling user accounts.
*   **System Monitoring & Analytics:** Admin tools for overseeing system health and activity.
*   **PPE Detection Core Features:** Core functionalities for users to perform and review detections.
*   **Account Management (User):** Standard account operations for registered users.
*   **General Access:** Basic functionalities available to guests.

### Relationships:
*   **Association (`--`):** Direct interaction between an actor and a use case.
*   **Includes (`..>` with `<<includes>>`):** A base use case incorporates the behavior of another use case. This is mandatory.
*   **Extends (`<..` with `<<extends>>`):** An extending use case adds optional behavior to a base use case under certain conditions (not heavily used in this simplified diagram for clarity).
*   **Generalization (`--|>`):** An actor (e.g., Registered User) inherits from another (e.g., after Guest registers).
