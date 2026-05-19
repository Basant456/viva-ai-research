# API Basics Notes

## What is an API?

API stands for Application Programming Interface.

An API helps different applications or systems communicate with each other.

For this research project, Canvas APIs may allow our application to communicate with Canvas LMS to retrieve course information, assignments, submissions, and potentially create quizzes automatically.

---

## What is Canvas LMS?

Canvas LMS is a Learning Management System used by schools and universities to manage:

- Courses
- Assignments
- Quizzes
- Grades
- Student submissions

This is the platform being explored in this research project.

---

## Important HTTP Methods

### GET
Used to retrieve information.

Example:
GET /api/v1/courses

This may allow us to retrieve available courses from Canvas LMS.

---

### POST
Used to create information.

Example:
POST /api/v1/quizzes

This may allow quizzes to be created inside Canvas LMS.

---

### PUT
Used to update existing information.

---

### DELETE
Used to remove information.

---

## Authentication

Canvas APIs require authentication before accessing data.

Example:
Authorization: Bearer <ACCESS-TOKEN>

The access token acts like a permission key that allows authorized access to Canvas LMS.

---

## JSON Format

Canvas API responses are usually returned in JSON format.

Example:

{
  "id": 370663,
  "name": "Sample Course",
  "course_code": "CSC101"
}

JSON helps applications organize and process data more easily.

---

## Connection to Research Project

Potential workflow being explored:

1. Student submits assignment in Canvas LMS
2. Canvas API retrieves submission
3. LLM analyzes the submission
4. AI generates verification quiz questions
5. Quiz may be added back into Canvas LMS

---

## Current Understanding

At this stage, the research is focused on understanding how existing Canvas APIs can support AI-based assessment verification workflows.
