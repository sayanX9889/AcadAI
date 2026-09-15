import sqlite3
from pathlib import Path
from datetime import datetime


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DATABASE_PATH = Path("data/academic_advisor.db")


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    # Enable foreign keys
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    # ========================================================
    # USERS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_id TEXT UNIQUE NOT NULL,

            full_name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password_hash TEXT NOT NULL,

            created_at TEXT NOT NULL
        )
    """)


    # ========================================================
    # PROFILE PICTURE
    # ========================================================

    cursor.execute(
        "PRAGMA table_info(users)"
    )

    user_columns = [
        row["name"]
        for row in cursor.fetchall()
    ]

    if "profile_picture" not in user_columns:

        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN profile_picture TEXT
        """)


    # ========================================================
    # ACADEMIC PROFILE
    #
    # Stores overall/current student information.
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS academic_profiles (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_id TEXT UNIQUE NOT NULL,

            cgpa REAL NOT NULL DEFAULT 0,

            target_cgpa REAL NOT NULL DEFAULT 0,

            career_goal TEXT,

            current_semester INTEGER,

            academic_year TEXT,

            updated_at TEXT NOT NULL,

            FOREIGN KEY(student_id)
                REFERENCES users(student_id)
                ON DELETE CASCADE
        )
    """)


    # ========================================================
    # SUBJECT RECORDS
    #
    # IMPORTANT:
    # semester + academic_year make the subjects
    # semester-specific.
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS academic_subjects (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_id TEXT NOT NULL,

            semester INTEGER NOT NULL DEFAULT 1,

            academic_year TEXT NOT NULL DEFAULT '2025-2026',

            course_code TEXT NOT NULL,

            course_name TEXT NOT NULL,

            marks REAL NOT NULL DEFAULT 0,

            attendance_percent REAL NOT NULL DEFAULT 0,

            status TEXT NOT NULL DEFAULT 'completed',

            FOREIGN KEY(student_id)
                REFERENCES users(student_id)
                ON DELETE CASCADE
        )
    """)


    # ========================================================
    # MIGRATION FOR OLD DATABASE
    #
    # Your old academic_subjects table did not have
    # semester or academic_year.
    #
    # These checks allow an existing database to continue
    # working without deleting old data.
    # ========================================================

    cursor.execute(
        "PRAGMA table_info(academic_subjects)"
    )

    subject_columns = [
        row["name"]
        for row in cursor.fetchall()
    ]


    # Add semester to old databases

    if "semester" not in subject_columns:

        cursor.execute("""
            ALTER TABLE academic_subjects
            ADD COLUMN semester INTEGER
            NOT NULL DEFAULT 1
        """)


    # Add academic_year to old databases

    if "academic_year" not in subject_columns:

        cursor.execute("""
            ALTER TABLE academic_subjects
            ADD COLUMN academic_year TEXT
            NOT NULL DEFAULT '2025-2026'
        """)


    # ========================================================
    # SEMESTER INFORMATION
    #
    # Stores semester-specific CGPA.
    #
    # Example:
    #
    # Student STU001
    # Semester 1 → 7.2
    # Semester 2 → 7.5
    # Semester 3 → 7.8
    #
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS academic_semesters (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_id TEXT NOT NULL,

            semester INTEGER NOT NULL,

            academic_year TEXT NOT NULL,

            semester_cgpa REAL,

            updated_at TEXT NOT NULL,

            UNIQUE(
                student_id,
                semester,
                academic_year
            ),

            FOREIGN KEY(student_id)
                REFERENCES users(student_id)
                ON DELETE CASCADE
        )
    """)


    # ========================================================
    # INDEXES
    #
    # Makes semester queries faster.
    # ========================================================

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_academic_subjects_student_semester
        ON academic_subjects(
            student_id,
            semester,
            academic_year
        )
    """)


    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_academic_semesters_student
        ON academic_semesters(
            student_id,
            semester,
            academic_year
        )
    """)


    # ========================================================
    # SAVE DATABASE
    # ========================================================

    connection.commit()

    connection.close()