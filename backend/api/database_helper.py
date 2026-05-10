"""
NAV-AI Pro — Full CRUD Data Access Layer
Handles all SQLite persistence for the ERP.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'database', 'students.db')


def get_db_connection():
    """Returns a connection with Row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # Better concurrency for Streamlit
    return conn


def init_db():
    """Initialize all tables from schema.sql."""
    schema_path = os.path.join(os.path.dirname(DB_PATH), 'schema.sql')
    conn = get_db_connection()
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("[OK] Database schema initialized.")


# =====================================================
# STUDENT PROFILE
# =====================================================
def get_or_create_student(name):
    """Get existing student or create a new one."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM students WHERE name = ?", (name,)).fetchone()
    if not row:
        conn.execute("INSERT INTO students (name) VALUES (?)", (name,))
        conn.commit()
        row = conn.execute("SELECT * FROM students WHERE name = ?", (name,)).fetchone()
    conn.close()
    return dict(row)


def update_student_rank(name, rank):
    """Update intelligence rank after AI test."""
    conn = get_db_connection()
    conn.execute("UPDATE students SET intelligence_rank = ? WHERE name = ?", (rank, name))
    conn.commit()
    conn.close()


# =====================================================
# SEMESTER HISTORY (Persistence Upgrade)
# =====================================================
def save_semester_history(student_name, history_dict):
    """
    Save semester SGPA dict like {'Sem 1': 9.2, 'Sem 2': 8.5, ...}
    Uses UPSERT to avoid duplicates.
    """
    conn = get_db_connection()
    for key, sgpa in history_dict.items():
        sem_num = int(key.replace("Sem ", ""))
        conn.execute("""
            INSERT INTO semester_history (student_name, semester, sgpa, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(student_name, semester) 
            DO UPDATE SET sgpa = excluded.sgpa, updated_at = CURRENT_TIMESTAMP
        """, (student_name, sem_num, float(sgpa)))
    conn.commit()
    conn.close()


def load_semester_history(student_name):
    """Load semester history as a dict: {'Sem 1': 9.2, ...}"""
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT semester, sgpa FROM semester_history WHERE student_name = ? ORDER BY semester",
        (student_name,)
    ).fetchall()
    conn.close()
    
    # Default all semesters to 0.0, then overlay DB values
    history = {f"Sem {i}": 0.0 for i in range(1, 9)}
    for row in rows:
        history[f"Sem {row['semester']}"] = row['sgpa']
    return history


# =====================================================
# PREDICTIONS LOG
# =====================================================
def save_prediction(student_name, attendance, mst, study_hours, distraction, predicted):
    """Log a prediction to the database."""
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO predictions (student_name, attendance, mst_marks, study_hours, distraction, predicted_sgpa)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (student_name, attendance, mst, study_hours, distraction, predicted))
    conn.commit()
    conn.close()


def get_prediction_history(student_name, limit=10):
    """Get recent predictions for a student."""
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT * FROM predictions WHERE student_name = ? ORDER BY created_at DESC LIMIT ?
    """, (student_name, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# =====================================================
# ATTENDANCE BURN-DOWN
# =====================================================
def save_attendance(student_name, total, attended):
    """Save or update attendance counts."""
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO attendance_logs (student_name, total_lectures, attended_lectures, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(student_name)
        DO UPDATE SET total_lectures = excluded.total_lectures, 
                      attended_lectures = excluded.attended_lectures,
                      updated_at = CURRENT_TIMESTAMP
    """, (student_name, total, attended))
    conn.commit()
    conn.close()


def load_attendance(student_name):
    """Load saved attendance data."""
    conn = get_db_connection()
    row = conn.execute(
        "SELECT total_lectures, attended_lectures FROM attendance_logs WHERE student_name = ?",
        (student_name,)
    ).fetchone()
    conn.close()
    return dict(row) if row else {"total_lectures": 0, "attended_lectures": 0}


# =====================================================
# AI REPORTS
# =====================================================
def save_ai_report(student_name, subject, weak_topic, content):
    """Save an AI-generated study plan report."""
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO ai_reports (student_name, subject, weak_topic, report_content)
        VALUES (?, ?, ?, ?)
    """, (student_name, subject, weak_topic, content))
    conn.commit()
    conn.close()


def get_latest_report(student_name):
    """Get the most recent AI report."""
    conn = get_db_connection()
    row = conn.execute("""
        SELECT * FROM ai_reports WHERE student_name = ? ORDER BY created_at DESC LIMIT 1
    """, (student_name,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_reports(student_name, limit=20):
    """Get all reports for a student."""
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT * FROM ai_reports WHERE student_name = ? ORDER BY created_at DESC LIMIT ?
    """, (student_name, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# =====================================================
# UNDERSTANDING LEVEL ASSESSMENTS
# =====================================================
def save_assessment(student_name, subject, topic, difficulty, total_q, correct_q,
                    time_taken, comprehension, speed_ratio, understanding_index, tier):
    """Save an understanding assessment result."""
    conn = get_db_connection()
    cursor = conn.execute("""
        INSERT INTO understanding_assessments
        (student_name, subject, topic, difficulty_level, total_questions, correct_answers,
         time_taken_seconds, comprehension_score, speed_ratio, understanding_index, tier)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (student_name, subject, topic, difficulty, total_q, correct_q,
          time_taken, comprehension, speed_ratio, understanding_index, tier))
    assessment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return assessment_id


def save_assessment_questions(assessment_id, questions_data):
    """Save individual question results for an assessment."""
    conn = get_db_connection()
    for q in questions_data:
        conn.execute("""
            INSERT INTO assessment_questions
            (assessment_id, question_text, options, correct_option, selected_option,
             is_correct, difficulty, time_spent_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (assessment_id, q['question'], json.dumps(q['options']),
              q['correct'], q.get('selected', -1),
              1 if q.get('is_correct') else 0,
              q.get('difficulty', 'medium'),
              q.get('time_spent', 0)))
    conn.commit()
    conn.close()


def get_understanding_baseline(student_name, subject):
    """Get the student's personal baseline for a subject."""
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM understanding_baselines WHERE student_name = ? AND subject = ?",
        (student_name, subject)
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"avg_time_per_question": 30.0, "avg_accuracy": 0.5, "total_assessments": 0}


def update_understanding_baseline(student_name, subject, new_avg_time, new_accuracy):
    """Update baseline with running average after each assessment."""
    conn = get_db_connection()
    existing = conn.execute(
        "SELECT * FROM understanding_baselines WHERE student_name = ? AND subject = ?",
        (student_name, subject)
    ).fetchone()

    if existing:
        n = existing['total_assessments']
        # Exponential moving average (gives more weight to recent performance)
        alpha = 0.3  # smoothing factor
        updated_time = existing['avg_time_per_question'] * (1 - alpha) + new_avg_time * alpha
        updated_acc = existing['avg_accuracy'] * (1 - alpha) + new_accuracy * alpha
        conn.execute("""
            UPDATE understanding_baselines
            SET avg_time_per_question = ?, avg_accuracy = ?,
                total_assessments = ?, updated_at = CURRENT_TIMESTAMP
            WHERE student_name = ? AND subject = ?
        """, (updated_time, updated_acc, n + 1, student_name, subject))
    else:
        conn.execute("""
            INSERT INTO understanding_baselines
            (student_name, subject, avg_time_per_question, avg_accuracy, total_assessments)
            VALUES (?, ?, ?, ?, 1)
        """, (student_name, subject, new_avg_time, new_accuracy))

    conn.commit()
    conn.close()


def get_assessment_history(student_name, limit=20):
    """Get recent assessment results for a student."""
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT * FROM understanding_assessments
        WHERE student_name = ? ORDER BY created_at DESC LIMIT ?
    """, (student_name, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_subject_understanding_summary(student_name):
    """Get latest understanding index per subject for the dashboard."""
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT subject, topic, understanding_index, tier, comprehension_score,
               speed_ratio, created_at
        FROM understanding_assessments
        WHERE student_name = ?
        AND id IN (
            SELECT MAX(id) FROM understanding_assessments
            WHERE student_name = ? GROUP BY subject
        )
        ORDER BY subject
    """, (student_name, student_name)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


import json  # needed for json.dumps in save_assessment_questions


if __name__ == "__main__":
    init_db()
    print("[OK] Database Tables Initialized!")