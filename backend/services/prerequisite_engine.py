import json
import re
import pandas as pd
import networkx as nx


PREREQUISITE_FILE = "data/prerequisite_edges.csv"
COURSE_CATALOG_FILE = "data/course_catalog_clean.json"


# ============================================================
# LOAD PREREQUISITE GRAPH
# ============================================================

def load_prerequisite_graph():

    edges = pd.read_csv(PREREQUISITE_FILE)

    graph = nx.DiGraph()

    for _, row in edges.iterrows():

        prerequisite = str(
            row["prerequisite_course"]
        ).strip()

        target = str(
            row["target_course"]
        ).strip()

        relation = str(
            row["relation_context"]
        ).strip()

        if not prerequisite or not target:
            continue

        graph.add_edge(
            prerequisite,
            target,
            relation=relation
        )

    return graph


# ============================================================
# LOAD COURSE CATALOG
# ============================================================

def load_course_catalog():

    with open(
        COURSE_CATALOG_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# NORMALIZE COURSE CODE
# ============================================================

def normalize_course_code(course):

    if course is None:
        return ""

    course = str(course).strip()

    course = re.sub(
        r"\s+",
        " ",
        course
    )

    return course


# ============================================================
# GET COMPLETED COURSES
# ============================================================

def get_completed_courses(
    academic_records
):

    completed = academic_records[
        academic_records["status"]
        .astype(str)
        .str.lower()
        .eq("completed")
    ]

    return {
        normalize_course_code(code)
        for code in completed["course_code"]
    }


# ============================================================
# PARSE SIMPLE PREREQUISITE LIST
# ============================================================

def parse_prerequisites(
    prerequisite_list
):

    if not prerequisite_list:
        return []

    cleaned = []

    for item in prerequisite_list:

        item = normalize_course_code(item)

        if not item:
            continue

        if item.lower() in {
            "and",
            "or"
        }:
            cleaned.append(
                item.lower()
            )
        else:
            cleaned.append(item)

    return cleaned


# ============================================================
# CHECK PREREQUISITES
# ============================================================

def check_prerequisites(
    prerequisite_list,
    completed_courses
):

    tokens = parse_prerequisites(
        prerequisite_list
    )

    if not tokens:

        return {
            "eligible": True,
            "missing_prerequisites": []
        }


    # --------------------------------------------------------
    # Extract course codes and operators
    # --------------------------------------------------------

    courses = [
        token
        for token in tokens
        if token not in {"and", "or"}
    ]


    # --------------------------------------------------------
    # Simple case: one prerequisite
    # --------------------------------------------------------

    if len(courses) == 1:

        course = courses[0]

        return {
            "eligible": course in completed_courses,
            "missing_prerequisites": (
                []
                if course in completed_courses
                else [course]
            )
        }


    # --------------------------------------------------------
    # OR-only expression
    # Example:
    #
    # CSE 20 OR MATH 15A
    # --------------------------------------------------------

    if "and" not in tokens:

        satisfied = any(
            course in completed_courses
            for course in courses
        )

        return {
            "eligible": satisfied,
            "missing_prerequisites": (
                []
                if satisfied
                else courses
            )
        }


    # --------------------------------------------------------
    # AND-only expression
    # Example:
    #
    # CSE 12 AND CSE 15L
    # --------------------------------------------------------

    if "or" not in tokens:

        missing = [
            course
            for course in courses
            if course not in completed_courses
        ]

        return {
            "eligible": len(missing) == 0,
            "missing_prerequisites": missing
        }


    # --------------------------------------------------------
    # Mixed AND / OR
    #
    # For complex expressions, use prerequisite graph
    # relationships to determine missing courses.
    # --------------------------------------------------------

    missing = [
        course
        for course in courses
        if course not in completed_courses
    ]


    # If every listed course is completed,
    # the requirement is definitely satisfied.
    if not missing:

        return {
            "eligible": True,
            "missing_prerequisites": []
        }


    # If some courses are missing, conservatively
    # mark the course as not eligible.
    return {
        "eligible": False,
        "missing_prerequisites": missing
    }


# ============================================================
# CHECK COURSE ELIGIBILITY
# ============================================================

def check_course_eligibility(
    course_code,
    course_data,
    completed_courses,
    graph
):

    course_code = normalize_course_code(
        course_code
    )


    # --------------------------------------------------------
    # Get prerequisites from course catalog
    # --------------------------------------------------------

    prerequisites = course_data.get(
        "prerequisites",
        []
    )


    result = check_prerequisites(
        prerequisites,
        completed_courses
    )


    return result


# ============================================================
# FIND ELIGIBLE COURSES
# ============================================================

def find_eligible_courses(
    academic_records
):

    graph = load_prerequisite_graph()

    catalog = load_course_catalog()

    completed_courses = get_completed_courses(
        academic_records
    )


    eligible_courses = []


    for raw_course_code, course_data in catalog.items():

        course_code = normalize_course_code(
            raw_course_code
        )


        # Don't recommend completed courses
        if course_code in completed_courses:
            continue


        result = check_course_eligibility(
            course_code,
            course_data,
            completed_courses,
            graph
        )


        if result["eligible"]:

            eligible_courses.append({

                "course_code":
                    course_code,

                "course_name":
                    course_data.get(
                        "name",
                        "Unknown Course"
                    ).strip(),

                "prerequisites":
                    course_data.get(
                        "prerequisites",
                        []
                    ),

                "missing_prerequisites":
                    result[
                        "missing_prerequisites"
                    ]

            })


    return eligible_courses