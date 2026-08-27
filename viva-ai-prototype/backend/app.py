import json
import os
import re
import shutil
from pathlib import Path
from urllib import error, request as url_request

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from utils.database import (
    add_student_to_section,
    create_assignment as db_create_assignment,
    create_course as db_create_course,
    create_or_get_student,
    create_section as db_create_section,
    cleanup_deleted_local_files,
    delete_assignment_record,
    delete_course_record,
    delete_section_record,
    delete_student_from_section_record,
    delete_submission_record,
    get_all_submissions,
    get_assignment,
    get_course_library,
    get_submission,
    init_db,
    list_assignments,
    list_courses,
    list_sections,
    list_section_students,
    list_students,
    rename_assignment_record,
    update_assignment_files,
    update_canvas_mcq_file,
    update_submission_after_analysis,
    upsert_submission,
)
from utils.file_manager import DATA_ROOT, assignment_folder_for, extract_text


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

try:
    from dotenv import load_dotenv

    load_dotenv(ENV_PATH, override=True)
except ImportError:
    pass

AI_SCORE_THRESHOLD = float(os.environ.get("AI_SCORE_THRESHOLD", "50"))


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["SESSION_COOKIE_NAME"] = "viva_ai_phase_1_2"


@app.template_filter("basename")
def basename_filter(value):
    return Path(str(value)).name if value else ""

DATA_ROOT.mkdir(parents=True, exist_ok=True)
init_db()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def clean_api_key(key):
    if not key:
        return ""
    key = key.strip().strip('"').strip("'").strip()
    if key.lower().startswith("bearer "):
        key = key[7:].strip()
    return key


def key_is_loaded(key):
    key = clean_api_key(key)
    if not key:
        return False
    lowered = key.lower()
    placeholders = ["your_", "your-real", "your_real", "replace", "paste", "here"]
    return not any(part in lowered for part in placeholders)


def save_uploaded_file(file_storage, folder, preferred_stem):
    if not file_storage or not file_storage.filename:
        return None

    original_name = secure_filename(file_storage.filename)
    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(f"{original_name} is not supported. Upload PDF, DOCX, or TXT.")

    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    target_path = folder / f"{preferred_stem}{extension}"
    file_storage.save(target_path)
    return target_path


def selected_small_ids(**values):
    for key, value in values.items():
        if value:
            session[key] = int(value) if str(value).isdigit() else str(value)


def remove_local_paths(paths):
    data_root = DATA_ROOT.resolve()
    removed = []
    blocked = []
    for raw_path in sorted(set(filter(None, paths)), key=len, reverse=True):
        target = Path(raw_path).resolve()
        if target == data_root or data_root not in target.parents:
            continue
        try:
            if target.is_dir():
                shutil.rmtree(target)
                removed.append(str(target))
            elif target.exists():
                target.unlink()
                removed.append(str(target))
        except PermissionError:
            blocked.append(str(target))
        except OSError:
            blocked.append(str(target))
    return removed, blocked


def flash_delete_result(success_message, paths):
    remove_local_paths(paths)


def find_student_for_assignment(stu_id, assignment):
    for student in list_section_students():
        if student["stuID"] != int(stu_id):
            continue
        if student["courseID"] != assignment["courseID"]:
            continue
        if assignment.get("secID") and student["secID"] != assignment["secID"]:
            continue
        return student
    return None


def dashboard_context():
    cleanup_deleted_local_files()
    return {
        "courses": list_courses(),
        "sections": list_sections(),
        "students": list_students(),
        "section_students": list_section_students(),
        "assignments": list_assignments(),
        "submissions": get_all_submissions(),
        "library": get_course_library(),
        "data_root": DATA_ROOT,
        "db_path": BASE_DIR / "viva_ai.db",
        "threshold": AI_SCORE_THRESHOLD,
        "selected_course_id": session.get("course_id", ""),
        "selected_section_id": session.get("section_id", ""),
        "selected_student_id": session.get("student_id", ""),
        "selected_assignment_id": session.get("assignment_id", ""),
    }


def clean_json_response(content):
    content = content.strip()
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "").strip()
    elif content.startswith("```"):
        content = content.replace("```", "").strip()
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1:
        content = content[start : end + 1]
    return json.loads(content)


def post_json(endpoint, headers, payload, timeout=75):
    req = url_request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with url_request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API error {exc.code}: {detail}") from exc


def score_from_status(status):
    status = (status or "").lower()
    if "needs" in status or "high" in status:
        return 85
    if "review" in status or "medium" in status:
        return 55
    if "low" in status:
        return 20
    return 50


