from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException
)
from pathlib import Path
import uuid
PROFILE_DIR = Path(
    "data/profile_pictures"
)

PROFILE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp"
}

MAX_PROFILE_SIZE = 5 * 1024 * 1024
from pydantic import BaseModel, EmailStr
from datetime import datetime
import hashlib
import hmac
import secrets

from backend.database import get_connection


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password: str) -> str:

    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        310000
    )

    return (
        salt.hex()
        + ":"
        + password_hash.hex()
    )


def verify_password(
    password: str,
    stored_password: str
) -> bool:

    try:

        salt_hex, hash_hex = (
            stored_password.split(":")
        )

        salt = bytes.fromhex(salt_hex)

        stored_hash = bytes.fromhex(hash_hex)

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            310000
        )

        return hmac.compare_digest(
            password_hash,
            stored_hash
        )

    except (ValueError, TypeError):

        return False


# ============================================================
# REQUEST MODELS
# ============================================================

class SignupRequest(BaseModel):

    student_id: str
    full_name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):

    student_id: str
    password: str


# ============================================================
# SIGNUP
# ============================================================

@router.post("/signup")
def signup(request: SignupRequest):

    student_id = (
        request.student_id
        .strip()
        .upper()
    )

    full_name = (
        request.full_name
        .strip()
    )

    email = (
        str(request.email)
        .strip()
        .lower()
    )

    password = request.password


    if not student_id:

        return {
            "success": False,
            "error": "Student ID is required."
        }


    if not full_name:

        return {
            "success": False,
            "error": "Full name is required."
        }


    if len(password) < 6:

        return {
            "success": False,
            "error": "Password must be at least 6 characters."
        }


    connection = get_connection()

    cursor = connection.cursor()


    # --------------------------------------------------------
    # CHECK STUDENT ID
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE student_id = ?
        """,
        (student_id,)
    )

    existing_student = cursor.fetchone()


    if existing_student:

        connection.close()

        return {
            "success": False,
            "error": "Student ID already registered."
        }


    # --------------------------------------------------------
    # CHECK EMAIL
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE email = ?
        """,
        (email,)
    )

    existing_email = cursor.fetchone()


    if existing_email:

        connection.close()

        return {
            "success": False,
            "error": "Email already registered."
        }


    # --------------------------------------------------------
    # HASH PASSWORD
    # --------------------------------------------------------

    password_hash = hash_password(
        password
    )


    # --------------------------------------------------------
    # CREATE ACCOUNT
    # --------------------------------------------------------

    cursor.execute(
        """
        INSERT INTO users (
            student_id,
            full_name,
            email,
            password_hash,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            student_id,
            full_name,
            email,
            password_hash,
            datetime.now().isoformat()
        )
    )


    connection.commit()

    connection.close()


    return {
        "success": True,
        "message": "Account created successfully.",
        "student_id": student_id
    }


# ============================================================
# LOGIN
# ============================================================

@router.post("/login")
def login(request: LoginRequest):

    student_id = (
        request.student_id
        .strip()
        .upper()
    )

    password = request.password


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            student_id,
            full_name,
            email,
            password_hash
        FROM users
        WHERE student_id = ?
        """,
        (student_id,)
    )


    user = cursor.fetchone()

    connection.close()


    if not user:

        return {
            "success": False,
            "error": "Invalid Student ID or password."
        }


    if not verify_password(
        password,
        user["password_hash"]
    ):

        return {
            "success": False,
            "error": "Invalid Student ID or password."
        }


    return {
        "success": True,
        "message": "Login successful.",

        "student": {

            "student_id":
                user["student_id"],

            "full_name":
                user["full_name"],

            "email":
                user["email"]
        }
    }
    # ============================================================
# GET PROFILE
# ============================================================

