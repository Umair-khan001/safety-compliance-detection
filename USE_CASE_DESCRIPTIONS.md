# Use Case Descriptions

**Actor: Admin**

1.  **Use Case Name:** Manage Users
    *   **Actor:** Admin
    *   **Description:** Allows the admin to view, activate, deactivate, and delete user accounts.
    *   **Preconditions:** Admin is logged into the system.
    *   **Postconditions:** User account status is updated in the database.
    *   **Main Flow:**
        1.  Admin navigates to the user management page.
        2.  System displays a list of registered users.
        3.  Admin selects a user.
        4.  Admin chooses an action (activate, deactivate, delete).
        5.  System confirms the action.
        6.  System updates the user's status in the database.
        7.  System displays a success message.
    *   **Alternative Flow:**
        *   If the admin tries to delete their own account, the system displays an error message.
        *   If the selected user does not exist, the system displays an error message.

2.  **Use Case Name:** View System Logs
    *   **Actor:** Admin
    *   **Description:** Allows the admin to view system activity logs, including user actions, errors, and security events.
    *   **Preconditions:** Admin is logged into the system.
    *   **Postconditions:** System logs are displayed to the admin.
    *   **Main Flow:**
        1.  Admin navigates to the system logs page.
        2.  System retrieves and displays system logs, possibly with filtering options (e.g., by date, user, event type).
    *   **Alternative Flow:**
        *   If there are no logs to display, the system shows an appropriate message.

3.  **Use Case Name:** View Detection Statistics
    *   **Actor:** Admin
    *   **Description:** Allows the admin to view statistics related to PPE detection, such as the number of videos processed, common violations, and detection accuracy.
    *   **Preconditions:** Admin is logged into the system.
    *   **Postconditions:** Detection statistics are displayed to the admin, possibly in graphical format.
    *   **Main Flow:**
        1.  Admin navigates to the detection statistics page.
        2.  System retrieves and displays detection statistics.
    *   **Alternative Flow:**
        *   If there are no statistics to display, the system shows an appropriate message.

4.  **Use Case Name:** Approve/Reject User Registrations
    *   **Actor:** Admin
    *   **Description:** Allows the admin to review and approve or reject new user registration requests.
    *   **Preconditions:** Admin is logged into the system. There are pending user registration requests.
    *   **Postconditions:** User registration request is approved or rejected. If approved, the user account is activated. User is notified of the decision.
    *   **Main Flow:**
        1.  Admin navigates to the pending registrations page.
        2.  System displays a list of pending user registration requests.
        3.  Admin selects a registration request.
        4.  Admin reviews the user's details.
        5.  Admin chooses to approve or reject the registration.
        6.  System updates the user's status in the database (activates the account if approved).
        7.  System sends a notification email to the user regarding the decision.
        8.  System displays a success message.
    *   **Alternative Flow:**
        *   If there are no pending registrations, the system shows an appropriate message.

**Actor: User**

1.  **Use Case Name:** Register
    *   **Actor:** User (typically a new, unauthenticated user)
    *   **Description:** Allows a new user to create an account in the system.
    *   **Preconditions:** User is not already registered with the provided email.
    *   **Postconditions:** A new user account is created with a 'pending approval' status. A notification is sent to the admin for approval.
    *   **Main Flow:**
        1.  User navigates to the registration page.
        2.  User fills in the registration form (e.g., name, email, password).
        3.  User submits the form.
        4.  System validates the input data.
        5.  System checks if the email is already registered.
        6.  System creates a new user record in the database with 'pending approval' status.
        7.  System sends an email notification to the admin about the new registration.
        8.  System displays a message to the user that their registration is pending approval.
    *   **Alternative Flow:**
        *   If validation fails (e.g., invalid email format, weak password), the system displays error messages.
        *   If the email is already registered, the system displays an error message.