def normalize_llm_result(result):
    if "ai_analysis" in result:
        analysis = result.get("ai_analysis", {})
        mcq = result.get("verification_mcq", {})
        questions = mcq.get("questions", [])
    else:
        analysis = {
            "ai_score": result.get("score"),
            "risk_level": result.get("status", "Review Suggested"),
            "summary": result.get("reason", "Analysis completed."),
            "explanation": result.get("reason", "Analysis completed."),
            "evidence": result.get("evidence", []),
            "concerns": result.get("concerns", []),
            "recommended_follow_up": result.get("recommended_follow_up", []),
            "key_concepts": result.get("key_concepts", []),
        }
        questions = result.get("questions", [])

    analysis.setdefault("risk_level", "Review Suggested")
    analysis.setdefault("summary", "Analysis completed.")
    analysis.setdefault("explanation", analysis.get("summary", "Analysis completed."))
    analysis.setdefault("evidence", [])
    analysis.setdefault("concerns", [])
    analysis.setdefault("recommended_follow_up", [])
    analysis.setdefault("key_concepts", [])
    analysis["ai_score"] = float(
        analysis.get("ai_score") or score_from_status(analysis.get("risk_level"))
    )

    cleaned_questions = []
    for question in questions[:5]:
        options = question.get("options", [])[:4]
        if len(options) == 4:
            cleaned_questions.append(
                {
                    "question": question.get(
                        "question", "Conceptual, scenario-based verification question"
                    ),
                    "options": options,
                    "answer": question.get("answer", options[0]),
                    "concept": question.get("concept")
                    or question.get("explanation")
                    or "Conceptual understanding",
                    "explanation": question.get("explanation")
                    or question.get("concept")
                    or "This checks whether the student understands the related concept.",
                }
            )

    return {"ai_analysis": analysis, "verification_mcq": {"questions": cleaned_questions}}


def local_fallback_analysis(assignment_text, submission_text, model_answer_text=None):
    assignment_terms = set(re.findall(r"\b[a-zA-Z]{5,}\b", assignment_text.lower()))
    submission_terms = set(re.findall(r"\b[a-zA-Z]{5,}\b", submission_text.lower()))
    overlap = len(assignment_terms & submission_terms)
    word_count = len(submission_text.split())
    ai_score = 72 if word_count > 500 and overlap < 10 else 28
    risk = "Needs Verification" if ai_score > AI_SCORE_THRESHOLD else "Low Risk"
    model_note = " Model answer file was saved for future use." if model_answer_text else ""

    return normalize_llm_result(
        {
            "ai_analysis": {
                "ai_score": ai_score,
                "risk_level": risk,
                "summary": "No API key was available, so VIVA-AI used a local heuristic review.",
                "explanation": (
                    "The fallback compares submission length and key-term overlap only."
                    f"{model_note}"
                ),
                "evidence": [
                    f"Assignment text length: {len(assignment_text.split())} words.",
                    f"Submission text length: {word_count} words.",
                f"Shared key-term count: {overlap}.",
                ],
                "concerns": [
                    "Configure OPENROUTER_API_KEY for full AI-risk analysis."
                ],
                "recommended_follow_up": [
                    "Ask the student to explain the main design choices in their own words."
                ],
            },
            "verification_mcq": {
                "questions": [
                    {
                        "question": "Which explanation best shows genuine understanding of the submitted work?",
                        "options": [
                            "Describing why key choices were made",
                            "Repeating the first paragraph exactly",
                            "Listing unrelated definitions",
                            "Avoiding technical details",
                        ],
                        "answer": "Describing why key choices were made",
                        "concept": "Conceptual ownership",
                        "explanation": "The student should be able to explain the reasoning behind the submitted work.",
                    },
                    {
                        "question": "What should a student be able to do during a verification interview?",
                        "options": [
                            "Explain how their solution addresses the prompt",
                            "Claim the file is complete without discussion",
                            "Recite only the assignment title",
                            "Discuss a different assignment",
                        ],
                        "answer": "Explain how their solution addresses the prompt",
                        "concept": "Assignment alignment",
                        "explanation": "The answer should connect the submitted work back to the assignment requirements.",
                    },
                    {
                        "question": "What is the strongest evidence that a submission reflects student understanding?",
                        "options": [
                            "The student can modify or extend the idea live",
                            "The formatting looks polished",
                            "The response is very long",
                            "The vocabulary is complex",
                        ],
                        "answer": "The student can modify or extend the idea live",
                        "concept": "Applied understanding",
                        "explanation": "Being able to adapt the idea is stronger evidence of understanding than polished wording alone.",
                    },
                ]
            },
        }
    )


