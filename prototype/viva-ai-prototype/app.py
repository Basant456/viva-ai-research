from flask import Flask, render_template, request, session, redirect, url_for
from docx import Document
from pypdf import PdfReader
import re

app = Flask(__name__)
app.secret_key = "change-this-secret-key"


def extract_text_from_file(file):
    filename = file.filename.lower()

    if filename.endswith(".txt"):
        return file.read().decode("utf-8", errors="ignore")

    if filename.endswith(".docx"):
        doc = Document(file)
        return "\n".join([p.text for p in doc.paragraphs])

    if filename.endswith(".pdf"):
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    return ""


def analyze_ai_risk(submission_text):
    text = submission_text.strip()
    text_lower = text.lower()

    words = re.findall(r"\b\w+\b", text_lower)
    word_count = len(words)

    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    sentence_count = len(sentences)

    if sentence_count > 0:
        avg_sentence_length = round(word_count / sentence_count, 1)
    else:
        avg_sentence_length = 0

    long_sentence_count = 0
    for sentence in sentences:
        if len(sentence.split()) > 30:
            long_sentence_count += 1

    transition_phrases = [
        "furthermore",
        "moreover",
        "in conclusion",
        "therefore",
        "additionally",
        "as a result",
        "overall",
        "it is important to note",
        "in today's world",
        "this essay will discuss"
    ]

    generic_phrases = [
        "plays a crucial role",
        "significant impact",
        "it is essential",
        "cannot be overstated",
        "in various ways",
        "rapidly evolving",
        "wide range of",
        "important aspect",
        "this highlights the importance",
        "modern society"
    ]

    transition_count = sum(text_lower.count(phrase) for phrase in transition_phrases)
    generic_count = sum(text_lower.count(phrase) for phrase in generic_phrases)

    personal_words = ["i", "my", "me", "we", "our", "us"]
    personal_count = sum(words.count(word) for word in personal_words)

    citation_markers = [
        "according to",
        "research shows",
        "source",
        "reference",
        "citation",
        "cited",
        "journal",
        "et al"
    ]

    citation_count = sum(text_lower.count(marker) for marker in citation_markers)

    score = 0
    reasons = []

    if word_count > 800:
        score += 15
        reasons.append("Submission has a high word count.")

    if avg_sentence_length > 24:
        score += 15
        reasons.append("Average sentence length is high.")

    if long_sentence_count >= 4:
        score += 15
        reasons.append("Several long sentences were detected.")

    if transition_count >= 4:
        score += 15
        reasons.append("Frequent formal transition phrases were detected.")

    if generic_count >= 3:
        score += 20
        reasons.append("Generic academic phrases were detected.")

    if personal_count == 0 and word_count > 250:
        score += 10
        reasons.append("Few personal explanation markers were found.")

    if citation_count == 0 and word_count > 400:
        score += 10
        reasons.append("No citation or source-related markers were found.")

    if score >= 60:
        status = "Needs Verification"
    elif score >= 30:
        status = "Review Suggested"
    else:
        status = "Low Risk"

    if not reasons:
        reasons.append("No major AI-risk writing patterns were detected.")

    key_concepts = extract_key_concepts(words)

    return {
        "status": status,
        "reason": " ".join(reasons),
        "score": score,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_sentence_length": avg_sentence_length,
        "long_sentence_count": long_sentence_count,
        "transition_count": transition_count,
        "generic_count": generic_count,
        "personal_count": personal_count,
        "citation_count": citation_count,
        "key_concepts": key_concepts
    }


def extract_key_concepts(words):
    stop_words = {
        "the", "and", "for", "that", "this", "with", "from", "have",
        "are", "was", "were", "has", "had", "but", "not", "you",
        "your", "they", "their", "its", "into", "also", "can",
        "will", "would", "should", "could", "about", "there",
        "which", "when", "what", "where", "how", "why", "then",
        "than", "been", "being", "because", "through", "these",
        "those", "such", "more", "most"
    }

    frequency = {}

    for word in words:
        if len(word) > 4 and word not in stop_words:
            frequency[word] = frequency.get(word, 0) + 1

    sorted_words = sorted(frequency.items(), key=lambda x: x[1], reverse=True)

    return [word for word, count in sorted_words[:3]]


def generate_mcqs(assignment, submission, key_concepts):
    if not key_concepts:
        key_concepts = ["main concept", "student understanding", "assignment topic"]

    concept_1 = key_concepts[0]
    concept_2 = key_concepts[1] if len(key_concepts) > 1 else "supporting idea"
    concept_3 = key_concepts[2] if len(key_concepts) > 2 else "application"

    return [
        {
            "question": f"Which statement best explains the role of {concept_1} in the submitted assignment?",
            "options": [
                f"{concept_1} is one of the main ideas that should be explained conceptually.",
                f"{concept_1} is unrelated to the assignment.",
                f"{concept_1} only matters for formatting.",
                f"{concept_1} replaces the need for instructor review."
            ],
            "answer": f"{concept_1} is one of the main ideas that should be explained conceptually.",
            "explanation": "This question checks whether the student understands a major concept from the submission."
        },
        {
            "question": f"How does {concept_2} support the overall argument or explanation in the assignment?",
            "options": [
                "It helps connect the main idea to supporting evidence or reasoning.",
                "It proves the assignment was automatically generated.",
                "It removes the need for examples.",
                "It is only used to increase word count."
            ],
            "answer": "It helps connect the main idea to supporting evidence or reasoning.",
            "explanation": "This checks whether the student can explain how supporting concepts fit into the assignment."
        },
        {
            "question": f"If the instructor asks about {concept_3}, what should the student be able to do?",
            "options": [
                "Explain it in their own words using the context of the assignment.",
                "Only repeat the exact sentence from the submission.",
                "Avoid answering because the system already analyzed it.",
                "Say that it is not related to the assignment."
            ],
            "answer": "Explain it in their own words using the context of the assignment.",
            "explanation": "The purpose of verification is to check conceptual understanding, not memorization."
        }
    ]


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        assignment = request.form.get("assignment", "")
        submission_text = request.form.get("submission", "")

        uploaded_file = request.files.get("submission_file")

        if uploaded_file and uploaded_file.filename:
            extracted_text = extract_text_from_file(uploaded_file)
            if extracted_text.strip():
                submission_text = extracted_text

        risk_result = analyze_ai_risk(submission_text)

        questions = []
        if risk_result["status"] in ["Review Suggested", "Needs Verification"]:
            questions = generate_mcqs(
                assignment,
                submission_text,
                risk_result["key_concepts"]
            )

        session["assignment"] = assignment
        session["submission"] = submission_text
        session["risk_result"] = risk_result
        session["questions"] = questions

        return redirect(url_for("review"))

    return render_template("index.html")


@app.route("/review")
def review():
    return render_template(
        "review.html",
        risk=session.get("risk_result"),
        questions=session.get("questions")
    )


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    questions = session.get("questions", [])

    if request.method == "POST":
        results = []
        score = 0

        for i, q in enumerate(questions):
            selected = request.form.get(f"question_{i}")
            correct = q["answer"]

            if selected == correct:
                score += 1

            results.append({
                "question": q["question"],
                "selected": selected,
                "correct": correct,
                "explanation": q["explanation"],
                "is_correct": selected == correct
            })

        return render_template(
            "results.html",
            results=results,
            score=score,
            total=len(questions)
        )

    return render_template("quiz.html", questions=questions)


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)