from fastapi import APIRouter
import pandas as pd

router = APIRouter(
    prefix="/students",
    tags=["Academic Records"]
)

academic_records = pd.read_csv(
    "data/academic_records.csv"
)


@router.get("/{student_id}/records")
def get_academic_records(student_id: str):

    result = academic_records[
        academic_records["student_id"] == student_id
    ]

    if result.empty:
        return {
            "error": "Academic records not found"
        }

    return result.to_dict(orient="records")