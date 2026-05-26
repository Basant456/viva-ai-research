# LLM Limitations and Considerations

## Current Understanding

Today I studied several important limitations and challenges related to Large Language Models (LLMs).

Although LLMs are powerful tools, they are not perfect and may sometimes generate incorrect or unreliable outputs.

Understanding these limitations is important for the VIVA-AI project because the system may later generate educational verification quizzes automatically.

---

# Hallucinations

One major limitation is hallucination.

Current understanding:

LLMs may sometimes generate incorrect information while sounding confident.

Example concerns for the project:
- incorrect MCQs
- incorrect answers
- unrelated questions
- misleading explanations

This means AI-generated educational content may need validation or review.

---

# Limited Reasoning

LLMs may struggle with:
- complex reasoning
- multi-step logic
- mathematical accuracy

Current understanding:
Some generated quiz questions may contain logical or conceptual mistakes.

---

# Context Length and Memory Limitations

LLMs have limited context windows.

Current understanding:
If prompts become too large, the AI may:
- forget earlier instructions
- lose important context
- generate weaker outputs

This may become important later if:
- submissions are long
- rubrics are large
- prompts contain many examples

---

# Bias

LLMs learn from large internet datasets.

Current understanding:
AI responses may sometimes contain:
- bias
- unfair assumptions
- problematic wording

Educational AI systems should minimize biased outputs.

---

# Prompt Hacking / Prompt Injection

Prompt hacking refers to attempts to manipulate AI behavior through instructions inside prompts.

Example concern:
A submission may contain instructions intended to influence the AI system improperly.

Current understanding:
Prompt safety and filtering may become important in future implementation stages.

---

# Reliability Concerns

Current understanding:

AI-generated educational content should not always be trusted automatically.

Important concerns:
- correctness
- educational relevance
- consistency
- reliability

Human review or validation may sometimes be necessary.

---

# Current Understanding for the VIVA-AI Project

Current understanding:

The project is not only about generating quizzes.

It is also important to consider:
- AI reliability
- educational correctness
- hallucination prevention
- prompt quality
- output validation

---

# Current Focus

Right now, the focus is mainly on understanding:
- limitations of LLMs
- possible risks in educational AI systems
- reliability concerns
- safe prompt engineering practices

Advanced mitigation techniques may be explored later.
