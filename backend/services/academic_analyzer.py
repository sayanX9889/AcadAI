import pandas as pd

from backend.services.prerequisite_engine import (
    find_eligible_courses
)


# ============================================================
# DATA NORMALIZATION
# ============================================================

REQUIRED_COLUMNS = [
    "course_code",
    "course_name",
    "marks",
    "attendance_percent",
    "status",
]


def _ensure_dataframe(records):
    """
    Convert academic records into a Pandas DataFrame.

    Supported input:
        - list[dict]
        - dict
        - Pandas DataFrame
    """

    if records is None:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    if isinstance(records, pd.DataFrame):
        df = records.copy()

    elif isinstance(records, list):
        df = pd.DataFrame(records)

    elif isinstance(records, dict):
        df = pd.DataFrame([records])

    else:
        raise TypeError(
            f"Unsupported records type: {type(records).__name__}"
        )

    # Make sure all required columns exist
    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            df[column] = None

    # Numeric fields
    df["marks"] = pd.to_numeric(
        df["marks"],
        errors="coerce"
    ).fillna(0)

    df["attendance_percent"] = pd.to_numeric(
        df["attendance_percent"],
        errors="coerce"
    ).fillna(0)

    # Text fields
    df["course_code"] = (
        df["course_code"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["course_name"] = (
        df["course_name"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["status"] = (
        df["status"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    return df


# ============================================================
# AVERAGE ATTENDANCE
# ============================================================

def calculate_average_attendance(records):
    """
    Calculate average attendance across all academic records.
    """

    records = _ensure_dataframe(records)

    if records.empty:
        return 0.0

    return round(
        records["attendance_percent"].mean(),
        2
    )


# ============================================================
# FIND WEAK SUBJECTS
# ============================================================

def find_weak_subjects(records):
    """
    Identify subjects requiring academic attention.

    A subject is weak when:
        - marks < 60
        OR
        - attendance < 75%
    """

    records = _ensure_dataframe(records)

    if records.empty:
        return records.copy()

    weak = records[
        (records["marks"] < 60)
        |
        (records["attendance_percent"] < 75)
    ].copy()

    return weak


# ============================================================
# ACADEMIC RISK
# ============================================================

def calculate_academic_risk(records, cgpa):
    """
    Determine overall academic risk.
    """

    records = _ensure_dataframe(records)

    weak_subjects = find_weak_subjects(records)

    low_attendance = records[
        records["attendance_percent"] < 75
    ]

    try:
        cgpa = float(cgpa)

    except (TypeError, ValueError):
        cgpa = 0.0

    if cgpa < 5.0 or len(weak_subjects) >= 3:
        return "High"

    if cgpa < 7.0 or len(weak_subjects) >= 1:
        return "Moderate"

    if len(low_attendance) >= 2:
        return "Moderate"

    return "Low"


# ============================================================
# CAREER MATCH
# ============================================================

def calculate_career_match(student, records):
    """
    Calculate personalized career compatibility.

    Uses:
        1. Target career
        2. Actual academic courses
        3. Course codes
        4. Course names
        5. Marks
        6. Attendance

    The result is dynamically calculated from the student's
    actual academic records.
    """

    records = _ensure_dataframe(records)

    # ========================================================
    # STUDENT CAREER
    # ========================================================

    career_goal = str(
        student.get("career_goal", "")
    ).strip()

    if not career_goal:
        return {
            "career": "Not specified",
            "match_percentage": 0,
            "matched_courses": [],
            "matched_course_count": 0,
            "relevant_course_count": 0,
            "message": (
                "No career goal has been specified."
            )
        }

    career = career_goal.lower()

    # ========================================================
    # CAREER → RELEVANT COURSE CODES
    # ========================================================

    career_courses = {

        "ai/ml engineer": {
            "CSE 100",
            "CSE 103",
            "CSE 105",
            "CSE 106",
            "CSE 150A",
            "CSE 150B",
            "CSE 151A",
            "CSE 152",
            "CSE 156",
            "MATH 18",
            "MATH 20A",
            "MATH 20B",
            "MATH 181A"
        },

        "data scientist": {
            "CSE 100",
            "CSE 103",
            "CSE 105",
            "CSE 106",
            "CSE 150A",
            "CSE 151A",
            "CSE 152",
            "CSE 156",
            "MATH 18",
            "MATH 20A",
            "MATH 20B",
            "MATH 181A",
            "MATH 183"
        },

        "data engineer": {
            "CSE 100",
            "CSE 101",
            "CSE 102",
            "CSE 110",
            "CSE 120",
            "CSE 130",
            "CSE 132A",
            "DSC 80"
        },

        "software engineer": {
            "CSE 11",
            "CSE 5A",
            "CSE 12",
            "CSE 100",
            "CSE 101",
            "CSE 102",
            "CSE 110",
            "CSE 120",
            "CSE 130",
            "CSE 150B"
        },

        "web developer": {
            "CSE 11",
            "CSE 12",
            "CSE 110",
            "CSE 120",
            "CSE 130",
            "CSE 150B"
        },

        "cybersecurity engineer": {
            "CSE 30",
            "CSE 100",
            "CSE 110",
            "CSE 120",
            "CSE 130"
        },

        "cloud engineer": {
            "CSE 30",
            "CSE 110",
            "CSE 120",
            "CSE 130",
            "CSE 150B"
        }
    }

    # ========================================================
    # FIND CAREER KEY
    # ========================================================

    career_key = None

    for key in career_courses:

        if (
            career == key
            or key in career
            or career in key
        ):
            career_key = key
            break

    # ========================================================
    # UNKNOWN CAREER
    # ========================================================

    if career_key is None:

        return {
            "career": career_goal,
            "match_percentage": 0,
            "matched_courses": [],
            "matched_course_count": 0,
            "relevant_course_count": 0,
            "message": (
                f"Career matching rules for "
                f"{career_goal} have not been configured yet."
            )
        }

    relevant_courses = career_courses[career_key]

    # ========================================================
    # STUDENT RECORDS
    # ========================================================

    completed = records[
        records["status"]
        .astype(str)
        .str.lower()
        .isin([
            "completed",
            "complete",
            "passed",
            "current"
        ])
    ].copy()

    # If status filtering produces nothing,
    # use the student's actual records.
    if completed.empty and not records.empty:
        completed = records.copy()

    if completed.empty:

        return {
            "career": career_goal,
            "match_percentage": 0,
            "matched_courses": [],
            "matched_course_count": 0,
            "relevant_course_count": len(
                relevant_courses
            ),
            "message": (
                "No academic records are available "
                "for career matching."
            )
        }

    # ========================================================
    # NORMALIZE COURSE CODES
    # ========================================================

    completed["normalized_code"] = (
        completed["course_code"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    normalized_relevant_codes = {
        str(code).upper().strip()
        for code in relevant_courses
    }

    # ========================================================
    # EXACT COURSE CODE MATCH
    # ========================================================

    matched_rows = completed[
        completed["normalized_code"].isin(
            normalized_relevant_codes
        )
    ].copy()

    matched_courses = []

    for _, row in matched_rows.iterrows():

        matched_courses.append({
            "course_code": row["course_code"],
            "course_name": row["course_name"],
            "marks": float(row["marks"]),
            "attendance_percent": float(
                row["attendance_percent"]
            )
        })

    # ========================================================
    # COURSE NAME KEYWORDS
    # ========================================================

    keyword_map = {

        "ai/ml engineer": [
            "artificial intelligence",
            "machine learning",
            "deep learning",
            "data science",
            "probability",
            "statistics",
            "statistical",
            "linear algebra",
            "calculus",
            "algorithm",
            "data structure",
            "python"
        ],

        "data scientist": [
            "data science",
            "statistics",
            "statistical",
            "probability",
            "machine learning",
            "artificial intelligence",
            "linear algebra",
            "calculus",
            "algorithm",
            "data structure"
        ],

        "data engineer": [
            "database",
            "data structure",
            "data science",
            "systems",
            "programming",
            "algorithm"
        ],

        "software engineer": [
            "programming",
            "data structure",
            "algorithm",
            "software engineering",
            "computer organization",
            "operating systems",
            "systems programming"
        ],

        "web developer": [
            "programming",
            "software engineering",
            "database",
            "web"
        ],

        "cybersecurity engineer": [
            "operating systems",
            "computer networks",
            "network",
            "systems",
            "programming",
            "algorithm",
            "security",
            "cybersecurity"
        ],

        "cloud engineer": [
            "operating systems",
            "systems",
            "database",
            "programming",
            "computer organization",
            "cloud",
            "network"
        ]
    }

    keywords = keyword_map.get(
        career_key,
        []
    )

    # ========================================================
    # MATCH BY COURSE NAME
    # ========================================================

    existing_codes = {
        str(course["course_code"])
        .upper()
        .strip()
        for course in matched_courses
    }

    for _, row in completed.iterrows():

        course_name = str(
            row["course_name"]
        ).lower()

        course_code = str(
            row["course_code"]
        ).upper().strip()

        if not course_name:
            continue

        if course_code in existing_codes:
            continue

        if any(
            keyword in course_name
            for keyword in keywords
        ):

            matched_courses.append({
                "course_code": row["course_code"],
                "course_name": row["course_name"],
                "marks": float(row["marks"]),
                "attendance_percent": float(
                    row["attendance_percent"]
                )
            })

            existing_codes.add(course_code)

    # ========================================================
    # COURSE COVERAGE
    # ========================================================

    relevant_course_count = len(
        relevant_courses
    )

    matched_course_count = len(
        matched_courses
    )

    course_coverage = (
        matched_course_count
        /
        max(relevant_course_count, 1)
    ) * 100

    course_coverage = min(
        course_coverage,
        100
    )

    # ========================================================
    # MARKS SCORE
    # ========================================================

    performance_score = 0.0

    if matched_courses:

        average_marks = sum(
            course["marks"]
            for course in matched_courses
        ) / len(matched_courses)

        # Maximum 20 points
        performance_score = (
            average_marks / 100
        ) * 20

    # ========================================================
    # ATTENDANCE SCORE
    # ========================================================

    attendance_score = 0.0

    if matched_courses:

        average_attendance = sum(
            course["attendance_percent"]
            for course in matched_courses
        ) / len(matched_courses)

        # Maximum 10 points
        attendance_score = (
            average_attendance / 100
        ) * 10

    # ========================================================
    # FINAL CAREER MATCH
    # ========================================================

    if matched_courses:

        # 70% → relevant course coverage
        # 20% → marks
        # 10% → attendance

        match_percentage = round(
            (
                course_coverage * 0.70
            )
            +
            performance_score
            +
            attendance_score
        )

    else:

        match_percentage = 0

    match_percentage = max(
        0,
        min(
            match_percentage,
            100
        )
    )

    # ========================================================
    # MESSAGE
    # ========================================================

    if match_percentage >= 80:

        message = (
            f"Excellent! Your academic profile has a "
            f"{match_percentage}% match with your "
            f"target career."
        )

    elif match_percentage >= 60:

        message = (
            f"Good career alignment. Your academic "
            f"profile has a {match_percentage}% match "
            f"with your target career."
        )

    elif match_percentage >= 30:

        message = (
            f"Your academic profile currently has a "
            f"{match_percentage}% match with your "
            f"target career. Focus on building more "
            f"skills related to {career_goal}."
        )

    else:

        message = (
            f"Your current academic profile has a "
            f"{match_percentage}% match with "
            f"{career_goal}. More relevant courses "
            f"and skills are needed."
        )

    # ========================================================
    # RETURN
    # ========================================================

    return {
        "career": career_goal,

        "match_percentage":
            match_percentage,

        "matched_courses":
            matched_courses,

        "matched_course_count":
            matched_course_count,

        "relevant_course_count":
            relevant_course_count,

        "course_coverage":
            round(
                course_coverage,
                2
            ),

        "average_marks": round(
            sum(
                course["marks"]
                for course in matched_courses
            ) / matched_course_count,
            2
        ) if matched_courses else 0,

        "average_attendance": round(
            sum(
                course["attendance_percent"]
                for course in matched_courses
            ) / matched_course_count,
            2
        ) if matched_courses else 0,

        "message":
            message
    }


# ============================================================
# RECOMMENDATIONS
# ============================================================

def generate_recommendations(records, cgpa):
    """
    Generate rule-based academic recommendations.

    Uses:
        - Weak subjects
        - Attendance
        - CGPA
        - Prerequisite eligibility
    """

    records = _ensure_dataframe(records)

    recommendations = []

    try:
        cgpa = float(cgpa)

    except (TypeError, ValueError):
        cgpa = 0.0

    # ========================================================
    # 1. WEAK SUBJECTS
    # ========================================================

    weak_subjects = find_weak_subjects(
        records
    )

    for _, subject in weak_subjects.iterrows():

        marks = float(
            subject["marks"]
        )

        attendance = float(
            subject["attendance_percent"]
        )

        # ----------------------------------------------------
        # LOW MARKS
        # ----------------------------------------------------

        if marks < 60:

            recommendations.append({
                "type": "academic",

                "course_code":
                    subject["course_code"],

                "course_name":
                    subject["course_name"],

                "message": (
                    f"Improve "
                    f"{subject['course_name']}. "
                    f"Current marks are "
                    f"{marks:g}/100."
                )
            })

        # ----------------------------------------------------
        # LOW ATTENDANCE
        # ----------------------------------------------------

        if attendance < 75:

            recommendations.append({
                "type": "attendance",

                "course_code":
                    subject["course_code"],

                "course_name":
                    subject["course_name"],

                "message": (
                    f"Attendance in "
                    f"{subject['course_name']} "
                    f"is {attendance:g}%. "
                    f"Try to maintain attendance "
                    f"above 75%."
                )
            })

    # ========================================================
    # 2. CGPA RECOMMENDATION
    # ========================================================

    if cgpa < 7.0:

        recommendations.append({
            "type": "cgpa",

            "message": (
                f"Current CGPA is {cgpa:g}. "
                f"Increase weekly study time and "
                f"prioritize low-performing subjects."
            )
        })

    # ========================================================
    # 3. PREREQUISITE RECOMMENDATIONS
    # ========================================================

    try:

        eligible_courses = find_eligible_courses(
            records
        )

        cse_courses = [
            course
            for course in eligible_courses
            if str(
                course.get(
                    "course_code",
                    ""
                )
            ).upper().startswith("CSE ")
        ]

        # Maximum 10 course recommendations
        cse_courses = cse_courses[:10]

        for course in cse_courses:

            recommendations.append({
                "type": "course",

                "course_code":
                    course.get(
                        "course_code",
                        ""
                    ),

                "course_name":
                    course.get(
                        "course_name",
                        ""
                    ),

                "message": (
                    f"{course.get('course_name', '')} "
                    f"is eligible because its "
                    f"prerequisites are satisfied."
                ),

                "prerequisites":
                    course.get(
                        "prerequisites",
                        []
                    )
            })

    except Exception as error:

        print(
            "Prerequisite recommendation error:",
            error
        )

    return recommendations