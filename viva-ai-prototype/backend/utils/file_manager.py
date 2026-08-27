import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_ROOT = BASE_DIR / "student_data"
SUPPORTED_EXTENSIONS = (".pdf", ".docx", ".txt")


def safe_folder_name(value):
    value = value.strip().replace(" ", "_")
    value = re.sub(r"[^A-Za-z0-9_.-]", "_", value)
    value = re.sub(r"_+", "_", value).strip("._")
    if not value:
        raise ValueError("Folder name cannot be empty.")
    return value


def ensure_assignment_folder(course_name, student_id, assignment_name, section_name=None):
    course_folder = DATA_ROOT / safe_folder_name(course_name)
    section_folder = course_folder / safe_folder_name(section_name) if section_name else course_folder
    assignment_folder = section_folder / safe_folder_name(assignment_name)
    student_folder = assignment_folder / safe_folder_name(student_id)
    student_folder.mkdir(parents=True, exist_ok=True)
    return course_folder, assignment_folder, student_folder


def assignment_folder_for(course_name, banner_id, assignment_name, section_name=None):
    _, _, student_folder = ensure_assignment_folder(
        course_name, banner_id, assignment_name, section_name
    )
    return student_folder


def find_named_file(folder, stem):
    folder = Path(folder)
    for extension in SUPPORTED_EXTENSIONS:
        candidate = folder / f"{stem}{extension}"
        if candidate.exists():
            return candidate
    return None


def find_assignment_file(folder):
    return find_named_file(folder, "assignment_questions")


def find_submission_file(folder):
    return find_named_file(folder, "student_submission")


def find_model_answer_file(folder):
    return find_named_file(folder, "model_answer")


def extract_text(path):
    path = Path(path)
    extension = path.suffix.lower()
    if extension == ".pdf":
        return extract_pdf_text(path)
    if extension == ".docx":
        return extract_docx_text(path)
    if extension == ".txt":
        return path.read_text(encoding="utf-8", errors="replace")
    raise ValueError(f"Unsupported file type: {extension}")


def extract_pdf_text(path):
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Install pypdf to extract PDF files.") from exc

    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n\n".join(pages).strip()


def extract_docx_text(path):
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError("Install python-docx to extract DOCX files.") from exc

    document = Document(str(path))
    paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
    return "\n".join(paragraphs).strip()
