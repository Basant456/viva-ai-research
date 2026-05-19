# API Basics Notes

## What is an API?

API stands for Application Programming Interface.

An API acts as a communication bridge between applications or systems.

In this research project, APIs allow our application to communicate with Canvas LMS to retrieve assignments, submissions, and potentially create quizzes automatically.

Example:
- A program can request information from Canvas LMS using APIs.
- Canvas responds with data in JSON format.

---

## Important HTTP Methods

### GET
Used to retrieve data.

Example:
GET /api/v1/courses

Purpose:
Retrieve available courses from Canvas LMS.

---

### POST
Used to create data.

Example:
POST /api/v1/quizzes

Purpose:
Create quizzes inside Canvas LMS.

---

### PUT
Used to update existing data.

---

### DELETE
Used to remove data.

---

## Connection to Research Project

Potential workflow:
1. Student submits assignment
2. Canvas API retrieves submission
3. LLM analyzes submission
4. AI generates verification quiz
5. Quiz is sent back to Canvas LMS
