from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from backend.database import get_connection


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/students",
    tags=["Academic Profile"]
)


# ============================================================
# SUBJECT MODEL
# ============================================================

class SubjectInput(BaseModel):

    course_code: str

    course_name: str

    marks: float = Field(
        ge=0,
        le=100
    )

    attendance_percent: float = Field(
        ge=0,
        le=100
    )

    status: str = "completed"


# ============================================================
# ACADEMIC PROFILE REQUEST
# ============================================================

class AcademicProfileRequest(BaseModel):

    # Overall/current CGPA
    cgpa: float = Field(
        ge=0,
        le=10
    )

    # Target CGPA
    target_cgpa: float = Field(
        ge=0,
        le=10
    )

    # Career goal
    career_goal: Optional[str] = ""

    # Semester being saved
    current_semester: int = Field(
        ge=1,
        le=12
    )

    # Academic year
    academic_year: str = "2025-2026"

    # CGPA for selected semester
    semester_cgpa: float = Field(
        ge=0,
        le=10
    )

    # Subjects belonging to selected semester
    subjects: List[SubjectInput]


# ============================================================
# GET ACADEMIC PROFILE
#
# Example:
#
# GET
# /students/STU001/academic-profile
#
# Returns the student's current profile and subjects
# for the current semester.
#
# ============================================================

@router.get("/{student_id}/academic-profile")
def get_academic_profile(
    student_id: str,
    semester: Optional[int] = Query(
        default=None,
        ge=1,
        le=12
    ),
    academic_year: str = "2025-2026"
):

    student_id = (
        student_id
        .strip()
        .upper()
    )

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ====================================================
        # GET MAIN PROFILE
        # ====================================================

        cursor.execute(
            """
            SELECT
                student_id,
                cgpa,
                target_cgpa,
                career_goal,
                current_semester,
                academic_year
            FROM academic_profiles
            WHERE student_id = ?
            """,
            (student_id,)
        )

        profile = cursor.fetchone()


        # ====================================================
        # PROFILE DOES NOT EXIST
        # ====================================================

        if not profile:

            connection.close()

            return {
                "student_id": student_id,
                "profile_exists": False,
                "subjects": []
            }


        # ====================================================
        # DETERMINE SEMESTER
        # ====================================================

        selected_semester = (
            semester
            if semester is not None
            else profile["current_semester"]
        )

        selected_year = (
            academic_year
            if academic_year
            else profile["academic_year"]
        )


        # ====================================================
        # GET SEMESTER CGPA
        # ====================================================

        semester_cgpa = None

        if selected_semester is not None:

            cursor.execute(
                """
                SELECT
                    semester_cgpa
                FROM academic_semesters
                WHERE student_id = ?
                  AND semester = ?
                  AND academic_year = ?
                """,
                (
                    student_id,
                    selected_semester,
                    selected_year
                )
            )

            semester_record = cursor.fetchone()

            if semester_record:

                semester_cgpa = (
                    semester_record["semester_cgpa"]
                )


        # ====================================================
        # GET SUBJECTS FOR SELECTED SEMESTER
        # ====================================================

        subjects = []

        if selected_semester is not None:

            cursor.execute(
                """
                SELECT
                    course_code,
                    course_name,
                    marks,
                    attendance_percent,
                    status
                FROM academic_subjects
                WHERE student_id = ?
                  AND semester = ?
                  AND academic_year = ?
                ORDER BY id
                """,
                (
                    student_id,
                    selected_semester,
                    selected_year
                )
            )

            subjects = cursor.fetchall()


        # ====================================================
        # RETURN DATA
        # ====================================================

        return {
            "student_id": profile["student_id"],

            "profile_exists": True,

            "cgpa": profile["cgpa"],

            "target_cgpa": profile["target_cgpa"],

            "career_goal": profile["career_goal"],

            "current_semester": profile["current_semester"],

            "academic_year": profile["academic_year"],

            "selected_semester": selected_semester,

            "selected_academic_year": selected_year,

            "semester_cgpa": semester_cgpa,

            "subjects": [
                dict(subject)
                for subject in subjects
            ]
        }

    finally:

        connection.close()


# ============================================================
# GET COMPLETE ACADEMIC HISTORY
#
# This endpoint is for the AI chatbot / analysis module.
#
# It returns ALL semesters.
#
# Example:
#
# GET /students/STU001/academic-history
#
# ============================================================

