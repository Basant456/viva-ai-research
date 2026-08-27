import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "viva_ai.db"


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def now_iso():
    return datetime.utcnow().isoformat(timespec="seconds")


def init_db():
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS Course (
                courseID INTEGER PRIMARY KEY AUTOINCREMENT,
                prefix TEXT NOT NULL,
                code TEXT NOT NULL,
                name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS Section (
                secID INTEGER PRIMARY KEY AUTOINCREMENT,
                secNo TEXT NOT NULL,
                courseID INTEGER NOT NULL,
                FOREIGN KEY(courseID) REFERENCES Course(courseID)
            );

            CREATE TABLE IF NOT EXISTS Student (
                stuID INTEGER PRIMARY KEY AUTOINCREMENT,
                bannerID TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS SectionStudent (
                secID INTEGER NOT NULL,
                stuID INTEGER NOT NULL,
                PRIMARY KEY(secID, stuID),
                FOREIGN KEY(secID) REFERENCES Section(secID),
                FOREIGN KEY(stuID) REFERENCES Student(stuID)
            );

            CREATE TABLE IF NOT EXISTS Assignment (
                assignmentID INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                dueDate TEXT,
                points REAL,
                assignmentFile TEXT,
                assignmentOriginalName TEXT,
                rubricFile TEXT,
                modelAnswerFile TEXT,
                courseID INTEGER NOT NULL,
                secID INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY(courseID) REFERENCES Course(courseID),
                FOREIGN KEY(secID) REFERENCES Section(secID)
            );

            CREATE TABLE IF NOT EXISTS Submission (
                submissionID INTEGER PRIMARY KEY AUTOINCREMENT,
                stuID INTEGER NOT NULL,
                assignmentID INTEGER NOT NULL,
                subDate TEXT,
                subFile TEXT,
                submissionOriginalName TEXT,
                AIanalyticFile TEXT,
                AIscore REAL,
                mcqFile TEXT,
                canvasMCQFile TEXT,
                status TEXT NOT NULL DEFAULT 'Not Analyzed',
                folderPath TEXT,
                extractedAssignmentFile TEXT,
                extractedSubmissionFile TEXT,
                created_at TEXT NOT NULL,
                analyzed_at TEXT,
                UNIQUE(stuID, assignmentID),
                FOREIGN KEY(stuID) REFERENCES Student(stuID),
                FOREIGN KEY(assignmentID) REFERENCES Assignment(assignmentID)
            );
            """
        )
        columns = conn.execute("PRAGMA table_info(Student)").fetchall()
        if not any(column["name"] == "studentName" for column in columns):
            conn.execute("ALTER TABLE Student ADD COLUMN studentName TEXT")
        assignment_columns = conn.execute("PRAGMA table_info(Assignment)").fetchall()
        if not any(column["name"] == "assignmentOriginalName" for column in assignment_columns):
            conn.execute("ALTER TABLE Assignment ADD COLUMN assignmentOriginalName TEXT")
        submission_columns = conn.execute("PRAGMA table_info(Submission)").fetchall()
        if not any(column["name"] == "submissionOriginalName" for column in submission_columns):
            conn.execute("ALTER TABLE Submission ADD COLUMN submissionOriginalName TEXT")

        assignments = conn.execute(
            """
            SELECT assignmentID, name, assignmentFile
            FROM Assignment
            WHERE assignmentOriginalName IS NULL
              AND assignmentFile IS NOT NULL
            """
        ).fetchall()
        for assignment in assignments:
            extension = Path(assignment["assignmentFile"]).suffix
            conn.execute(
                """
                UPDATE Assignment
                SET assignmentOriginalName = ?
                WHERE assignmentID = ?
                """,
                (f"{assignment['name']}{extension}", assignment["assignmentID"]),
            )

        submissions = conn.execute(
            """
            SELECT
                Submission.submissionID,
                Submission.subFile,
                Student.bannerID,
                Assignment.name AS assignmentName
            FROM Submission
            JOIN Student ON Student.stuID = Submission.stuID
            JOIN Assignment ON Assignment.assignmentID = Submission.assignmentID
            WHERE Submission.submissionOriginalName IS NULL
              AND Submission.subFile IS NOT NULL
            """
        ).fetchall()
        for submission in submissions:
            extension = Path(submission["subFile"]).suffix
            display_name = f"{submission['bannerID']}_{submission['assignmentName']}{extension}"
            conn.execute(
                """
                UPDATE Submission
                SET submissionOriginalName = ?
                WHERE submissionID = ?
                """,
                (display_name, submission["submissionID"]),
            )


def create_course(prefix, code, name):
    init_db()
    with get_connection() as conn:
        existing = conn.execute(
            """
            SELECT courseID FROM Course
            WHERE lower(prefix) = lower(?)
              AND lower(code) = lower(?)
              AND lower(name) = lower(?)
            """,
            (prefix, code, name),
        ).fetchone()
        if existing:
            return existing["courseID"]

        cursor = conn.execute(
            "INSERT INTO Course (prefix, code, name) VALUES (?, ?, ?)",
            (prefix.strip(), code.strip(), name.strip()),
        )
        return cursor.lastrowid


def create_section(sec_no, course_id):
    init_db()
    with get_connection() as conn:
        existing = conn.execute(
            """
            SELECT secID FROM Section
            WHERE courseID = ? AND lower(secNo) = lower(?)
            """,
            (course_id, sec_no),
        ).fetchone()
        if existing:
            return existing["secID"]

        cursor = conn.execute(
            "INSERT INTO Section (secNo, courseID) VALUES (?, ?)",
            (sec_no.strip(), course_id),
        )
        return cursor.lastrowid


def create_or_get_student(banner_id, student_name=None):
    init_db()
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO Student (bannerID, studentName) VALUES (?, ?)",
            (banner_id, student_name),
        )
        if student_name:
            conn.execute(
                "UPDATE Student SET studentName = ? WHERE bannerID = ?",
                (student_name, banner_id),
            )
        row = conn.execute(
            "SELECT stuID FROM Student WHERE bannerID = ?", (banner_id,)
        ).fetchone()
        return row["stuID"]


def add_student_to_section(sec_id, stu_id):
    init_db()
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO SectionStudent (secID, stuID) VALUES (?, ?)",
            (sec_id, stu_id),
        )


def create_assignment(
    course_id,
    sec_id,
    name,
    description=None,
    due_date=None,
    points=None,
    assignment_file=None,
    rubric_file=None,
    model_answer_file=None,
):
    init_db()
    with get_connection() as conn:
        existing = conn.execute(
            """
            SELECT assignmentID FROM Assignment
            WHERE courseID = ?
              AND COALESCE(secID, 0) = COALESCE(?, 0)
              AND lower(name) = lower(?)
            """,
            (course_id, sec_id, name),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE Assignment
                SET description = COALESCE(?, description),
                    dueDate = COALESCE(?, dueDate),
                    points = COALESCE(?, points)
                WHERE assignmentID = ?
                """,
                (description, due_date, points, existing["assignmentID"]),
            )
            return existing["assignmentID"]

        cursor = conn.execute(
            """
            INSERT INTO Assignment (
                name, description, dueDate, points, assignmentFile, rubricFile,
                modelAnswerFile, courseID, secID, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                description,
                due_date,
                points,
                str(assignment_file) if assignment_file else None,
                str(rubric_file) if rubric_file else None,
                str(model_answer_file) if model_answer_file else None,
                course_id,
                sec_id,
                now_iso(),
            ),
        )
        return cursor.lastrowid


def update_assignment_files(
    assignment_id,
    assignment_file=None,
    rubric_file=None,
    model_answer_file=None,
    assignment_original_name=None,
):
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE Assignment
            SET assignmentFile = COALESCE(?, assignmentFile),
                assignmentOriginalName = COALESCE(?, assignmentOriginalName),
                rubricFile = COALESCE(?, rubricFile),
                modelAnswerFile = COALESCE(?, modelAnswerFile)
            WHERE assignmentID = ?
            """,
            (
                str(assignment_file) if assignment_file else None,
                assignment_original_name,
                str(rubric_file) if rubric_file else None,
                str(model_answer_file) if model_answer_file else None,
                assignment_id,
            ),
        )


def upsert_submission(
    stu_id,
    assignment_id,
    sub_file=None,
    folder_path=None,
    submission_original_name=None,
):
    init_db()
    with get_connection() as conn:
        existing = conn.execute(
            """
            SELECT submissionID FROM Submission
            WHERE stuID = ? AND assignmentID = ?
            """,
            (stu_id, assignment_id),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE Submission
                SET subFile = COALESCE(?, subFile),
                    submissionOriginalName = COALESCE(?, submissionOriginalName),
                    folderPath = COALESCE(?, folderPath),
                    subDate = ?
                WHERE submissionID = ?
                """,
                (
                    str(sub_file) if sub_file else None,
                    submission_original_name,
                    str(folder_path) if folder_path else None,
                    now_iso(),
                    existing["submissionID"],
                ),
            )
            return existing["submissionID"]

        cursor = conn.execute(
            """
            INSERT INTO Submission (
                stuID, assignmentID, subDate, subFile, submissionOriginalName,
                folderPath, status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 'Not Analyzed', ?)
            """,
            (
                stu_id,
                assignment_id,
                now_iso(),
                str(sub_file) if sub_file else None,
                submission_original_name,
                str(folder_path) if folder_path else None,
                now_iso(),
            ),
        )
        return cursor.lastrowid


def update_submission_after_analysis(
    submission_id,
    analysis_path,
    ai_score,
    mcq_path,
    canvas_mcq_path,
    status,
    extracted_assignment_path=None,
    extracted_submission_path=None,
):
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE Submission
            SET AIanalyticFile = ?,
                AIscore = ?,
                mcqFile = ?,
                canvasMCQFile = ?,
                status = ?,
                extractedAssignmentFile = COALESCE(?, extractedAssignmentFile),
                extractedSubmissionFile = COALESCE(?, extractedSubmissionFile),
                analyzed_at = ?
            WHERE submissionID = ?
            """,
            (
                str(analysis_path) if analysis_path else None,
                ai_score,
                str(mcq_path) if mcq_path else None,
                str(canvas_mcq_path) if canvas_mcq_path else None,
                status,
                str(extracted_assignment_path) if extracted_assignment_path else None,
                str(extracted_submission_path) if extracted_submission_path else None,
                now_iso() if status in ("Analyzed", "Needs Verification") else None,
                submission_id,
            ),
        )


def update_canvas_mcq_file(submission_id, canvas_mcq_path):
    init_db()
    with get_connection() as conn:
        conn.execute(
            "UPDATE Submission SET canvasMCQFile = ? WHERE submissionID = ?",
            (str(canvas_mcq_path), submission_id),
        )


def cleanup_deleted_local_files(prune_empty_setup=False):
    init_db()
    with get_connection() as conn:
        submissions = conn.execute("SELECT * FROM Submission").fetchall()
        for submission in submissions:
            folder_path = submission["folderPath"]
            sub_file = submission["subFile"]
            folder_missing = bool(folder_path) and not Path(folder_path).exists()
            submission_missing = bool(sub_file) and not Path(sub_file).exists()
            if folder_missing or submission_missing:
                conn.execute(
                    "DELETE FROM Submission WHERE submissionID = ?",
                    (submission["submissionID"],),
                )

        duplicate_courses = conn.execute(
            """
            SELECT lower(prefix) AS prefix_key, lower(code) AS code_key,
                   lower(name) AS name_key, MIN(courseID) AS keep_id
            FROM Course
            GROUP BY lower(prefix), lower(code), lower(name)
            HAVING COUNT(*) > 1
            """
        ).fetchall()
        for duplicate in duplicate_courses:
            rows = conn.execute(
                """
                SELECT courseID FROM Course
                WHERE lower(prefix) = ?
                  AND lower(code) = ?
                  AND lower(name) = ?
                  AND courseID <> ?
                """,
                (
                    duplicate["prefix_key"],
                    duplicate["code_key"],
                    duplicate["name_key"],
                    duplicate["keep_id"],
                ),
            ).fetchall()
            for row in rows:
                conn.execute(
                    "UPDATE Section SET courseID = ? WHERE courseID = ?",
                    (duplicate["keep_id"], row["courseID"]),
                )
                conn.execute(
                    "UPDATE Assignment SET courseID = ? WHERE courseID = ?",
                    (duplicate["keep_id"], row["courseID"]),
                )
                conn.execute("DELETE FROM Course WHERE courseID = ?", (row["courseID"],))

        duplicate_sections = conn.execute(
            """
            SELECT courseID, lower(secNo) AS sec_key, MIN(secID) AS keep_id
            FROM Section
            GROUP BY courseID, lower(secNo)
            HAVING COUNT(*) > 1
            """
        ).fetchall()
        for duplicate in duplicate_sections:
            rows = conn.execute(
                """
                SELECT secID FROM Section
                WHERE courseID = ? AND lower(secNo) = ? AND secID <> ?
                """,
                (duplicate["courseID"], duplicate["sec_key"], duplicate["keep_id"]),
            ).fetchall()
            for row in rows:
                students = conn.execute(
                    "SELECT stuID FROM SectionStudent WHERE secID = ?",
                    (row["secID"],),
                ).fetchall()
                for student in students:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO SectionStudent (secID, stuID)
                        VALUES (?, ?)
                        """,
                        (duplicate["keep_id"], student["stuID"]),
                    )
                conn.execute(
                    "UPDATE Assignment SET secID = ? WHERE secID = ?",
                    (duplicate["keep_id"], row["secID"]),
                )
                conn.execute("DELETE FROM SectionStudent WHERE secID = ?", (row["secID"],))
                conn.execute("DELETE FROM Section WHERE secID = ?", (row["secID"],))

        if prune_empty_setup:
            pass


def _submission_paths(conn, where_clause, params):
    rows = conn.execute(
        f"""
        SELECT DISTINCT folderPath
        FROM Submission
        {where_clause}
        """,
        params,
    ).fetchall()
    return [row["folderPath"] for row in rows if row["folderPath"]]


def _delete_orphan_students(conn):
    conn.execute(
        """
        DELETE FROM Student
        WHERE stuID NOT IN (SELECT DISTINCT stuID FROM SectionStudent)
          AND stuID NOT IN (SELECT DISTINCT stuID FROM Submission)
        """
    )


def delete_submission_record(submission_id):
    init_db()
    with get_connection() as conn:
        paths = _submission_paths(
            conn,
            "WHERE submissionID = ?",
            (submission_id,),
        )
        conn.execute("DELETE FROM Submission WHERE submissionID = ?", (submission_id,))
        _delete_orphan_students(conn)
        return paths


def delete_assignment_record(assignment_id):
    init_db()
    with get_connection() as conn:
        paths = _submission_paths(
            conn,
            "WHERE assignmentID = ?",
            (assignment_id,),
        )
        conn.execute("DELETE FROM Submission WHERE assignmentID = ?", (assignment_id,))
        conn.execute("DELETE FROM Assignment WHERE assignmentID = ?", (assignment_id,))
        _delete_orphan_students(conn)
        return paths


def rename_assignment_record(assignment_id, new_name):
    init_db()
    new_name = new_name.strip()
    if not new_name:
        raise ValueError("Assignment name cannot be blank.")

    with get_connection() as conn:
        assignment = conn.execute(
            """
            SELECT assignmentID, courseID, secID, name
            FROM Assignment
            WHERE assignmentID = ?
            """,
            (assignment_id,),
        ).fetchone()
        if not assignment:
            raise ValueError("Assignment was not found.")

        duplicate = conn.execute(
            """
            SELECT assignmentID
            FROM Assignment
            WHERE courseID = ?
              AND COALESCE(secID, 0) = COALESCE(?, 0)
              AND lower(name) = lower(?)
              AND assignmentID <> ?
            """,
            (
                assignment["courseID"],
                assignment["secID"],
                new_name,
                assignment_id,
            ),
        ).fetchone()
        if duplicate:
            raise ValueError("That assignment name already exists in this section.")

        conn.execute(
            "UPDATE Assignment SET name = ? WHERE assignmentID = ?",
            (new_name, assignment_id),
        )
        return assignment["name"], new_name


def delete_student_from_section_record(sec_id, stu_id):
    init_db()
    with get_connection() as conn:
        paths = _submission_paths(
            conn,
            """
            WHERE stuID = ?
              AND assignmentID IN (
                  SELECT assignmentID FROM Assignment WHERE secID = ?
              )
            """,
            (stu_id, sec_id),
        )
        conn.execute(
            """
            DELETE FROM Submission
            WHERE stuID = ?
              AND assignmentID IN (
                  SELECT assignmentID FROM Assignment WHERE secID = ?
              )
            """,
            (stu_id, sec_id),
        )
        conn.execute(
            "DELETE FROM SectionStudent WHERE secID = ? AND stuID = ?",
            (sec_id, stu_id),
        )
        _delete_orphan_students(conn)
        return paths


def delete_section_record(sec_id):
    init_db()
    with get_connection() as conn:
        paths = _submission_paths(
            conn,
            """
            WHERE assignmentID IN (
                SELECT assignmentID FROM Assignment WHERE secID = ?
            )
            """,
            (sec_id,),
        )
        conn.execute(
            """
            DELETE FROM Submission
            WHERE assignmentID IN (
                SELECT assignmentID FROM Assignment WHERE secID = ?
            )
            """,
            (sec_id,),
        )
        conn.execute("DELETE FROM Assignment WHERE secID = ?", (sec_id,))
        conn.execute("DELETE FROM SectionStudent WHERE secID = ?", (sec_id,))
        conn.execute("DELETE FROM Section WHERE secID = ?", (sec_id,))
        _delete_orphan_students(conn)
        return paths


def delete_course_record(course_id):
    init_db()
    with get_connection() as conn:
        paths = _submission_paths(
            conn,
            """
            WHERE assignmentID IN (
                SELECT assignmentID FROM Assignment WHERE courseID = ?
            )
            """,
            (course_id,),
        )
        conn.execute(
            """
            DELETE FROM Submission
            WHERE assignmentID IN (
                SELECT assignmentID FROM Assignment WHERE courseID = ?
            )
            """,
            (course_id,),
        )
        conn.execute("DELETE FROM Assignment WHERE courseID = ?", (course_id,))
        conn.execute(
            """
            DELETE FROM SectionStudent
            WHERE secID IN (
                SELECT secID FROM Section WHERE courseID = ?
            )
            """,
            (course_id,),
        )
        conn.execute("DELETE FROM Section WHERE courseID = ?", (course_id,))
        conn.execute("DELETE FROM Course WHERE courseID = ?", (course_id,))
        _delete_orphan_students(conn)
        return paths


def list_courses():
    init_db()
    with get_connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                """
                SELECT
                    Course.*,
                    COUNT(DISTINCT Section.secID) AS section_count,
                    COUNT(DISTINCT SectionStudent.stuID) AS student_count
                FROM Course
                LEFT JOIN Section ON Section.courseID = Course.courseID
                LEFT JOIN SectionStudent ON SectionStudent.secID = Section.secID
                GROUP BY Course.courseID
                ORDER BY Course.prefix, Course.code, Course.name
                """
            ).fetchall()
        ]


def list_sections():
    init_db()
    with get_connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                """
                SELECT Section.*, Course.prefix, Course.code, Course.name AS courseName
                FROM Section
                JOIN Course ON Course.courseID = Section.courseID
                ORDER BY Course.prefix, Course.code, Section.secNo
                """
            ).fetchall()
        ]


def list_students():
    init_db()
    with get_connection() as conn:
        return [
            dict(row)
            for row in conn.execute("SELECT * FROM Student ORDER BY bannerID").fetchall()
        ]


def list_section_students():
    init_db()
    with get_connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                """
                SELECT
                    Student.*,
                    Section.secID,
                    Section.secNo,
                    Course.courseID,
                    Course.prefix,
                    Course.code,
                    Course.name AS courseName
                FROM Student
                JOIN SectionStudent ON SectionStudent.stuID = Student.stuID
                JOIN Section ON Section.secID = SectionStudent.secID
                JOIN Course ON Course.courseID = Section.courseID
                ORDER BY Course.prefix, Course.code, Section.secNo, Student.bannerID
                """
            ).fetchall()
        ]


def list_assignments():
    init_db()
    with get_connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                """
                SELECT
                    Assignment.*,
                    Course.prefix,
                    Course.code,
                    Course.name AS courseName,
                    Section.secNo,
                    COUNT(DISTINCT Submission.submissionID) AS submitted_count,
                    COUNT(DISTINCT SectionStudent.stuID) AS student_count
                FROM Assignment
                JOIN Course ON Course.courseID = Assignment.courseID
                LEFT JOIN Section ON Section.secID = Assignment.secID
                LEFT JOIN SectionStudent ON SectionStudent.secID = Assignment.secID
                LEFT JOIN Submission ON Submission.assignmentID = Assignment.assignmentID
                GROUP BY Assignment.assignmentID
                ORDER BY Assignment.created_at DESC
                """
            ).fetchall()
        ]


def get_course_library():
    init_db()
    with get_connection() as conn:
        courses = [
            dict(row)
            for row in conn.execute(
                """
                SELECT * FROM Course
                ORDER BY prefix, code, name
                """
            ).fetchall()
        ]

        for course in courses:
            sections = [
                dict(row)
                for row in conn.execute(
                    """
                    SELECT * FROM Section
                    WHERE courseID = ?
                    ORDER BY secNo
                    """,
                    (course["courseID"],),
                ).fetchall()
            ]

            for section in sections:
                students = [
                    dict(row)
                    for row in conn.execute(
                        """
                        SELECT Student.*
                        FROM Student
                        JOIN SectionStudent
                          ON SectionStudent.stuID = Student.stuID
                        WHERE SectionStudent.secID = ?
                        ORDER BY Student.bannerID
                        """,
                        (section["secID"],),
                    ).fetchall()
                ]

                assignments = [
                    dict(row)
                    for row in conn.execute(
                        """
                        SELECT *
                        FROM Assignment
                        WHERE courseID = ?
                          AND (secID = ? OR secID IS NULL)
                        ORDER BY name
                        """,
                        (course["courseID"], section["secID"]),
                    ).fetchall()
                ]

                for assignment in assignments:
                    assignment_students = []
                    for student in students:
                        student_row = dict(student)
                        submission = conn.execute(
                            """
                            SELECT
                                Submission.*,
                                Assignment.name AS assignmentName,
                                Assignment.assignmentFile,
                                Assignment.assignmentOriginalName
                            FROM Submission
                            JOIN Assignment
                              ON Assignment.assignmentID = Submission.assignmentID
                            WHERE Submission.stuID = ?
                              AND Submission.assignmentID = ?
                            """,
                            (student["stuID"], assignment["assignmentID"]),
                        ).fetchone()
                        student_row["submission"] = dict(submission) if submission else None
                        assignment_students.append(student_row)
                    assignment["students"] = assignment_students

                for student in students:
                    submissions = [
                        dict(row)
                        for row in conn.execute(
                            """
                            SELECT
                                Submission.*,
                                Assignment.name AS assignmentName,
                                Assignment.assignmentFile,
                                Assignment.assignmentOriginalName
                            FROM Submission
                            JOIN Assignment
                              ON Assignment.assignmentID = Submission.assignmentID
                            WHERE Submission.stuID = ?
                              AND Assignment.courseID = ?
                              AND (Assignment.secID = ? OR Assignment.secID IS NULL)
                            ORDER BY Assignment.name
                            """,
                            (
                                student["stuID"],
                                course["courseID"],
                                section["secID"],
                            ),
                        ).fetchall()
                    ]
                    student["submissions"] = submissions

                section["students"] = students
                section["assignments"] = assignments

            course["sections"] = sections

        return courses


def get_assignment(assignment_id):
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT Assignment.*, Course.prefix, Course.code, Course.name AS courseName,
                   Section.secNo
            FROM Assignment
            JOIN Course ON Course.courseID = Assignment.courseID
            LEFT JOIN Section ON Section.secID = Assignment.secID
            WHERE Assignment.assignmentID = ?
            """,
            (assignment_id,),
        ).fetchone()
        return dict(row) if row else None