def detect_ai_like_signals(submission_text):
    text = submission_text.strip()
    lower = text.lower()
    words = re.findall(r"\b[a-zA-Z']+\b", text)
    sentences = [part.strip() for part in re.split(r"[.!?]+", text) if part.strip()]
    signals = []

    generic_phrases = [
        "demonstrates a clear understanding",
        "effectively addresses",
        "well-structured",
        "comprehensive",
        "in conclusion",
        "overall",
        "it is important to note",
        "plays a crucial role",
        "designed to",
        "ensures that",
        "allows the program to",
        "manage any invalid",
    ]
    phrase_hits = [phrase for phrase in generic_phrases if phrase in lower]
    if len(phrase_hits) >= 2:
        signals.append(
            "The submission uses multiple polished, generic explanatory phrases often seen in AI-generated summaries."
        )

    first_person_markers = [" i ", " my ", " me ", " we ", " our "]
    if len(words) >= 120 and not any(marker in f" {lower} " for marker in first_person_markers):
        signals.append(
            "The submission gives a polished explanation without personal examples, original comparisons, or first-person ownership."
        )

    if sentences:
        avg_sentence_length = len(words) / len(sentences)
        if avg_sentence_length >= 22 and len(words) >= 140:
            signals.append(
                "The writing has long, smooth explanatory sentences with little variation or informal student-specific detail."
            )

    if len(words) >= 100 and not re.search(r"\b(for example|my example|i think|i understand|in my words|i would)\b", lower):
        signals.append(
            "The submission gives few personal examples or student-specific explanations of the concepts."
        )

    if re.search(r"\bfunctionality\b", lower) and re.search(r"\berror handling\b", lower) and re.search(r"\bfile operations?\b", lower):
        signals.append(
            "The explanation reads like a broad answer-key summary of the expected concepts."
        )

    return signals


def calibrate_ai_risk(llm_result, assignment_text, submission_text):
    analysis = llm_result["ai_analysis"]
    signals = detect_ai_like_signals(submission_text)
    if not signals:
        return llm_result

    evidence = analysis.setdefault("evidence", [])
    concerns = analysis.setdefault("concerns", [])
    follow_up = analysis.setdefault("recommended_follow_up", [])

    for signal in signals:
        if signal not in evidence:
            evidence.append(signal)

    concern = (
        "The submission may be conceptually correct but still needs verification because it appears polished, generic, "
        "or answer-key-like rather than clearly student-owned."
    )
    if concern not in concerns:
        concerns.append(concern)

    follow = "Ask the student to explain the main concepts in their own words and give an original example for each major comparison."
    if follow not in follow_up:
        follow_up.append(follow)

    current_score = float(analysis.get("ai_score") or 0)
    if len(signals) >= 2 and current_score <= AI_SCORE_THRESHOLD:
        analysis["ai_score"] = max(current_score, AI_SCORE_THRESHOLD + 8)
        analysis["risk_level"] = "Needs Verification"
        analysis["summary"] = "The submission is technically aligned with the assignment, but its polished and generic presentation requires conceptual verification."
        analysis["explanation"] = (
            "Correctness alone is not treated as proof of authentic authorship. "
            "The submission contains signals that warrant follow-up MCQs and student explanation."
        )
    elif current_score <= 35:
        analysis["ai_score"] = max(current_score, 42)
        analysis["risk_level"] = "Review Suggested"

    return llm_result


def build_prompt(assignment_text, submission_text, model_answer_text=None, force_mcq=False):
    model_answer_section = (
        f"\nOptional Model Answer For Future Reference:\n{model_answer_text[:12000]}\n"
        if model_answer_text
        else ""
    )
    return f"""
You are an educational assessment assistant specialized in academic verification and conceptual understanding evaluation.

Analyze the student's submission using the assignment questions as context.
Do not accuse the student of AI use. Identify whether conceptual verification is needed.
The score is an AI-use concern score, not a correctness score.
A correct, detailed, or well-written submission can still require verification if it appears generic, overly polished,
answer-key-like, detached from a student's own explanation, or lacks original examples and reasoning.
Do not assign Low Risk simply because the content is accurate or aligned with the assignment.

Use this scoring guide:
- 0 to 30: Low Risk only when the submission includes clear student-specific ownership, original examples,
  natural explanation, or reasoning that shows how the student understands the concepts.
- 31 to 50: Review Suggested when the submission is correct or aligned with the assignment but mostly polished,
  generic, answer-key-like, or missing concrete evidence of student ownership.
- Above 50: Needs Verification when authenticity concerns are strong enough to require conceptual MCQs.

Important scoring rule:
- Do not use correctness, completeness, detailed wording, or assignment alignment as the main reason for Low Risk.
- If the evidence mainly says the answer is accurate, detailed, or well aligned, but there is little personal process
  or student-specific ownership, assign Review Suggested or Needs Verification.
- Low Risk requires positive evidence of authentic student ownership, not just absence of proof of AI use.
- If Review Suggested or Needs Verification, include at least one concern and one recommended follow-up.

Look for authenticity signals such as:
- generic polished textbook wording,
- broad summaries that mirror the assignment prompt,
- lack of personal examples, original comparisons, reasoning, or student-specific explanation,
- suspiciously complete explanations without natural student variation,
- mismatch between submitted artifact and explanation,
- minimal evidence that the student can explain the work independently.

When generating verification MCQs:
- Questions must test conceptual understanding, not memorization.
- Avoid generic textbook-definition questions.
- Avoid questions that can be answered by copying one sentence from the submission.
- Questions must be based on the student's submitted content and assignment context.
- Use scenario-based reasoning where possible.
- Each question must include exactly 4 answer choices.
- Only one answer choice should be correct.
- Include the correct answer.
- Include a short explanation of why the correct answer is correct.
- Include the concept being tested.
- Do not accuse the student of AI use.
- Return only valid JSON.

Return ONLY valid JSON in this format:
{{
  "ai_analysis": {{
    "ai_score": 0,
    "risk_level": "Low Risk | Review Suggested | Needs Verification",
    "summary": "Brief instructor-facing summary",
    "explanation": "Why this score was assigned",
    "evidence": ["specific observations"],
    "concerns": ["possible authenticity concerns"],
    "recommended_follow_up": ["practical next steps"],
    "key_concepts": ["Concept 1", "Concept 2"]
  }},
  "verification_mcq": {{
    "questions": [
      {{
        "question": "Conceptual, scenario-based verification question",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "answer": "Correct option text",
        "concept": "Concept being verified",
        "explanation": "Brief explanation of why the correct answer is correct"
      }}
    ]
  }}
}}

{"Generate 3 to 5 conceptual MCQs because the instructor explicitly requested them." if force_mcq else "If risk_level is Review Suggested or Needs Verification, generate 3 to 5 conceptual MCQs automatically. If risk_level is Low Risk, return an empty questions array unless the instructor explicitly requested MCQs."}

Assignment Questions:
{assignment_text[:20000]}

Student Submission:
{submission_text[:30000]}
{model_answer_section}
"""


