# Submissions API Notes

## Current Understanding

The Submissions API is used to retrieve student submission information from Canvas LMS.

From the documentation, submissions appear to contain:
- assignment information
- student information
- submission content
- submission type
- timestamps
- grading-related information

For this project, the Submissions API may become one of the most important parts because it connects student work with possible AI analysis workflows.

---

## Submission Object

Some important fields noticed in the Submission object:

- assignment_id
- user_id
- body
- submission_type
- submitted_at
- score
- grade

Simple understanding:

Canvas returns submission information in JSON format.

The `body` field may contain student written responses depending on the submission type.

---

## Important Endpoint

GET /api/v1/courses/:course_id/assignments/:assignment_id/submissions

Example:

GET /api/v1/courses/101/assignments/55/submissions

Current understanding:

This may retrieve submissions for assignment 55 from course 101.

---

## Retrieve a Single Submission

GET /api/v1/courses/101/assignments/55/submissions/134

Current understanding:

This may retrieve the submission from user 134 for assignment 55.

---

## Submission Types Noticed

Some submission types mentioned in the documentation:

- online_text_entry
- online_upload
- online_url
- media_recording

Current understanding:

Different submission types may represent different kinds of student work such as:
- typed responses
- uploaded files
- links
- recorded media

---

## Important Observation

The API workflow continues in connected steps.

Example:

Course → Assignment → Submission

The submission endpoint depends on:
- course_id
- assignment_id
- user_id

This structure helps retrieve more specific information step-by-step.

---

## Connection to VIVA-AI Project

Possible future workflow being explored:

1. Student submits assignment
2. Canvas stores submission
3. Submissions API retrieves student work
4. LLM analyzes submission
5. Verification quiz may be generated
6. Quiz may later be connected back into Canvas LMS

---

## Current Focus

Right now, the focus is mainly on understanding:
- how submissions are retrieved
- how submission objects are structured
- and how submission data may support AI-assisted verification workflows
