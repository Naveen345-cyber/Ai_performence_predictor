-- =====================================================
-- NAV-AI Pro — Complete Database Schema (Phase 2)
-- =====================================================

-- Core student profile
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    attendance REAL DEFAULT 0,
    study_hours REAL DEFAULT 0,
    sleep_hours REAL DEFAULT 0,
    dsa_solved INTEGER DEFAULT 0,
    current_cgpa REAL DEFAULT 0,
    intelligence_rank TEXT DEFAULT 'Unranked',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Semester-wise SGPA history (persists across refreshes)
CREATE TABLE IF NOT EXISTS semester_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL,
    semester INTEGER NOT NULL CHECK(semester BETWEEN 1 AND 8),
    sgpa REAL DEFAULT 0.0 CHECK(sgpa BETWEEN 0.0 AND 10.0),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_name, semester)
);

-- Prediction logs for the forecaster
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL,
    attendance REAL,
    mst_marks REAL,
    study_hours REAL,
    distraction TEXT,
    predicted_sgpa REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Attendance tracking for burn-down calculator
CREATE TABLE IF NOT EXISTS attendance_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL,
    total_lectures INTEGER DEFAULT 0,
    attended_lectures INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_name)
);

-- AI-generated reports (for PDF export recall)
CREATE TABLE IF NOT EXISTS ai_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL,
    subject TEXT,
    weak_topic TEXT,
    report_content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance logs (legacy compat)
CREATE TABLE IF NOT EXISTS performance_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    prediction TEXT,
    suggestion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id)
);

-- Subject-level analysis
CREATE TABLE IF NOT EXISTS subject_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT,
    subject TEXT,
    marks INTEGER,
    behavior TEXT,
    weak_topics TEXT
);

-- =====================================================
-- Understanding Level Assessment System (NLE Engine)
-- =====================================================

-- Each assessment session a student takes
CREATE TABLE IF NOT EXISTS understanding_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL,
    subject TEXT NOT NULL,
    topic TEXT NOT NULL,
    difficulty_level TEXT DEFAULT 'medium',
    total_questions INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    time_taken_seconds INTEGER DEFAULT 0,
    comprehension_score REAL DEFAULT 0.0,
    speed_ratio REAL DEFAULT 1.0,
    understanding_index REAL DEFAULT 0.0,
    tier TEXT DEFAULT 'Needs Work',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Individual question results within an assessment
CREATE TABLE IF NOT EXISTS assessment_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    options TEXT NOT NULL,
    correct_option INTEGER NOT NULL,
    selected_option INTEGER,
    is_correct INTEGER DEFAULT 0,
    difficulty TEXT DEFAULT 'medium',
    time_spent_seconds INTEGER DEFAULT 0,
    FOREIGN KEY (assessment_id) REFERENCES understanding_assessments(id)
);

-- Per-student per-subject baseline learning speeds for normalization
CREATE TABLE IF NOT EXISTS understanding_baselines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL,
    subject TEXT NOT NULL,
    avg_time_per_question REAL DEFAULT 30.0,
    avg_accuracy REAL DEFAULT 0.5,
    total_assessments INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_name, subject)
);