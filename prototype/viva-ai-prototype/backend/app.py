from flask import Flask, render_template, request, session, redirect, url_for
from docx import Document
from pypdf import PdfReader
from dotenv import load_dotenv
import requests
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH, override=True)

print("RUNNING OPENAI / OPENROUTER VERSION")
print("App file:", __file__)
print("Env file:", ENV_PATH)

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["SESSION_COOKIE_NAME"] = "viva_ai_session_v2"

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openrouter").lower()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

def key_is_loaded(key):
    if not key:
        return False

    placeholder_parts = [
        "your_",
        "your-real",
        "your_real",
        "replace",
        "paste",
        "here"
    ]

    lowered = key.lower()
    return not any(part in lowered for part in placeholder_parts)


print("Provider:", LLM_PROVIDER)
print("OpenRouter Key Loaded:", key_is_loaded(OPENROUTER_API_KEY))
print("OpenAI Key Loaded:", key_is_loaded(OPENAI_API_KEY))


@app.after_request
def prevent_cached_review_pages(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


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


def build_prompt(assignment, submission):
    return f"""
You are an academic integrity verification assistant.

Analyze the student submission and provide an AI-writing risk assessment based on writing style, structure, reasoning patterns, and overall characteristics.

Do not claim that the student definitely used AI. Do not accuse the student. Provide only a risk assessment showing whether additional verification may be appropriate.

Then identify the most important concepts that a genuine author of the work should understand.

Then generate 3-5 conceptual verification MCQs designed to determine whether the student truly understands the submitted material.

Requirements:
- Focus only on concepts that appear in the submission.
- Questions must test understanding rather than memorization.
- Use realistic scenarios whenever possible.
- Avoid directly quoting the submission.
- Questions should be difficult for someone who copied the work without understanding it.
- Include four answer choices for each question.
- Include one correct answer.
- Include a short explanation.
- Do not ask whether the student used AI.
- Do not ask questions about grammar, formatting, or citations.

Return ONLY valid JSON in this format:

{{
  "status": "Low Risk | Review Suggested | Needs Verification",
  "score": 0,
  "reason": "Brief explanation of the AI-writing risk assessment.",
  "key_concepts": ["Concept 1", "Concept 2", "Concept 3"],
  "questions": [
    {{
      "question": "Question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Correct option text",
      "explanation": "Short explanation"
    }}
  ]
}}

Assignment Instructions:
{assignment}

Student Submission:
{submission[:5000]}
"""


def clean_json_response(content):
    content = content.strip()

    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "").strip()
    elif content.startswith("```"):
        content = content.replace("```", "").strip()

    start = content.find("{")
    end = content.rfind("}")

    if start != -1 and end != -1:
        content = content[start:end + 1]

    return json.loads(content)


def call_openrouter(prompt):
    if not key_is_loaded(OPENROUTER_API_KEY):
        raise ValueError("Missing or placeholder OPENROUTER_API_KEY")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are an academic integrity verification assistant. Return only valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3,
        "max_tokens": 1800
    }

    response = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=45
    )

    print("API response status code:", response.status_code)

    if not response.ok:
        print("API error response body:", response.text)
        raise RuntimeError(f"OpenRouter API error {response.status_code}: {response.text}")

    content = response.json()["choices"][0]["message"]["content"]
    return clean_json_response(content)


def call_openai(prompt):
    if not key_is_loaded(OPENAI_API_KEY):
        raise ValueError("Missing or placeholder OPENAI_API_KEY")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are an academic integrity verification assistant. Return only valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3,
        "max_tokens": 1800
    }

    response = requests.post(
        OPENAI_URL,
        headers=headers,
        json=payload,
        timeout=45
    )

    print("API response status code:", response.status_code)

    if not response.ok:
        print("API error response body:", response.text)
        raise RuntimeError(f"OpenAI API error {response.status_code}: {response.text}")

    content = response.json()["choices"][0]["message"]["content"]
    return clean_json_response(content)


def analyze_submission_with_llm(assignment, submission):
    prompt = build_prompt(assignment, submission)

    try:
        print("Selected provider:", LLM_PROVIDER)
        print("OpenRouter Key Loaded:", key_is_loaded(OPENROUTER_API_KEY))
        print("OpenAI Key Loaded:", key_is_loaded(OPENAI_API_KEY))

        if LLM_PROVIDER == "openai":
            return call_openai(prompt)

        return call_openrouter(prompt)

    except Exception as error:
        print("LLM Error:", error)

        return {
            "status": "API Error",
            "score": 0,
            "reason": str(error),
            "key_concepts": [],
            "questions": []
        }


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        session.clear()

    if request.method == "POST":
        session.clear()

        assignment = request.form.get("assignment", "")
        submission_text = ""

        uploaded_file = request.files.get("submission_file")

        if uploaded_file and uploaded_file.filename:
            extracted_text = extract_text_from_file(uploaded_file)
            if extracted_text.strip():
                submission_text = extracted_text

        if not submission_text.strip():
            llm_result = {
                "status": "API Error",
                "score": 0,
                "reason": "No readable submission text was found. Please upload a PDF, DOCX, or TXT file with readable text.",
                "key_concepts": [],
                "questions": []
            }
        else:
            llm_result = analyze_submission_with_llm(assignment, submission_text)

        risk_result = {
            "status": llm_result.get("status", "Review Suggested"),
            "score": llm_result.get("score", 0),
            "reason": llm_result.get("reason", "No explanation provided."),
            "key_concepts": llm_result.get("key_concepts", [])
        }

        questions = llm_result.get("questions", [])

        session["assignment"] = assignment
        session["submission"] = submission_text
        session["risk_result"] = risk_result
        session["questions"] = questions

        return redirect(url_for("review"))

    return render_template("index.html")


@app.route("/review")
@app.route("/review/")
def review():
    return render_template(
        "review.html",
        risk=session.get("risk_result"),
        questions=session.get("questions"),
        provider=LLM_PROVIDER,
        app_file=__file__,
        env_file=ENV_PATH
    )


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    questions = session.get("questions", [])

    if not questions:
        return render_template(
            "quiz_error.html",
            message="No verification questions are available. If this was caused by an API error, check the review page for the exact error message."
        )

    if request.method == "POST":
        results = []
        score = 0

        for i, q in enumerate(questions):
            selected = request.form.get(f"question_{i}")
            correct = q.get("answer")

            if selected == correct:
                score += 1

            results.append({
                "question": q.get("question"),
                "selected": selected,
                "correct": correct,
                "explanation": q.get("explanation"),
                "is_correct": selected == correct
            })

        return render_template(
            "results.html",
            results=results,
            score=score,
            total=len(questions)
        )

    return render_template("quiz.html", questions=questions)

@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
