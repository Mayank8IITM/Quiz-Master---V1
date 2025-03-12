# Quiz Master - V1

## Overview
Quiz Master is a multi-user exam preparation web application featuring role-based access. Admins (Quiz Masters) can manage subjects, chapters, quizzes, and questions, while users can register, take quizzes, view scores, and track performance using interactive statistics.

## Features

### **Admin Features**
- Manage subjects, chapters, quizzes, and questions.
- View all users and quiz attempts.
- Access interactive statistics via Chart.js.

### **User Features**
- Register and log in securely.
- Attempt quizzes based on selected subjects and chapters.
- View quiz history and track performance.

## Technologies Used
- **Back-End:** Flask (Python)
- **Database:** SQLite (Flask-SQLAlchemy ORM)
- **Authentication:** Flask-Login
- **Front-End:** Jinja2, HTML, CSS, Bootstrap
- **Charts & Visualization:** Chart.js

## Project Structure
```
Quiz-Master-V1/
│
├── .venv/                 # Virtual environment (ignored in .gitignore)
├── instance/              # Application instance files
├── static/
│   ├── css/               # CSS files for styling
├── templates/             # Jinja2 HTML templates for Admin and User
│
├── .gitignore             # Git ignore file
├── app.py                 # Main application file 
├── index.html             # Main entry HTML file
├── README.md              # Documentation (this file)
├── requirements.txt       # List of dependencies
```

## Installation

### **Prerequisites**
- Python 3+
- Virtual Environment (recommended)
- SQLite (default database)

### **Setup Steps**

1. **Clone the Repository**
   ```sh
   git clone https://github.com/Mayank8IITM/Quiz-Master---V1.git
   cd quiz-master
   ```

2. **Set Up a Virtual Environment**
   ```sh
   python -m venv venv
   source venv/bin/activate   # On Windows, use `venv\Scripts\activate`
   ```

3. **Install Dependencies**
   ```sh
   pip install -r requirements.txt
   ```

4. **Run the Application**
   ```sh
   python app.py
   ```
   The application will be available at: **http://127.0.0.1:5000/**

## API Endpoints 
The project provides RESTful API endpoints for retrieving data:
- `GET /api/subjects` → Returns all subjects.
- `GET /api/chapters/<subject_id>` → Returns chapters for a subject.
- `GET /api/quizzes/<chapter_id>` → Returns quizzes for a chapter.

---

This project demonstrates full-stack web development using Flask, SQLite, and modern front-end technologies.
