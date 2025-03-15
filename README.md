# CHETGPT: This is an early version when i try to build the app in VS code using Kivy. Sadly, it's so slow i have to move to Android Studio and use Kotlin. The app is up and running for my church community. I only need to add the location tracking now. <--- It's a joke

# BY CHATGPT

## 📌 Overview
**JTMS Alpha 1.3** is a **task management system** designed for **church communities** to track and manage member tasks, reports, and communication. It integrates **Google Sheets, Google Drive, and authentication APIs** to provide an efficient workflow for **task reporting, verification, and document management**.

## 🚀 Features
- **📋 Task Reporting**: Members can submit reports with task type, notes, and file uploads.
- **✅ Task Verification**: Leaders can verify submitted reports and update statuses.
- **📊 Google Sheets Integration**: Stores member, customer, and task data securely.
- **📂 Google Drive Integration**: Allows members to **upload files** related to their reports.
- **🔒 Google Authentication**: Supports login via **Google OAuth**.
- **📱 Mobile-Friendly UI**: Optimized for mobile with **Kivy framework**.
- **🗂️ Group-Based Management**: Leaders oversee specific groups and verify reports.

## 📦 Dependencies
Ensure you have the required Python packages installed:
```bash
pip install kivy google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

## 🛠 How to Use
1. **Run the Application**:
   ```bash
   python JTMS_Alpha.1.3.py
   ```
2. **Login with Username/Google**.
3. **Members** can submit task reports.
4. **Leaders** can verify reports and approve tasks.
5. **All data is stored in Google Sheets and Drive**.

## 🔑 Key Functionalities
### 🏠 **User Roles & Permissions**
- **Members**: Submit task reports and attach documents.
- **Leaders**: Verify member reports and update task statuses.
- **Observers**: View submitted reports without modifying them.
- **Admins**: Oversee the entire system and user management.

### 📋 **Task Reporting & File Uploads**
- Members submit task reports including:
  - **Customer Name**
  - **Task Type** (Chat, Visit, Video Call)
  - **Task Notes**
  - **File Uploads** (Stored in Google Drive)

### ✅ **Task Verification for Leaders**
- View pending tasks from group members.
- Review **notes and file attachments**.
- Approve or reject reports with **one-click verification**.

### 📡 **Google Sheets & Drive Integration**
- Stores member/customer/task data in **Google Sheets**.
- Uploaded documents are stored securely in **Google Drive**.

## 📁 File Outputs
- **Google Sheets** → Stores user, task, and verification data.
- **Google Drive** → Stores task-related documents.

## 📌 Next Steps
- Add **push notifications** for task verification.
- Improve **UI/UX** for better mobile experience.
- Integrate **automated reports for church management**.

## 🤝 Contributing
Contributions are welcome! Feel free to submit **issues** or **pull requests** to enhance the functionality.

---
⛪ *Church Task Management System - Organizing church tasks efficiently!*
