# LLM and Verification Quiz Workflow Notes

## Current Understanding

After studying the Quizzes API and Quiz Questions API, I started understanding how the LLM workflow may connect with Canvas LMS for the VIVA-AI project.

Current workflow understanding:

Student Submission
        ↓
Submissions API retrieves submission
        ↓
LLM analyzes submission
        ↓
LLM generates verification MCQs
        ↓
Quizzes API creates quiz
        ↓
Quiz Questions API adds MCQ questions

---

## Current Understanding of LLM Workflow

The LLM does not directly retrieve information from Canvas LMS.

Canvas APIs retrieve the data, while the LLM may analyze the retrieved submission content.

For example:
- Canvas APIs may retrieve assignments and submissions
- the LLM may analyze the submission
- the LLM may generate verification quiz questions

---

## Important Understanding

The project idea is not simply to generate random quiz questions.

The goal seems to be:
- analyze the student submission
- compare it against assignment requirements
- generate questions that verify understanding

---

## Example Workflow Explored

### Assignment Requirement

Explain how GET and POST requests work and how APIs use JSON communication.

---

### Student Submission

GET is used to retrieve data from a system through an API.

POST is used to create or send new data to a system.

APIs often return or send data in JSON format because JSON is structured and easy for programs to process.

---

## Possible LLM-Generated MCQ Example

Question:

What is the main purpose of a GET request?

A. Retrieve data from a system
B. Delete data from a database
C. Encrypt API communication
D. Restart the server

Correct Answer:
A. Retrieve data from a system

---

## Important Observation

The generated quiz questions are based on:
- assignment requirements
- concepts used in the student submission
- important technical understanding

This may help verify whether the student understands the concepts used in the submission.

---

## Current Understanding of APIs vs LLM

### Canvas APIs
May handle:
- retrieving submissions
- retrieving assignments
- creating quizzes
- adding quiz questions

### LLM
May handle:
- analyzing submissions
- understanding concepts
- generating verification MCQs

---

## Current Focus

Right now, the focus is mainly on understanding:
- how LLM workflows may connect with Canvas LMS
- how submissions may be analyzed
- how verification MCQs may be generated
- how APIs and LLM workflows connect together

Implementation and testing may be explored later.