def call_llm_for_analysis(assignment_text, submission_text, model_answer_text=None, force_mcq=False):
    if not assignment_text.strip():
        raise ValueError("No readable assignment questions text was found.")
    if not submission_text.strip():
        raise ValueError("No readable student submission text was found.")

    prompt = build_prompt(assignment_text, submission_text, model_answer_text, force_mcq)

    try:
        api_key = clean_api_key(OPENROUTER_API_KEY)
        if not key_is_loaded(api_key):
            raise ValueError("Missing or placeholder OPENROUTER_API_KEY")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://127.0.0.1:5000",
            "X-OpenRouter-Title": "VIVA-AI",
        }
        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": "Return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 2500,
        }
        body = post_json(OPENROUTER_URL, headers, payload)

        content = body["choices"][0]["message"]["content"]
        result = normalize_llm_result(clean_json_response(content))
        if force_mcq and not result["verification_mcq"]["questions"]:
            fallback = local_fallback_analysis(assignment_text, submission_text, model_answer_text)
            result["verification_mcq"] = fallback["verification_mcq"]
        return calibrate_ai_risk(result, assignment_text, submission_text)
    except Exception:
        fallback = local_fallback_analysis(assignment_text, submission_text, model_answer_text)
        return calibrate_ai_risk(fallback, assignment_text, submission_text)


def review_category(submission_or_analysis):
    if not submission_or_analysis:
        return "Not Analyzed"
    risk = submission_or_analysis.get("risk_level") or submission_or_analysis.get("status")
    if risk:
        return risk
    score = submission_or_analysis.get("AIscore") or submission_or_analysis.get("ai_score")
    if score is None:
        return "Not Analyzed"
    return "Needs Verification" if float(score) > AI_SCORE_THRESHOLD else "Analyzed"


def analysis_requires_mcq(analysis):
    risk = (analysis.get("risk_level") or "").lower()
    if risk:
        return "low risk" not in risk
    score = analysis.get("ai_score")
    return score is not None and float(score) > 30


def build_canvas_mcq(mcq, submission):
    questions = []
    for index, question in enumerate(mcq.get("questions", []), start=1):
        answers = [
            {
                "answer_text": option,
                "answer_weight": 100 if option == question.get("answer") else 0,
            }
            for option in question.get("options", [])
        ]
        questions.append(
            {
                "question_name": f"Verification Question {index}",
                "question_type": "multiple_choice_question",
                "question_text": question.get("question"),
                "points_possible": 1,
                "answers": answers,
                "concept": question.get("concept"),
                "explanation": question.get("explanation") or question.get("concept"),
            }
        )

    return {
        "canvas_placeholder": True,
        "course": f"{submission['prefix']} {submission['code']} - {submission['courseName']}",
        "assignment": submission["assignmentName"],
        "student_banner_id": submission["bannerID"],
        "quiz_title": f"VIVA-AI Verification - {submission['assignmentName']}",
        "questions": questions,
    }


def read_json_file(path, default):
    if path and Path(path).exists():
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return default


