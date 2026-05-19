# Canvas API Workflow Notes

## Current Understanding

From studying the Canvas API documentation, it looks like Canvas provides different API endpoints that may allow external applications to retrieve course information, assignments, submissions, and quizzes.

For this project, I am currently trying to understand how these APIs may connect with the VIVA-AI workflow.

---

## Basic Workflow Idea

Possible workflow being explored:

1. Retrieve courses from Canvas LMS
2. Retrieve assignments from a selected course
3. Retrieve submissions from an assignment
4. Send submission content to an LLM
5. Generate verification quiz questions
6. Potentially create a quiz back inside Canvas LMS

---

## Example API Endpoints

### Retrieve Courses

GET /api/v1/courses

This may return available courses from Canvas LMS.

---

### Retrieve Assignments

GET /api/v1/courses/101/assignments

This may return assignments from course 101.

---

### Retrieve Submissions

GET /api/v1/courses/101/assignments/55/submissions

This may return submissions for assignment 55 from course 101.

---

### Create Quiz

POST /api/v1/courses/101/quizzes

This may allow quizzes to be created inside course 101.

---

## Important Observation

The API structure seems connected step-by-step.

Example:

Course → Assignment → Submission

The endpoint structure follows the same pattern.

For example:

GET /api/v1/courses/101/assignments/55/submissions

This represents:
- course 101
- assignment 55
- submissions for that assignment

---

## Current Focus

Right now, the focus is mainly on understanding:
- how Canvas APIs are structured
- how information is retrieved
- and how these APIs may support AI-based verification workflows

The next APIs to explore further are:
- Assignments API
- Submissions API
- Quizzes API
