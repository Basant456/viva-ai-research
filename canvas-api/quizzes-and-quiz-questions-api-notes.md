# Quizzes and Quiz Questions API Notes

## Current Understanding

After studying the Quizzes API and Quiz Questions API, I understood that creating a quiz in Canvas may involve two main steps.

First, the Quizzes API may be used to create the quiz itself.

Then, the Quiz Questions API may be used to add questions inside that quiz.

---

## Quizzes API

The Quizzes API is used to retrieve, create, update, or delete quizzes inside a Canvas course.

Important endpoint:

POST /api/v1/courses/:course_id/quizzes

Current understanding:

This endpoint may create a new quiz inside a selected course.

Example:

POST /api/v1/courses/101/quizzes

This may create a quiz inside course 101.

Some important quiz fields noticed:

- quiz[title]
- quiz[description]
- quiz[quiz_type]
- quiz[time_limit]
- quiz[allowed_attempts]
- quiz[published]

---

## Quiz Questions API

The Quiz Questions API is used to create and manage questions inside a quiz.

Important endpoint:

POST /api/v1/courses/:course_id/quizzes/:quiz_id/questions

Current understanding:

This endpoint may create a new question inside a selected quiz.

Example:

POST /api/v1/courses/101/quizzes/20/questions

This may create a question inside quiz 20 in course 101.

---

## Important Fields for Quiz Questions

Some important question fields noticed:

- question[question_name]
- question[question_text]
- question[question_type]
- question[position]
- question[points_possible]
- question[answers]

For MCQ-style questions, the important question type appears to be:

multiple_choice_question

---

## Answer Object Understanding

For multiple-choice questions, answers seem to include:

- answer_text
- answer_weight
- answer_comments

Current understanding:

answer_weight seems important because it identifies whether an answer is correct or incorrect.

- answer_weight = 100 means correct answer
- answer_weight = 0 means incorrect answer

---

## Connection to VIVA-AI Project

This API section seems directly connected to the professor’s direction about generating 3–5 MCQs.

Possible workflow being explored:

1. Student submits assignment
2. Submissions API retrieves student work
3. LLM analyzes the submission against assignment requirements
4. LLM generates 3–5 MCQ questions
5. Quizzes API creates the quiz
6. Quiz Questions API adds the generated MCQs into the quiz

---

## Current Understanding

The Quizzes API may create the quiz structure, while the Quiz Questions API may add the actual questions.

This means both APIs may be needed if the project later explores automatically generating verification quizzes inside Canvas LMS.
