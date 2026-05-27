# Prompt Experiment 02: Few-Shot Prompting for OOP MCQ Generation

## Purpose

The purpose of this experiment was to test whether providing example MCQs inside the prompt would improve the quality and conceptual depth of AI-generated questions.

The experiment used a student submission based on Object-Oriented Programming (OOP) concepts in Java.

---

## Sample Student Submission Summary

The student submission covered the following Java OOP concepts:

- Introduction to Object-Oriented Programming
- Importance and advantages of OOP
- Classes and Objects
- Encapsulation
- Inheritance
- Polymorphism
- Abstraction
- Constructors and Methods
- Real-world applications of OOP systems

The assignment was theory and concept based.

---

## Few-Shot Prompt Used

You are an educational assessment assistant specialized in any of the programming.

Based on the student submission, generate 3 conceptual verification MCQs.

Example Question Format:

Question:
A programmer wants to store a student's GPA value 3.75 in Python. Which data type would be most appropriate?

A. Integer
B. Boolean
C. Float
D. String

Question:
A programmer wants to repeat a task exactly 5 times. Which loop would be most appropriate?

A. while loop
B. infinite loop
C. for loop
D. conditional loop

Requirements:
- questions must test conceptual understanding
- avoid direct memorization
- include 4 answer choices
- do not reveal answers immediately
- explanations should only appear after answer submission

---

## AI-Generated MCQ Output

### Question 1

A programmer creates a class called Animal with common features like name and age. Later, another class called Dog uses those same features without rewriting them. Which OOP principle is being used?

A. Encapsulation  
B. Inheritance  
C. Abstraction  
D. Polymorphism  

---

### Question 2

A developer wants to protect important student information in a program so users cannot directly change the data without permission. Which OOP concept best supports this idea?

A. Inheritance  
B. Looping  
C. Encapsulation  
D. Compilation  

---

### Question 3

A class blueprint describes the properties and behaviors of a smartphone. Which statement best explains the relationship between the class and an object?

A. The class is a real phone used by customers.  
B. The object is a template used to create classes.  
C. The object is a specific instance created from the class.  
D. Classes and objects are completely unrelated concepts.  

---

## Observation

The generated MCQs became more conceptual and scenario-based compared to previous experiments.

Instead of directly asking for definitions, the questions required students to apply OOP concepts to practical situations.

Examples included:
- identifying inheritance through class reuse
- understanding encapsulation through data protection
- recognizing the relationship between classes and objects

The examples inside the prompt helped guide the AI toward more educational and assessment-focused outputs.

---

## Current Understanding

Few-shot prompting improved:
- question consistency
- conceptual understanding
- educational quality
- scenario-based reasoning

Providing examples within prompts helped the LLM better understand the expected assessment style and output structure.

---

## Comparison with Previous Prompt Experiments

### Basic Prompt
Generated mostly recall-based and definition-focused questions.

### Role + Instruction Prompt
Improved educational tone and structure.

### Few-Shot Prompting
Produced stronger conceptual and application-based MCQs by learning from provided examples.

---

## Research Relevance to VIVA-AI

This experiment suggests that few-shot prompting may help generate stronger AI-based verification quizzes for educational assessment systems.

The workflow currently being explored is:

Student Submission → Few-Shot Prompting → LLM Analysis → Conceptual Verification MCQs

---

## Current Research Direction

The VIVA-AI project is currently exploring:
- prompt engineering techniques
- educational AI workflows
- conceptual verification quizzes
- LLM-generated assessment systems
- AI-assisted learning validation
- Canvas LMS integration workflows

This experiment demonstrates how prompt structure and examples can directly influence the quality of educational AI outputs.
