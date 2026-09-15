import pandas as pd
import json

# Load students
students = pd.read_csv("data/students.csv")

# Load academic records
academic_records = pd.read_csv("data/academic_records.csv")

# Load course catalog
with open("data/course_catalog_clean.json", "r") as file:
    courses = json.load(file)

# Load prerequisite edges
prerequisites = pd.read_csv("data/prerequisite_edges.csv")


print("================================")
print("AI ACADEMIC ADVISOR DATA TEST")
print("================================")

print("Students:", len(students))
print("Academic records:", len(academic_records))
print("Courses:", len(courses))
print("Prerequisite edges:", len(prerequisites))

print("\nFirst student:")
print(students.iloc[0])

print("\nFirst academic record:")
print(academic_records.iloc[0])

print("\nFirst prerequisite:")
print(prerequisites.iloc[0])