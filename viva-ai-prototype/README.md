# VIVA-AI Verification Quiz Prototype

## Purpose

This is a small early-stage prototype for the VIVA-AI research project.

The goal is to explore this workflow:

```text
Student Submission
        ↓
Submission Analysis
        ↓
Verification Needed / Low Risk
        ↓
Conceptual MCQ Generation
        ↓
Student Answers
        ↓
Feedback After Submission
```

## Current Features

- Instructor can paste assignment requirements
- Instructor can paste student submission
- App performs a basic placeholder verification/risk check
- App extracts simple programming concepts
- App generates 3 conceptual MCQs
- Student answers questions
- Correct answers and explanations appear only after submission

## Important Note

The current risk check is only a placeholder and should not be treated as a real AI detector.

Better wording for the research direction is:

```text
Flag potentially AI-generated or suspicious submissions for verification.
```

## How to Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Future Improvements

- Connect Canvas LMS API
- Retrieve real assignments and submissions
- Use LLM API for MCQ generation
- Add instructor approval screen
- Add proctored quiz workflow idea
- Store results in a database
