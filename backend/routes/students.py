from fastapi import APIRouter, HTTPException

from backend.database import get_connection

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/{student_id}")
def get_student(student_id: str):

    student_id = student_id.strip().upper()

    connection = get_connection()
    cursor = connection.cursor()

    # ---------------------------------------------------------
    # GET BASIC USER INFORMATION
    # ---------------------------------------------------------

    cursor.execute(
        """
        SELECT student_id
        FROM users
        WHERE student_id = ?
        """,
        (student_id,),
    )

    user = cursor.fetchone()

    if not user:
        connection.close()
        raise HTTPException(status_code=404, detail="Student not found")

    # ---------------------------------------------------------
    # GET ACADEMIC PROFILE
    # ---------------------------------------------------------

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
        (student_id,),
    )

    profile = cursor.fetchone()

    if not profile:
        connection.close()

        return {
            "student_id": student_id,
            "profile_exists": False,
            "cgpa": None,
            "target_cgpa": None,
            "career_goal": None,
            "current_semester": None,
            "academic_year": None,
        }

    connection.close()

    return {
        "student_id": profile["student_id"],
        "profile_exists": True,
        "cgpa": profile["cgpa"],
        "target_cgpa": profile["target_cgpa"],
        "career_goal": profile["career_goal"],
        "current_semester": profile["current_semester"],
        "academic_year": profile["academic_year"],
    }
