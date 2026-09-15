import pandas as pd


def generate_study_plan(records, weekly_hours=10):
    """
    Generate a personalized weekly study plan.

    Priority is based on:
    1. Low marks
    2. Low attendance
    3. Overall academic weakness
    """

    if records.empty:
        return []

    subjects = []

    for _, record in records.iterrows():

        marks = float(record["marks"])
        attendance = float(record["attendance_percent"])

        # Calculate priority score
        priority = 0

        # Lower marks = higher priority
        if marks < 60:
            priority += 50
        elif marks < 70:
            priority += 30
        elif marks < 80:
            priority += 15

        # Lower attendance = higher priority
        if attendance < 75:
            priority += 30
        elif attendance < 80:
            priority += 15

        # Always give every subject a small baseline priority
        priority += 5

        subjects.append({
            "course_code": record["course_code"],
            "course_name": record["course_name"],
            "marks": marks,
            "attendance": attendance,
            "priority": priority
        })

    # Highest priority first
    subjects.sort(
        key=lambda x: x["priority"],
        reverse=True
    )

    # Allocate study hours
    total_priority = sum(
        subject["priority"]
        for subject in subjects
    )

    plan = []

    for subject in subjects:

        if total_priority == 0:
            hours = 0
        else:
            hours = round(
                weekly_hours
                * subject["priority"]
                / total_priority,
                1
            )

        plan.append({
            "course_code": subject["course_code"],
            "course_name": subject["course_name"],
            "marks": subject["marks"],
            "attendance": subject["attendance"],
            "priority": subject["priority"],
            "weekly_hours": hours
        })

    return plan