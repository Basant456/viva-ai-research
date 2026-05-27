# Prompt Experiment 01: Python MCQ Generation

## Purpose

The purpose of this experiment was to test how different prompt styles affect the quality of AI-generated multiple-choice questions.

The student submission was based on basic Python programming concepts.

---

## Prompt 1: Basic Prompt

Generate 3 multiple-choice questions based on the student submission.

### Observation

The questions were correct, but they were mostly direct recall questions.

They focused on simple definitions such as:
- data types
- input function
- list vs tuple

Current understanding:
Basic prompts can generate usable questions, but the questions may be more memorization-based.

---

## Prompt 2: Role + Instruction Prompt

You are an educational assessment assistant. Please create 3 MCQs based on the student submission.

### Observation

The questions became more structured and sounded more like assessment questions.

The wording was clearer compared to the basic prompt.

Current understanding:
Adding a role helped improve the educational tone and structure of the output.

---

## Prompt 3: Structured Prompt

You are an educational assessment assistant specialized in Python programming.

Based on the student submission, generate 3 conceptual verification MCQs.

Requirements:
- questions must test conceptual understanding
- avoid direct memorization
- include 4 answer choices
- do not reveal the answer immediately
- explanations should only appear after answer submission

### Observation

This prompt produced the best result.

The questions became more scenario-based and conceptual.

Example:
Instead of asking directly what a float is, the question asked what data type should be used to store a GPA value such as 3.75.

Current understanding:
Structured prompts can guide the LLM to generate better educational questions.

---

## Key Learning

This experiment showed that prompt structure affects the quality of AI-generated MCQs.

Basic prompts generated simple recall-based questions.

Role-based prompts improved tone and structure.

Structured prompts produced more conceptual and application-based questions.

---

## Current Understanding for VIVA-AI

For the VIVA-AI project, the LLM should not only generate random quiz questions.

The goal should be to generate verification MCQs that:
- match the student submission
- test conceptual understanding
- avoid direct memorization
- provide feedback only after student response