2.  **Use Case Name:** Login
    *   **Actor:** User
    *   **Description:** Allows a registered user to authenticate and access the system.
    *   **Preconditions:** User has a registered and approved account.
    *   **Postconditions:** User is authenticated, a session is created, and the user is redirected to their dashboard or the video upload page.
    *   **Main Flow:**
        1.  User navigates to the login page.
        2.  User enters their email and password.
        3.  User submits the login form.
        4.  System validates the credentials against the database.
        5.  If credentials are valid and the account is active, the system creates a user session.
        6.  System redirects the user to their dashboard or the main application page.
    *   **Alternative Flow:**
        *   If credentials are invalid, the system displays an error message.
        *   If the account is pending approval or deactivated, the system displays an appropriate message.

3.  **Use Case Name:** Upload Video for PPE Detection
    *   **Actor:** User
    *   **Description:** Allows an authenticated user to upload a video file for PPE detection analysis.
    *   **Preconditions:** User is logged in.
    *   **Postconditions:** Video is uploaded to the server, processed for PPE detection, and results are stored. User is notified of processing status.
    *   **Main Flow:**
        1.  User navigates to the video upload page.
        2.  User selects a video file from their local system.
        3.  User initiates the upload.
        4.  System uploads the video file to the server.
        5.  System queues the video for PPE detection processing.
        6.  (Asynchronously) The detection module processes the video.
        7.  Detection results (e.g., violations, timestamps) are stored in the database, associated with the user and video.
        8.  System notifies the user once processing is complete (e.g., via UI update or email).
    *   **Alternative Flow:**
        *   If the file type is not supported, the system displays an error message.
        *   If the file size exceeds the limit, the system displays an error message.
        *   If processing fails, the system logs the error and notifies the user.

4.  **Use Case Name:** View Detection Results
    *   **Actor:** User
    *   **Description:** Allows an authenticated user to view the results of their previously uploaded and processed videos.
    *   **Preconditions:** User is logged in. User has uploaded videos that have been processed.
    *   **Postconditions:** Detection results for selected videos are displayed to the user.
    *   **Main Flow:**
        1.  User navigates to the detection results page or their dashboard.
        2.  System displays a list of videos uploaded by the user and their processing status.
        3.  User selects a processed video to view its results.
        4.  System retrieves and displays the detection results (e.g., annotated video, list of violations, timestamps).
    *   **Alternative Flow:**
        *   If no videos have been processed, the system displays an appropriate message.

5.  **Use Case Name:** View Own Activity Log
    *   **Actor:** User
    *   **Description:** Allows an authenticated user to view their own activity log within the system (e.g., login times, videos uploaded).
    *   **Preconditions:** User is logged in.
    *   **Postconditions:** User's activity log is displayed.
    *   **Main Flow:**
        1.  User navigates to their profile or activity log page.
        2.  System retrieves and displays the user's activity log.
    *   **Alternative Flow:**
        *   If there is no activity to display, the system shows an appropriate message.

6.  **Use Case Name:** Manage Profile
    *   **Actor:** User
    *   **Description:** Allows an authenticated user to view and update their profile information (e.g., name, password).
    *   **Preconditions:** User is logged in.
    *   **Postconditions:** User's profile information is updated in the database.
    *   **Main Flow:**
        1.  User navigates to their profile page.
        2.  System displays the user's current profile information.
        3.  User modifies their information (e.g., changes password, updates name).
        4.  User submits the changes.
        5.  System validates the input.
        6.  System updates the user's profile in the database.
        7.  System displays a success message.
    *   **Alternative Flow:**
        *   If validation fails (e.g., new passwords don't match), the system displays error messages.

7.  **Use Case Name:** Logout
    *   **Actor:** User
    *   **Description:** Allows an authenticated user to end their session and log out of the system.
    *   **Preconditions:** User is logged in.
    *   **Postconditions:** User session is terminated. User is redirected to the login page.
    *   **Main Flow:**
        1.  User clicks the logout button/link.
        2.  System terminates the user's session.
        3.  System redirects the user to the login page.
    *   **Alternative Flow:** None.

---
This completes the detailed use case descriptions.
