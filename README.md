# viva-ai-research

VIVA-AI is a research prototype for AI-supported assessment verification using
LLM-generated conceptual quizzes and potential Canvas LMS integration.

The project explores how instructors can use AI-assisted analysis and targeted
follow-up questions to verify students' conceptual understanding after assignment
submission.

## Objective

Develop and evaluate an AI-supported assessment verification framework that
analyzes student submissions, identifies cases that may require conceptual
verification, and generates individualized post-submission quizzes using LLMs.

## Research Areas

- Generative AI in Education
- Authentic Assessment
- AI-Assisted Submission Verification
- LLM-Generated Conceptual Quizzes
- Canvas LMS Integration
- Educational Technology

## Technologies

- Python
- Flask
- OpenRouter / OpenAI-compatible LLM APIs
- HTML / CSS
- SQLite
- Canvas REST API
- Git / GitHub

## Prototype Workflow

1. Instructor provides the assignment requirements.
2. Student submission is analyzed by the system.
3. The system assigns a verification concern level:
   - Low Risk
   - Review Suggested
   - Needs Verification
4. Conceptual MCQs are generated based on the assignment and student submission.
5. The instructor reviews the generated verification questions.
6. The questions can be used to verify the student's conceptual understanding.

## Key Features

- Assignment and student submission analysis
- Verification concern scoring
- Concept extraction from student submissions
- Automatic conceptual MCQ generation
- Instructor review workflow
- Student quiz preview
- Quiz answer evaluation and feedback
- Research-oriented prototype interface

## Research Approach

VIVA-AI is not intended to make a definitive determination that a student used
AI.

Instead, the system is designed to identify submissions that may benefit from
additional conceptual verification.

The framework focuses on determining whether students can demonstrate
understanding of the concepts contained in their submitted work through targeted
follow-up questions.

## Team Members

- Basant Aryal
- Prabina Shrestha

**Faculty Supervisor:**  
Dr. Selvarajah Mohanarajah  
Department of Mathematics and Computer Science

## Project Status

**Prototype Development Completed**

The initial VIVA-AI research prototype has been successfully developed and
tested.

Completed work includes:

- Prototype design and implementation
- LLM integration
- Submission analysis workflow
- Verification concern scoring
- Conceptual MCQ generation
- Instructor and student workflow development
- Comparison with existing AI-detection tools
- Experimental testing using sample programming assignments
- Research documentation and reporting

## Current Research Stage

The prototype development phase is complete.

Current work focuses on:

- Research analysis and documentation
- Evaluation of experimental results
- Manuscript preparation and research dissemination

## Important Note

VIVA-AI should not be interpreted as a traditional AI detector.

The system is designed as a **conceptual verification framework** that helps
instructors identify submissions that may require additional assessment and
generate targeted questions to verify student understanding.

The prototype was developed for research and educational purposes and is not
intended to make automated academic misconduct decisions.
