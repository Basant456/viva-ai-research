# Assignments API Notes

## Current Understanding

The Assignments API is used to retrieve and manage assignment-related information from Canvas LMS.

From the documentation, assignments seem to contain important information such as:
- assignment id
- assignment name
- assignment description
- due date
- submission types
- course id

---

## Assignment Object

Example fields noticed in the Assignment object:

- id
- name
- description
- due_at
- course_id
- points_possible

Simple understanding:

Canvas returns assignment information in JSON format.

The assignment id looks important because it may later be needed to retrieve submissions.

---

## Important Endpoint

GET /api/v1/courses/:course_id/assignments

Example:

GET /api/v1/courses/101/assignments

Current understanding:

This may retrieve assignments from course 101.

---

## Retrieve a Single Assignment

GET /api/v1/courses/101/assignments/55

Current understanding:

This may retrieve assignment 55 from course 101.

---

## Important Observation

The API structure continues step-by-step.

Example:

Course → Assignment → Submission

The assignment_id appears to be important because it may later connect to the Submissions API.

Example:

GET /api/v1/courses/101/assignments/55/submissions

This may retrieve submissions for assignment 55.

---

## Submission Types

Some submission types noticed in the documentation:

- online_text_entry
- online_upload
- online_url

This may become important later if the project analyzes different types of student submissions.

---

## Current Focus

Right now, the focus is mainly on understanding:
- how assignments are retrieved
- how assignment IDs work
- and how assignments connect to submissions in the Canvas API workflow
