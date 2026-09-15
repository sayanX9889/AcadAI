import pandas as pd

from backend.services.prerequisite_engine import (
    load_prerequisite_graph,
    find_eligible_courses,
    get_completed_courses
)


print()
print("======================================")
print("CSE PREREQUISITE ENGINE TEST")
print("======================================")


# ------------------------------------------------------------
# Load academic records
# ------------------------------------------------------------

records = pd.read_csv(
    "data/academic_records.csv"
)


student_id = "STU0001"


student_records = records[
    records["student_id"] == student_id
].copy()


print(
    f"Student: {student_id}"
)

print(
    f"Completed records: {len(student_records)}"
)


# ------------------------------------------------------------
# Show completed courses
# ------------------------------------------------------------

completed_courses = get_completed_courses(
    student_records
)


print()
print("Completed courses:")

for course in sorted(completed_courses):
    print(
        f"  ✓ {course}"
    )


# ------------------------------------------------------------
# Load graph
# ------------------------------------------------------------

graph = load_prerequisite_graph()


print()
print(
    f"Graph nodes: {graph.number_of_nodes()}"
)

print(
    f"Graph edges: {graph.number_of_edges()}"
)


# ------------------------------------------------------------
# Find eligible courses
# ------------------------------------------------------------

eligible = find_eligible_courses(
    student_records
)


# ------------------------------------------------------------
# Filter CSE courses
# ------------------------------------------------------------

cse_courses = [

    course
    for course in eligible

    if course["course_code"].startswith("CSE ")
]


print()
print(
    f"Total eligible courses: {len(eligible)}"
)

print(
    f"Eligible CSE courses: {len(cse_courses)}"
)


# ------------------------------------------------------------
# Display CSE recommendations
# ------------------------------------------------------------

print()
print("First 20 eligible CSE courses:")
print("--------------------------------------")


for course in cse_courses[:20]:

    print(
        f"{course['course_code']}: "
        f"{course['course_name']}"
    )


print()
print("======================================")
print("TEST COMPLETE")
print("======================================")