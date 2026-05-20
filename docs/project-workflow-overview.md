# Project Workflow Overview

## Current Understanding

The current focus of the project is to understand how Canvas LMS APIs may connect with AI workflows for assignment verification and quiz generation.

Right now, the project is mainly in the research and learning phase.

---

## Workflow Understanding So Far

Current workflow understanding:

Course → Assignment → Submission → LLM Analysis → Verification Quiz

Simple understanding:

1. Retrieve courses from Canvas LMS
2. Retrieve assignments from a selected course
3. Retrieve submissions from an assignment
4. Send submission content to an LLM
5. Generate verification quiz questions
6. Potentially connect quizzes back into Canvas LMS

---

## APIs Explored So Far

### Courses API

Current understanding:
Used to retrieve course-related information.

Example:

GET /api/v1/courses

---

### Assignments API

Current understanding:
Used to retrieve assignment-related information.

Example:

GET /api/v1/courses/:course_id/assignments

---

### Submissions API

Current understanding:
Used to retrieve student submission information.

Example:

GET /api/v1/courses/:course_id/assignments/:assignment_id/submissions

This currently appears to be one of the most important APIs for the project because it may provide the actual student submission content.

---

## Important Observation

The APIs appear to follow a connected structure.

Example:

Course → Assignment → Submission

Each API depends on IDs from previous APIs such as:
- course_id
- assignment_id
- user_id

---

## Possible AI Workflow Being Explored

Possible future workflow idea:

Student submits assignment
        ↓
Canvas stores submission
        ↓
Submissions API retrieves submission
        ↓
LLM analyzes submission
        ↓
Verification quiz may be generated
        ↓
Quiz may later connect back into Canvas LMS

---

## Current Focus

Right now, the focus is mainly on:
- understanding Canvas API structure
- understanding workflow connections
- identifying important APIs
- organizing documentation and research notes in GitHub

Coding and implementation may be explored later after gaining a better understanding of the workflow and APIs.
