from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.database import initialize_database

from backend.routes.students import router as student_router
from backend.routes.records import router as records_router
from backend.routes.analysis import router as analysis_router
from backend.routes.study_plan import router as study_plan_router
from backend.routes.chatbot import router as chatbot_router
from backend.routes.auth import router as auth_router
from backend.routes.academic_profile import router as academic_profile_router
from backend.routes.feedback import router as feedback_router
from backend.routes.feedback import initialize_feedback_table
from backend.routes.quiz import router as quiz_router
from backend.routes.notifications import router as notifications_router
from backend.routes.notifications import initialize_notifications_table

app = FastAPI(
    title="AI Academic Advisor",
    description="AI-powered academic advisory system",
    version="1.0.0"
)

initialize_database()
initialize_feedback_table()
initialize_notifications_table()

app.mount(
    "/uploads",
    StaticFiles(directory="data"),
    name="uploads"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(student_router)
app.include_router(records_router)
app.include_router(analysis_router)
app.include_router(study_plan_router)
app.include_router(chatbot_router)
app.include_router(auth_router)
app.include_router(academic_profile_router)
app.include_router(feedback_router)
app.include_router(quiz_router)
app.include_router(notifications_router)


@app.get("/")
def home():
    return {"message": "AI Academic Advisor is running"}


@app.get("/health")
def health():
    return {"status": "OK"}