@app.after_request
def prevent_cached_pages(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", **dashboard_context())


@app.route("/phase_status", methods=["GET"])
def phase_status():
    return {
        "app": "VIVA-AI",
        "implemented": ["Phase 1 AI Processing", "Phase 2 Local Dashboard"],
        "canvas_api": "placeholder only",
        "storage_root": str(DATA_ROOT),
    }


@app.route("/create_course", methods=["POST"])
def create_course():
    prefix = request.form.get("prefix", "").strip()
    code = request.form.get("code", "").strip()
    name = request.form.get("name", "").strip()
    if not prefix or not code or not name:
        flash("Course prefix, code, and name are required.")
        return redirect(url_for("index"))

    course_id = db_create_course(prefix, code, name)
    selected_small_ids(course_id=course_id)
    flash("Course saved.")
    return redirect(url_for("index"))


@app.route("/create_section", methods=["POST"])
def create_section():
    course_id = request.form.get("course_id", "").strip()
    sec_no = request.form.get("sec_no", "").strip()
    if not course_id or not sec_no:
        flash("Choose a course and enter a section number.")
        return redirect(url_for("index"))

    sec_id = db_create_section(sec_no, int(course_id))
    selected_small_ids(course_id=course_id, section_id=sec_id)
    flash("Section saved.")
    return redirect(url_for("index"))


@app.route("/add_student", methods=["POST"])
def add_student():
    sec_id = request.form.get("sec_id", "").strip()
    banner_id = request.form.get("banner_id", "").strip()
    student_name = request.form.get("student_name", "").strip()
    if not sec_id or not banner_id:
        flash("Choose a section and enter a Banner ID.")
        return redirect(url_for("index"))

    stu_id = create_or_get_student(banner_id, student_name)
    add_student_to_section(int(sec_id), stu_id)
    matching_section = next(
        (section for section in list_sections() if section["secID"] == int(sec_id)),
        None,
    )
    selected_small_ids(
        course_id=matching_section["courseID"] if matching_section else None,
        section_id=sec_id,
        student_id=stu_id,
    )
    flash("Student added to section.")
    return redirect(url_for("index"))


@app.route("/create_assignment", methods=["POST"])
def create_assignment():
    course_id = request.form.get("course_id", "").strip()
    sec_id = request.form.get("sec_id", "").strip() or None
    stu_id = request.form.get("stu_id", "").strip()
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    if not course_id or not name:
        flash("Choose a course and enter an assignment name.")
        return redirect(url_for("index"))

    assignment_id = db_create_assignment(
        course_id=int(course_id),
        sec_id=int(sec_id) if sec_id else None,
        name=name,
        description=description,
    )
    selected_small_ids(course_id=course_id, section_id=sec_id, assignment_id=assignment_id)

    assignment_file_storage = request.files.get("assignment_file")
    submission_file_storage = request.files.get("submission_file")
    if stu_id or (assignment_file_storage and assignment_file_storage.filename) or (submission_file_storage and submission_file_storage.filename):
        if not stu_id:
            flash("Choose a student before saving assignment files.")
            return redirect(url_for("index"))
        if not assignment_file_storage or not assignment_file_storage.filename:
            flash("Assignment questions file is required when saving student work.")
            return redirect(url_for("index"))
        if not submission_file_storage or not submission_file_storage.filename:
            flash("Student submission file is required when saving student work.")
            return redirect(url_for("index"))

        assignment = get_assignment(assignment_id)
        matching_student = find_student_for_assignment(stu_id, assignment)
        if not assignment or not matching_student:
            flash("Assignment or student was not found.")
            return redirect(url_for("index"))

        if assignment.get("secID"):
            add_student_to_section(assignment["secID"], int(stu_id))

        course_label = f"{assignment['prefix']}_{assignment['code']}_{assignment['courseName']}"
        student_label = matching_student["bannerID"]
        if matching_student.get("studentName"):
            student_label = f"{matching_student['bannerID']}_{matching_student['studentName']}"
        section_label = f"Section_{assignment['secNo']}" if assignment.get("secNo") else None
        folder = assignment_folder_for(course_label, student_label, assignment["name"], section_label)

        try:
            assignment_original_name = secure_filename(assignment_file_storage.filename)
            submission_original_name = secure_filename(submission_file_storage.filename)
            assignment_file = save_uploaded_file(
                assignment_file_storage, folder, "assignment_questions"
            )
            submission_file = save_uploaded_file(
                submission_file_storage, folder, "student_submission"
            )
        except ValueError as exc:
            flash(str(exc))
            return redirect(url_for("index"))

        update_assignment_files(
            int(assignment_id),
            assignment_file=assignment_file,
            assignment_original_name=assignment_original_name,
        )
        upsert_submission(
            int(stu_id),
            int(assignment_id),
            submission_file,
            folder,
            submission_original_name=submission_original_name,
        )
        flash("Assignment and student files saved.")
        return redirect(url_for("index"))

    flash("Assignment saved.")
    return redirect(url_for("index"))


@app.route("/upload_submission", methods=["POST"])
def upload_submission():
    assignment_id = request.form.get("assignment_id", "").strip()
    stu_id = request.form.get("stu_id", "").strip()
    if not assignment_id or not stu_id:
        flash("Choose an assignment and student.")
        return redirect(url_for("index"))

    assignment = get_assignment(int(assignment_id))
    if not assignment:
        flash("Assignment was not found.")
        return redirect(url_for("index"))

    matching_student = find_student_for_assignment(stu_id, assignment)
    if not matching_student:
        flash("Student was not found in the selected section.")
        return redirect(url_for("index"))

    if assignment.get("secID"):
        add_student_to_section(assignment["secID"], int(stu_id))

    course_label = f"{assignment['prefix']}_{assignment['code']}_{assignment['courseName']}"
    student_label = matching_student["bannerID"]
    if matching_student.get("studentName"):
        student_label = f"{matching_student['bannerID']}_{matching_student['studentName']}"
    section_label = f"Section_{assignment['secNo']}" if assignment.get("secNo") else None
    folder = assignment_folder_for(course_label, student_label, assignment["name"], section_label)

    try:
        assignment_storage = request.files.get("assignment_file")
        submission_storage = request.files.get("submission_file")
        assignment_original_name = (
            secure_filename(assignment_storage.filename)
            if assignment_storage and assignment_storage.filename
            else None
        )
        submission_original_name = (
            secure_filename(submission_storage.filename)
            if submission_storage and submission_storage.filename
            else None
        )
        assignment_file = save_uploaded_file(
            assignment_storage, folder, "assignment_questions"
        )
        submission_file = save_uploaded_file(
            submission_storage, folder, "student_submission"
        )
    except ValueError as exc:
        flash(str(exc))
        return redirect(url_for("index"))

    update_assignment_files(
        int(assignment_id),
        assignment_file=assignment_file,
        assignment_original_name=assignment_original_name,
    )
    submission_id = upsert_submission(
        int(stu_id),
        int(assignment_id),
        submission_file,
        folder,
        submission_original_name=submission_original_name,
    )
    selected_small_ids(assignment_id=assignment_id)
    session["last_submission_id"] = submission_id
    flash("Submission uploaded locally.")
    return redirect(url_for("index"))


@app.route("/analyze_submission/<int:submission_id>", methods=["POST"])
def analyze_submission(submission_id):
    submission = get_submission(submission_id)
    if not submission:
        flash("Submission record was not found.")
        return redirect(url_for("index"))

    assignment_path = submission.get("assignmentFile")
    submission_path = submission.get("subFile")
    model_answer_path = submission.get("modelAnswerFile")
    folder = Path(submission.get("folderPath") or DATA_ROOT)

    if not assignment_path or not Path(assignment_path).exists():
        flash("Assignment questions file is required before analysis.")
        return redirect(url_for("index"))
    if not submission_path or not Path(submission_path).exists():
        flash("Student submission file is required before analysis.")
        return redirect(url_for("index"))

    try:
        assignment_text = extract_text(assignment_path)
        submission_text = extract_text(submission_path)
        model_answer_text = (
            extract_text(model_answer_path)
            if model_answer_path and Path(model_answer_path).exists()
            else None
        )

        extracted_assignment_path = folder / "extracted_assignment_questions.txt"
        extracted_submission_path = folder / "extracted_student_submission.txt"
        extracted_assignment_path.write_text(assignment_text, encoding="utf-8")
        extracted_submission_path.write_text(submission_text, encoding="utf-8")

        llm_result = call_llm_for_analysis(
            assignment_text, submission_text, model_answer_text
        )
        ai_score = llm_result["ai_analysis"]["ai_score"]
        needs_mcq = analysis_requires_mcq(llm_result["ai_analysis"])
        if not needs_mcq:
            llm_result["verification_mcq"] = {"questions": []}
        elif not llm_result["verification_mcq"].get("questions"):
            fallback = local_fallback_analysis(
                assignment_text, submission_text, model_answer_text
            )
            llm_result["verification_mcq"] = fallback["verification_mcq"]

        analysis_path = folder / "ai_analysis.json"
        mcq_path = folder / "verification_mcq.json"
        canvas_mcq_path = folder / "canvas_mcq_file.json"
        analysis_path.write_text(
            json.dumps(llm_result["ai_analysis"], indent=2), encoding="utf-8"
        )
        mcq_path.write_text(
            json.dumps(llm_result["verification_mcq"], indent=2), encoding="utf-8"
        )
        canvas_mcq_path.write_text(
            json.dumps(build_canvas_mcq(llm_result["verification_mcq"], submission), indent=2),
            encoding="utf-8",
        )

        update_submission_after_analysis(
            submission_id=submission_id,
            analysis_path=analysis_path,
            ai_score=ai_score,
            mcq_path=mcq_path,
            canvas_mcq_path=canvas_mcq_path,
            status=llm_result["ai_analysis"].get("risk_level")
            or ("Needs Verification" if needs_mcq else "Analyzed"),
            extracted_assignment_path=extracted_assignment_path,
            extracted_submission_path=extracted_submission_path,
        )
    except Exception as exc:
        update_submission_after_analysis(
            submission_id=submission_id,
            analysis_path=None,
            ai_score=None,
            mcq_path=None,
            canvas_mcq_path=None,
            status="Not Analyzed",
        )
        flash(f"Analysis failed: {exc}")
        return redirect(url_for("index"))

    return redirect(url_for("review", submission_id=submission_id))


@app.route("/review/<int:submission_id>", methods=["GET"])
def review(submission_id):
    submission = get_submission(submission_id)
    if not submission:
        flash("Submission record was not found.")
        return redirect(url_for("index"))

    analysis = read_json_file(submission.get("AIanalyticFile"), {})
    mcq = read_json_file(submission.get("mcqFile"), {"questions": []})
    return render_template(
        "review.html",
        submission=submission,
        analysis=analysis,
        mcq=mcq,
        review_status=review_category(analysis) if analysis else submission.get("status"),
    )


@app.route("/generate_mcq/<int:submission_id>", methods=["POST"])
def generate_mcq(submission_id):
    submission = get_submission(submission_id)
    if not submission:
        flash("Submission record was not found.")
        return redirect(url_for("index"))

    assignment_path = submission.get("assignmentFile")
    submission_path = submission.get("subFile")
    model_answer_path = submission.get("modelAnswerFile")
    folder = Path(submission.get("folderPath") or DATA_ROOT)

    if not assignment_path or not Path(assignment_path).exists():
        flash("Assignment questions file is required before MCQs can be generated.")
        return redirect(url_for("review", submission_id=submission_id))
    if not submission_path or not Path(submission_path).exists():
        flash("Student submission file is required before MCQs can be generated.")
        return redirect(url_for("review", submission_id=submission_id))

    try:
        assignment_text = extract_text(assignment_path)
        submission_text = extract_text(submission_path)
        model_answer_text = (
            extract_text(model_answer_path)
            if model_answer_path and Path(model_answer_path).exists()
            else None
        )

        folder.mkdir(parents=True, exist_ok=True)
        extracted_assignment_path = folder / "extracted_assignment_questions.txt"
        extracted_submission_path = folder / "extracted_student_submission.txt"
        extracted_assignment_path.write_text(assignment_text, encoding="utf-8")
        extracted_submission_path.write_text(submission_text, encoding="utf-8")

        llm_result = call_llm_for_analysis(
            assignment_text, submission_text, model_answer_text, force_mcq=True
        )
        existing_analysis = read_json_file(submission.get("AIanalyticFile"), {})
        analysis = existing_analysis or llm_result["ai_analysis"]

        analysis_path = Path(submission.get("AIanalyticFile") or folder / "ai_analysis.json")
        mcq_path = folder / "verification_mcq.json"
        canvas_mcq_path = folder / "canvas_mcq_file.json"
        analysis_path.write_text(json.dumps(analysis, indent=2), encoding="utf-8")
        mcq_path.write_text(
            json.dumps(llm_result["verification_mcq"], indent=2), encoding="utf-8"
        )
        canvas_mcq_path.write_text(
            json.dumps(build_canvas_mcq(llm_result["verification_mcq"], submission), indent=2),
            encoding="utf-8",
        )

        update_submission_after_analysis(
            submission_id=submission_id,
            analysis_path=analysis_path,
            ai_score=submission.get("AIscore") or analysis.get("ai_score"),
            mcq_path=mcq_path,
            canvas_mcq_path=canvas_mcq_path,
            status=submission.get("status") or "Analyzed",
            extracted_assignment_path=extracted_assignment_path,
            extracted_submission_path=extracted_submission_path,
        )
    except Exception as exc:
        flash(f"MCQ generation failed: {exc}")
        return redirect(url_for("review", submission_id=submission_id))

    return redirect(url_for("quiz", submission_id=submission_id))


@app.route("/quiz/<int:submission_id>", methods=["GET"])
def quiz(submission_id):
    submission = get_submission(submission_id)
    if not submission:
        flash("Submission record was not found.")
        return redirect(url_for("index"))

    mcq = read_json_file(submission.get("mcqFile"), {"questions": []})
    return render_template("quiz.html", submission=submission, mcq=mcq)


@app.route("/student_quiz/<int:submission_id>", methods=["GET", "POST"])
def student_quiz(submission_id):
    submission = get_submission(submission_id)
    if not submission:
        flash("Submission record was not found.")
        return redirect(url_for("index"))

    mcq = read_json_file(submission.get("mcqFile"), {"questions": []})
    if request.method == "POST":
        responses = []
        for index, question in enumerate(mcq.get("questions", [])):
            selected = request.form.get(f"question_{index}", "")
            answer = question.get("answer", "")
            responses.append(
                {
                    "question": question.get("question"),
                    "selected": selected,
                    "answer": answer,
                    "is_correct": selected == answer,
                    "concept": question.get("concept", ""),
                    "explanation": question.get("explanation")
                    or question.get("concept")
                    or "No explanation was saved for this question.",
                }
            )
        return render_template(
            "student_quiz_submitted.html",
            submission=submission,
            responses=responses,
        )

    return render_template("student_quiz.html", submission=submission, mcq=mcq)


@app.route("/download_canvas_mcq/<int:submission_id>", methods=["GET"])
def download_canvas_mcq(submission_id):
    submission = get_submission(submission_id)
    if not submission:
        flash("Submission record was not found.")
        return redirect(url_for("index"))

    canvas_path = submission.get("canvasMCQFile")
    if not canvas_path or not Path(canvas_path).exists():
        mcq = read_json_file(submission.get("mcqFile"), {"questions": []})
        folder = Path(submission.get("folderPath") or DATA_ROOT)
        folder.mkdir(parents=True, exist_ok=True)
        canvas_path = folder / "canvas_mcq_file.json"
        canvas_path.write_text(
            json.dumps(build_canvas_mcq(mcq, submission), indent=2), encoding="utf-8"
        )
        update_canvas_mcq_file(submission_id, canvas_path)

    return send_file(canvas_path, as_attachment=True, download_name="canvas_mcq_file.json")


@app.route("/download_saved_file/<int:submission_id>/<file_kind>", methods=["GET"])
def download_saved_file(submission_id, file_kind):
    submission = get_submission(submission_id)
    if not submission:
        flash("Submission record was not found.")
        return redirect(url_for("index"))

    if file_kind == "assignment":
        file_path = submission.get("assignmentFile")
        download_name = (
            submission.get("assignmentOriginalName")
            or (Path(file_path).name if file_path else "assignment_questions")
        )
    elif file_kind == "submission":
        file_path = submission.get("subFile")
        download_name = (
            submission.get("submissionOriginalName")
            or (Path(file_path).name if file_path else "student_submission")
        )
    else:
        flash("Requested file type was not found.")
        return redirect(url_for("index"))

    if not file_path or not Path(file_path).exists():
        flash("The saved file was not found.")
        return redirect(url_for("index"))

    return send_file(file_path, as_attachment=True, download_name=download_name)


@app.route("/retrieve_from_canvas", methods=["POST"])
def retrieve_from_canvas():
    flash("Canvas retrieval placeholder only. Real Canvas API integration is Phase 3.")
    return redirect(url_for("index"))


@app.route("/sync_local_files", methods=["POST"])
def sync_local_files():
    cleanup_deleted_local_files(prune_empty_setup=True)
    flash("Dashboard records synced with local files. Student names and section rosters were kept.")
    return redirect(url_for("index"))


@app.route("/delete_submission/<int:submission_id>", methods=["POST"])
def delete_submission(submission_id):
    paths = delete_submission_record(submission_id)
    flash_delete_result("Submission removed from the dashboard and local storage.", paths)
    return redirect(url_for("index"))


@app.route("/delete_assignment/<int:assignment_id>", methods=["POST"])
def delete_assignment(assignment_id):
    paths = delete_assignment_record(assignment_id)
    flash_delete_result("Assignment removed from the dashboard and local storage.", paths)
    return redirect(url_for("index"))


@app.route("/rename_assignment/<int:assignment_id>", methods=["POST"])
def rename_assignment(assignment_id):
    new_name = request.form.get("new_name", "").strip()
    try:
        old_name, saved_name = rename_assignment_record(assignment_id, new_name)
    except ValueError as exc:
        flash(str(exc))
        return redirect(url_for("index"))

    selected_small_ids(assignment_id=assignment_id)
    flash(f"Assignment renamed from {old_name} to {saved_name}.")
    return redirect(url_for("index"))


@app.route("/delete_student/<int:sec_id>/<int:stu_id>", methods=["POST"])
def delete_student(sec_id, stu_id):
    paths = delete_student_from_section_record(sec_id, stu_id)
    flash_delete_result(
        "Student removed from this section. Their saved submissions for this section were removed.",
        paths,
    )
    return redirect(url_for("index"))


@app.route("/delete_section/<int:sec_id>", methods=["POST"])
def delete_section(sec_id):
    paths = delete_section_record(sec_id)
    flash_delete_result("Section removed from the dashboard and local storage.", paths)
    return redirect(url_for("index"))


@app.route("/delete_subject/<int:course_id>", methods=["POST"])
def delete_subject(course_id):
    paths = delete_course_record(course_id)
    flash_delete_result("Subject removed from the dashboard and local storage.", paths)
    return redirect(url_for("index"))


@app.route("/send_quiz_to_canvas/<int:submission_id>", methods=["POST"])
def send_quiz_to_canvas(submission_id):
    return redirect(url_for("quiz", submission_id=submission_id))


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)