@router.get("/profile/{student_id}")
def get_profile(student_id: str):

    student_id = (
        student_id
        .strip()
        .upper()
    )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            student_id,
            full_name,
            email,
            profile_picture
        FROM users
        WHERE student_id = ?
        """,
        (student_id,)
    )

    user = cursor.fetchone()

    connection.close()


    if not user:

        raise HTTPException(
            status_code=404,
            detail="Student account not found."
        )


    profile_picture = None

    if user["profile_picture"]:

        profile_picture = (
            "/uploads/profile_pictures/"
            + user["profile_picture"]
        )


    return {
        "student_id":
            user["student_id"],

        "full_name":
            user["full_name"],

        "email":
            user["email"],

        "profile_picture":
            profile_picture
    }


# ============================================================
# UPLOAD PROFILE PICTURE
# ============================================================

@router.post("/profile-picture/{student_id}")
async def upload_profile_picture(
    student_id: str,
    file: UploadFile = File(...)
):

    student_id = (
        student_id
        .strip()
        .upper()
    )


    # --------------------------------------------------------
    # VALIDATE FILE TYPE
    # --------------------------------------------------------

    if file.content_type not in ALLOWED_IMAGE_TYPES:

        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG, and WEBP images are allowed."
        )


    # --------------------------------------------------------
    # READ FILE
    # --------------------------------------------------------

    image_data = await file.read()


    # --------------------------------------------------------
    # VALIDATE FILE SIZE
    # --------------------------------------------------------

    if len(image_data) > MAX_PROFILE_SIZE:

        raise HTTPException(
            status_code=400,
            detail="Profile picture must be smaller than 5 MB."
        )


    if len(image_data) == 0:

        raise HTTPException(
            status_code=400,
            detail="The uploaded image is empty."
        )


    # --------------------------------------------------------
    # CHECK STUDENT
    # --------------------------------------------------------

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            profile_picture
        FROM users
        WHERE student_id = ?
        """,
        (student_id,)
    )

    user = cursor.fetchone()


    if not user:

        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Student account not found."
        )


    # --------------------------------------------------------
    # DELETE OLD PICTURE
    # --------------------------------------------------------

    old_picture = user["profile_picture"]

    if old_picture:

        old_path = (
            PROFILE_DIR / old_picture
        )

        if old_path.exists():

            old_path.unlink()


    # --------------------------------------------------------
    # CREATE NEW FILE NAME
    # --------------------------------------------------------

    extension = ALLOWED_IMAGE_TYPES[
        file.content_type
    ]

    filename = (
        student_id
        + "_"
        + uuid.uuid4().hex
        + extension
    )


    file_path = (
        PROFILE_DIR / filename
    )


    # --------------------------------------------------------
    # SAVE IMAGE
    # --------------------------------------------------------

    with open(
        file_path,
        "wb"
    ) as image_file:

        image_file.write(
            image_data
        )


    # --------------------------------------------------------
    # SAVE FILE NAME IN DATABASE
    # --------------------------------------------------------

    cursor.execute(
        """
        UPDATE users
        SET profile_picture = ?
        WHERE student_id = ?
        """,
        (
            filename,
            student_id
        )
    )


    connection.commit()

    connection.close()


    return {

        "success": True,

        "message":
            "Profile picture updated successfully.",

        "profile_picture":
            "/uploads/profile_pictures/"
            + filename
    }

# ============================================================
# DELETE ACCOUNT
# ============================================================

@router.delete("/account/{student_id}")
def delete_account(student_id: str):

    student_id = (
        student_id
        .strip()
        .upper()
    )

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # CHECK ACCOUNT
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                profile_picture
            FROM users
            WHERE student_id = ?
            """,
            (student_id,)
        )

        user = cursor.fetchone()

        if not user:

            raise HTTPException(
                status_code=404,
                detail="Student account not found."
            )

        # ----------------------------------------------------
        # DELETE PROFILE PICTURE FROM DISK
        # ----------------------------------------------------

        old_picture = user["profile_picture"]

        if old_picture:

            old_path = PROFILE_DIR / old_picture

            if old_path.exists() and old_path.is_file():
                old_path.unlink()

        # ----------------------------------------------------
        # DELETE USER-OWNED ACADEMIC PROFILE DATA
        # ----------------------------------------------------
        # These tables are created/used by academic_profile.py.
        # Check that they exist so account deletion still works
        # with older databases.

        cursor.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name IN "
            "('academic_subjects', 'academic_profiles')"
        )

        existing_tables = {
            row["name"]
            for row in cursor.fetchall()
        }

        if "academic_subjects" in existing_tables:

            cursor.execute(
                """
                DELETE FROM academic_subjects
                WHERE student_id = ?
                """,
                (student_id,)
            )

        if "academic_profiles" in existing_tables:

            cursor.execute(
                """
                DELETE FROM academic_profiles
                WHERE student_id = ?
                """,
                (student_id,)
            )

        # ----------------------------------------------------
        # DELETE LOGIN ACCOUNT
        # ----------------------------------------------------

        cursor.execute(
            """
            DELETE FROM users
            WHERE student_id = ?
            """,
            (student_id,)
        )

        connection.commit()

        return {
            "success": True,
            "message": "Account deleted successfully.",
            "student_id": student_id
        }

    except HTTPException:

        connection.rollback()
        raise

    except Exception as error:

        connection.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Unable to delete account: {error}"
        )

    finally:

        connection.close()

