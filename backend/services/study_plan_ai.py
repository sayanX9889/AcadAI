import json

from backend.services.model_service import (
    generate_ai_response as generate_model_response
)


def generate_ai_study_plan(
    study_plan: list,
    weekly_hours: float
) -> str:

    system_prompt = """
You are AcadAI, an AI academic study-planning assistant.

Create a practical weekly study schedule using ONLY the
study-plan data provided.

STRICT RULES:

1. Do not invent subjects, marks, attendance, or hours.
2. Do not change the weekly hours assigned by the academic planner.
3. Higher-priority subjects should receive more attention.
4. Use the exact course names and hours provided.
5. Give practical study activities such as revision,
   practice questions, concepts, and problem solving.
6. Keep the schedule realistic for a college student.
7. Do not provide unrelated advice.
8. If information is missing, clearly say so.
"""

    # Convert study plan to JSON
    context = json.dumps(
        study_plan,
        indent=2,
        default=str
    )

    prompt = f"""
{system_prompt}

==============================
WEEKLY STUDY HOURS
==============================

{weekly_hours}

==============================
ACADEMIC PLANNER DATA
==============================

{context}

==============================
TASK
==============================

Create a concise personalized weekly study schedule.

For each subject, include:

- Subject name
- Allocated weekly hours
- What to study
- Suggested study activity

Do not change the allocated hours.
"""

    # Send request to the selected AI provider.
    return generate_model_response(
        prompt=prompt,
        system_prompt=system_prompt
    )