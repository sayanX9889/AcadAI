from fastapi import APIRouter, HTTPException
import pandas as pd

from backend.database import get_connection

from backend.services.academic_analyzer import (
    calculate_average_attendance,
    find_weak_subjects,
    calculate_academic_risk,
    generate_recommendations,
    calculate_career_match,
)


router = APIRouter(
    prefix="/students",
    tags=["Academic Analysis"]
)


@router.get("/{student_id}/analysis")
def get_student_analysis(student_id: str):

    # =========================================================
    # NORMALIZE STUDENT ID
    # =========================================================

    student_id = student_id.strip().upper()

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # =====================================================
        # GET ACADEMIC PROFILE
        # =====================================================

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
                detail=(
                    "Academic profile not found. "
                    "Please complete your Academic Profile first."
                )
            )

        # =====================================================
        # CONVERT PROFILE TO DICTIONARY
        # =====================================================

        profile_data = {
            "student_id": profile["student_id"],
            "cgpa": float(profile["cgpa"]),
            "target_cgpa": float(profile["target_cgpa"]),
            "career_goal": profile["career_goal"] or "",
            "current_semester": int(profile["current_semester"]),
            "academic_year": profile["academic_year"],
        }

        # =====================================================
        # GET ALL SUBJECTS FROM ALL SEMESTERS
        #
        # IMPORTANT:
        # Do NOT filter by current_semester here.
        #
        # The user wants the AI analysis to use their
        # complete academic history.
        # =====================================================

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
            ORDER BY semester ASC, id ASC
            """,
            (student_id,)
        )

        rows = cursor.fetchall()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=(
                    "No academic subjects found for this student. "
                    "Please add subjects to your Academic Profile."
                )
            )

        # =====================================================
        # SQLITE ROWS → PANDAS DATAFRAME
        # =====================================================

        records = pd.DataFrame(
            [
                {
                    "semester": int(row["semester"]),
                    "academic_year": row["academic_year"],
                    "course_code": row["course_code"],
                    "course_name": row["course_name"],
                    "marks": float(row["marks"]),
                    "attendance_percent": float(
                        row["attendance_percent"]
                    ),
                    "status": row["status"] or "completed",
                }
                for row in rows
            ]
        )

        # =====================================================
        # SAFETY CHECK
        # =====================================================

        if records.empty:
            raise HTTPException(
                status_code=404,
                detail="No academic records available for analysis."
            )

        # =====================================================
        # ACADEMIC VALUES
        # =====================================================

        cgpa = profile_data["cgpa"]
        target_cgpa = profile_data["target_cgpa"]

        # =====================================================
        # AVERAGE ATTENDANCE
        # =====================================================

        average_attendance = calculate_average_attendance(
            records
        )

        # =====================================================
        # FIND WEAK SUBJECTS
        # =====================================================

        weak_subjects_df = find_weak_subjects(
            records
        )

        # =====================================================
        # MAKE SURE WEAK SUBJECTS IS A DATAFRAME
        #
        # This protects against the previous:
        #
        # AttributeError:
        # 'list' object has no attribute 'empty'
        # =====================================================

        if isinstance(weak_subjects_df, list):

            weak_subjects_df = pd.DataFrame(
                weak_subjects_df
            )

        elif weak_subjects_df is None:

            weak_subjects_df = pd.DataFrame()

        # =====================================================
        # ACADEMIC RISK
        # =====================================================

        academic_risk = calculate_academic_risk(
            records,
            cgpa
        )

        # =====================================================
        # RECOMMENDATIONS
        # =====================================================

        recommendations = generate_recommendations(
            records,
            cgpa
        )

        # =====================================================
        # CAREER MATCH
        # =====================================================

        career_match = calculate_career_match(
            profile_data,
            records
        )

        # =====================================================
        # CONVERT WEAK SUBJECTS TO JSON
        # =====================================================

        weak_subjects = []

        if not weak_subjects_df.empty:

            available_columns = [
                column
                for column in [
                    "semester",
                    "academic_year",
                    "course_code",
                    "course_name",
                    "marks",
                    "attendance_percent",
                    "status",
                ]
                if column in weak_subjects_df.columns
            ]

            weak_subjects = (
                weak_subjects_df[
                    available_columns
                ]
                .to_dict(orient="records")
            )

        # =====================================================
        # CONVERT ALL SUBJECTS TO JSON
        # =====================================================

        subjects = records.to_dict(
            orient="records"
        )

        # =====================================================
        # SEMESTER SUMMARY
        # =====================================================

        semester_summary = []

        for semester_number in sorted(
            records["semester"].unique()
        ):

            semester_records = records[
                records["semester"] == semester_number
            ]

            semester_summary.append(
                {
                    "semester": int(semester_number),

                    "academic_year":
                        semester_records[
                            "academic_year"
                        ].iloc[0],

                    "subject_count":
                        int(len(semester_records)),

                    "average_marks":
                        round(
                            float(
                                semester_records[
                                    "marks"
                                ].mean()
                            ),
                            2
                        ),

                    "average_attendance":
                        round(
                            float(
                                semester_records[
                                    "attendance_percent"
                                ].mean()
                            ),
                            2
                        ),
                }
            )

        # =====================================================
        # RETURN PERSONALIZED ANALYSIS
        # =====================================================

        return {

            # -------------------------------------------------
            # STUDENT
            # -------------------------------------------------

            "student_id":
                student_id,

            # -------------------------------------------------
            # PROFILE
            # -------------------------------------------------

            "cgpa":
                cgpa,

            "target_cgpa":
                target_cgpa,

            "career_goal":
                profile_data["career_goal"],

            "current_semester":
                profile_data["current_semester"],

            "academic_year":
                profile_data["academic_year"],

            # -------------------------------------------------
            # ACADEMIC SUMMARY
            # -------------------------------------------------

            "average_attendance":
                round(
                    float(average_attendance),
                    2
                ),

            "total_subject_count":
                int(len(subjects)),

            "weak_subject_count":
                int(len(weak_subjects)),

            # -------------------------------------------------
            # WEAK SUBJECTS
            # -------------------------------------------------

            "weak_subjects":
                weak_subjects,

            # -------------------------------------------------
            # AI / ACADEMIC ANALYSIS
            # -------------------------------------------------

            "academic_risk":
                academic_risk,

            "career_match":
                career_match,

            "recommendations":
                recommendations,

            # -------------------------------------------------
            # ALL SUBJECTS
            # -------------------------------------------------

            "subjects":
                subjects,

            # -------------------------------------------------
            # SEMESTER-WISE SUMMARY
            # -------------------------------------------------

            "semester_summary":
                semester_summary,
        }

    except HTTPException:
        raise

    except Exception as error:

        # Print the real error in terminal
        # so debugging is much easier.

        print(
            "ERROR in /students/{student_id}/analysis:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to generate academic analysis: "
                f"{str(error)}"
            )
        )

    finally:

        connection.close()