@router.get("/{student_id}/academic-history")
def get_academic_history(
    student_id: str
):

    student_id = (
        student_id
        .strip()
        .upper()
    )

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ====================================================
        # CHECK PROFILE
        # ====================================================

        cursor.execute(
            """
            SELECT
                student_id,
                cgpa,
                target_cgpa,
                career_goal,
                current_semester,
                academic_year
            FROM academic_profiles
            WHERE student_id = ?
            """,
            (student_id,)
        )

        profile = cursor.fetchone()


        if not profile:

            raise HTTPException(
                status_code=404,
                detail="Academic profile not found."
            )


        # ====================================================
        # GET ALL SEMESTER CGPAs
        # ====================================================

        cursor.execute(
            """
            SELECT
                semester,
                academic_year,
                semester_cgpa,
                updated_at
            FROM academic_semesters
            WHERE student_id = ?
            ORDER BY semester
            """,
            (student_id,)
        )

        semesters = cursor.fetchall()


        # ====================================================
        # GET ALL SUBJECTS
        # ====================================================

        cursor.execute(
            """
            SELECT
                semester,
                academic_year,
                course_code,
                course_name,
                marks,
                attendance_percent,
                status
            FROM academic_subjects
            WHERE student_id = ?
            ORDER BY semester, id
            """,
            (student_id,)
        )

        subjects = cursor.fetchall()


        # ====================================================
        # GROUP SUBJECTS BY SEMESTER
        # ====================================================

        semester_data = {}


        for semester in semesters:

            key = (
                semester["semester"],
                semester["academic_year"]
            )

            semester_data[key] = {

                "semester":
                    semester["semester"],

                "academic_year":
                    semester["academic_year"],

                "semester_cgpa":
                    semester["semester_cgpa"],

                "subjects": []
            }


        for subject in subjects:

            key = (
                subject["semester"],
                subject["academic_year"]
            )

            if key not in semester_data:

                semester_data[key] = {

                    "semester":
                        subject["semester"],

                    "academic_year":
                        subject["academic_year"],

                    "semester_cgpa":
                        None,

                    "subjects": []
                }


            semester_data[key]["subjects"].append(
                {
                    "course_code":
                        subject["course_code"],

                    "course_name":
                        subject["course_name"],

                    "marks":
                        subject["marks"],

                    "attendance_percent":
                        subject["attendance_percent"],

                    "status":
                        subject["status"]
                }
            )


        # ====================================================
        # RETURN COMPLETE HISTORY
        # ====================================================

        return {

            "student_id":
                profile["student_id"],

            "cgpa":
                profile["cgpa"],

            "target_cgpa":
                profile["target_cgpa"],

            "career_goal":
                profile["career_goal"],

            "current_semester":
                profile["current_semester"],

            "academic_year":
                profile["academic_year"],

            "semesters":
                list(
                    semester_data.values()
                )
        }

    finally:

        connection.close()


# ============================================================
# SAVE / UPDATE ACADEMIC PROFILE
#
# IMPORTANT:
# Only the selected semester's subjects are replaced.
#
# Semester 1 data will NOT be deleted when Semester 2
# is saved.
#
# ============================================================

@router.put("/{student_id}/academic-profile")
def save_academic_profile(
    student_id: str,
    request: AcademicProfileRequest
):

    student_id = (
        student_id
        .strip()
        .upper()
    )

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ====================================================
        # CHECK USER
        # ====================================================

        cursor.execute(
            """
            SELECT student_id
            FROM users
            WHERE student_id = ?
            """,
            (student_id,)
        )

        user = cursor.fetchone()


        if not user:

            raise HTTPException(
                status_code=404,
                detail="Student account not found."
            )


        # ====================================================
        # SAVE / UPDATE MAIN PROFILE
        # ====================================================

        cursor.execute(
            """
            INSERT INTO academic_profiles (
                student_id,
                cgpa,
                target_cgpa,
                career_goal,
                current_semester,
                academic_year,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(student_id)
            DO UPDATE SET

                cgpa =
                    excluded.cgpa,

                target_cgpa =
                    excluded.target_cgpa,

                career_goal =
                    excluded.career_goal,

                current_semester =
                    excluded.current_semester,

                academic_year =
                    excluded.academic_year,

                updated_at =
                    excluded.updated_at
            """,
            (
                student_id,

                request.cgpa,

                request.target_cgpa,

                request.career_goal,

                request.current_semester,

                request.academic_year,

                datetime.now().isoformat()
            )
        )


        # ====================================================
        # SAVE SEMESTER CGPA
        # ====================================================

        cursor.execute(
            """
            INSERT INTO academic_semesters (
                student_id,
                semester,
                academic_year,
                semester_cgpa,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?)

            ON CONFLICT(
                student_id,
                semester,
                academic_year
            )
            DO UPDATE SET

                semester_cgpa =
                    excluded.semester_cgpa,

                updated_at =
                    excluded.updated_at
            """,
            (
                student_id,

                request.current_semester,

                request.academic_year,

                request.semester_cgpa,

                datetime.now().isoformat()
            )
        )


        # ====================================================
        # DELETE ONLY SELECTED SEMESTER
        #
        # DO NOT DELETE OTHER SEMESTERS.
        # ====================================================

        cursor.execute(
            """
            DELETE FROM academic_subjects

            WHERE student_id = ?

              AND semester = ?

              AND academic_year = ?
            """,
            (
                student_id,

                request.current_semester,

                request.academic_year
            )
        )


        # ====================================================
        # INSERT SELECTED SEMESTER SUBJECTS
        # ====================================================

        for subject in request.subjects:

            cursor.execute(
                """
                INSERT INTO academic_subjects (
                    student_id,
                    semester,
                    academic_year,
                    course_code,
                    course_name,
                    marks,
                    attendance_percent,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    student_id,

                    request.current_semester,

                    request.academic_year,

                    subject.course_code
                        .strip()
                        .upper(),

                    subject.course_name
                        .strip(),

                    subject.marks,

                    subject.attendance_percent,

                    subject.status
                )
            )


        # ====================================================
        # COMMIT
        # ====================================================

        connection.commit()


        return {

            "success": True,

            "message":
                "Academic profile saved successfully.",

            "student_id":
                student_id,

            "semester":
                request.current_semester,

            "academic_year":
                request.academic_year,

            "subjects_saved":
                len(request.subjects)
        }


    except HTTPException:

        connection.rollback()

        raise


    except Exception as error:

        connection.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Unable to save academic profile: {str(error)}"
        )


    finally:

        connection.close()