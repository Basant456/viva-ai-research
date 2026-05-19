# Canvas API Structure Notes

## Understanding API Structure

Canvas APIs use endpoints to communicate with Canvas LMS.

Example:

GET /api/v1/courses

Breakdown:
- GET → retrieve information
- /api → API route
- /v1 → version 1
- /courses → course information

Simple meaning:
This endpoint may return available courses from Canvas LMS.

---

## Another Example

GET /api/v1/courses/:course_id/users

Breakdown:
- /courses → course section
- :course_id → specific course ID
- /users → users inside the course

Example:

GET /api/v1/courses/101/users

Simple meaning:
This may return users from course 101.

---

## What is :course_id ?

:course_id is a placeholder value.

It gets replaced with an actual course ID.

Example:

GET /api/v1/courses/:course_id/users

can become:

GET /api/v1/courses/101/users

where 101 is the course ID.

---

## Possible Research Workflow

Current understanding of the possible workflow:

1. Retrieve courses
2. Retrieve assignments from a course
3. Retrieve student submissions
4. Send submission content to an LLM
5. Generate verification quiz questions
6. Potentially create quizzes back into Canvas LMS

---

## Important APIs to Explore Further

- Courses API
- Assignments API
- Submissions API
- Quizzes API

---

## Current Understanding

At this stage, the focus is mainly on understanding how existing Canvas APIs are structured and how they may support the VIVA-AI research workflow.