def get_submission(submission_id):
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                Submission.*,
                Student.bannerID,
                Student.studentName,
                Assignment.name AS assignmentName,
                Assignment.description,
                Assignment.assignmentFile,
                Assignment.assignmentOriginalName,
                Assignment.modelAnswerFile,
                Course.courseID,
                Course.prefix,
                Course.code,
                Course.name AS courseName,
                Section.secID,
                Section.secNo
            FROM Submission
            JOIN Student ON Student.stuID = Submission.stuID
            JOIN Assignment ON Assignment.assignmentID = Submission.assignmentID
            JOIN Course ON Course.courseID = Assignment.courseID
            LEFT JOIN Section ON Section.secID = Assignment.secID
            WHERE Submission.submissionID = ?
            """,
            (submission_id,),
        ).fetchone()
        return dict(row) if row else None


def get_all_submissions():
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                Submission.*,
                Student.bannerID,
                Student.studentName,
                Assignment.name AS assignmentName,
                Assignment.assignmentOriginalName,
                Course.prefix,
                Course.code,
                Course.name AS courseName,
                Section.secNo
            FROM Submission
            JOIN Student ON Student.stuID = Submission.stuID
            JOIN Assignment ON Assignment.assignmentID = Submission.assignmentID
            JOIN Course ON Course.courseID = Assignment.courseID
            LEFT JOIN Section ON Section.secID = Assignment.secID
            ORDER BY Submission.created_at DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]
