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
import os
import re
import smtplib
from email.message import EmailMessage
from datetime import timedelta

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

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyResetCodeRequest(BaseModel):
    email: EmailStr
    code: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    reset_token: str
    new_password: str


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
# PASSWORD RESET / EMAIL OTP
# ============================================================

OTP_EXPIRY_MINUTES = 10
RESET_TOKEN_EXPIRY_MINUTES = 10
MAX_OTP_ATTEMPTS = 5


def hash_reset_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def send_password_reset_email(email: str, otp: str):
    gmail_address = os.getenv("GMAIL_ADDRESS")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_address or not gmail_app_password:
        raise RuntimeError(
            "GMAIL_ADDRESS and GMAIL_APP_PASSWORD are not configured."
        )

    message = EmailMessage()
    message["Subject"] = "AcadAI Password Reset Code"
    message["From"] = gmail_address
    message["To"] = email
    message.set_content(
        f"""Hello,

We received a request to reset your AcadAI password.

Your 6-digit password reset code is:

{otp}

This code expires in {OTP_EXPIRY_MINUTES} minutes.

If you did not request this password reset, you can safely ignore this email.

Regards,
AcadAI
"""
    )

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(gmail_address, gmail_app_password)
        smtp.send_message(message)


@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest):
    email = str(request.email).strip().lower()

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT student_id
            FROM users
            WHERE email = ?
            """,
            (email,)
        )
        user = cursor.fetchone()

        # Keep the response generic so account existence is not disclosed.
        if not user:
            return {
                "success": True,
                "message": "If an account exists for this email, a reset code has been sent."
            }

        # Invalidate previous reset codes for this account.
        cursor.execute(
            """
            UPDATE email_verifications
            SET used = TRUE,
                reset_token_hash = NULL,
                reset_token_expires_at = NULL
            WHERE student_id = ? AND used = FALSE
            """,
            (user["student_id"],)
        )

        otp = f"{secrets.randbelow(1_000_000):06d}"
        otp_hash = hash_reset_value(otp)
        now = datetime.now()
        expires_at = (now + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat()

        cursor.execute(
            """
            INSERT INTO email_verifications (
                student_id,
                email,
                otp_hash,
                expires_at,
                used,
                attempts,
                reset_token_hash,
                reset_token_expires_at,
                created_at
            )
            VALUES (?, ?, ?, ?, FALSE, 0, NULL, NULL, ?)
            """,
            (
                user["student_id"],
                email,
                otp_hash,
                expires_at,
                now.isoformat()
            )
        )
        connection.commit()

        try:
            send_password_reset_email(email, otp)
        except Exception:
            # Do not leave a usable code when delivery failed.
            cursor.execute(
                """
                UPDATE email_verifications
                SET used = TRUE
                WHERE student_id = ? AND otp_hash = ?
                """,
                (user["student_id"], otp_hash)
            )
            connection.commit()
            raise HTTPException(
                status_code=500,
                detail="Unable to send password reset email. Please try again later."
            )

        return {
            "success": True,
            "message": "If an account exists for this email, a reset code has been sent."
        }

    except HTTPException:
        connection.rollback()
        raise
    except Exception as error:
        connection.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Unable to process password reset request: {error}"
        )
    finally:
        connection.close()


@router.post("/verify-reset-code")
def verify_reset_code(request: VerifyResetCodeRequest):
    email = str(request.email).strip().lower()
    code = request.code.strip()

    if not re.fullmatch(r"\d{6}", code):
        raise HTTPException(
            status_code=400,
            detail="Reset code must contain exactly 6 digits."
        )

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT
                id,
                student_id,
                otp_hash,
                expires_at,
                used,
                attempts
            FROM email_verifications
            WHERE email = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (email,)
        )
        verification = cursor.fetchone()

        if not verification or verification["used"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired reset code."
            )

        if verification["attempts"] >= MAX_OTP_ATTEMPTS:
            cursor.execute(
                """
                UPDATE email_verifications
                SET used = TRUE
                WHERE id = ?
                """,
                (verification["id"],)
            )
            connection.commit()
            raise HTTPException(
                status_code=400,
                detail="Too many incorrect attempts. Please request a new code."
            )

        try:
            expires_at = datetime.fromisoformat(verification["expires_at"])
        except (ValueError, TypeError):
            expires_at = datetime.min

        if datetime.now() > expires_at:
            cursor.execute(
                """
                UPDATE email_verifications
                SET used = TRUE
                WHERE id = ?
                """,
                (verification["id"],)
            )
            connection.commit()
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired reset code."
            )

        if not hmac.compare_digest(
            hash_reset_value(code),
            verification["otp_hash"]
        ):
            cursor.execute(
                """
                UPDATE email_verifications
                SET attempts = attempts + 1
                WHERE id = ?
                """,
                (verification["id"],)
            )
            connection.commit()
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired reset code."
            )

        reset_token = secrets.token_urlsafe(32)
        reset_token_hash = hash_reset_value(reset_token)
        reset_token_expires_at = (
            datetime.now() + timedelta(minutes=RESET_TOKEN_EXPIRY_MINUTES)
        ).isoformat()

        cursor.execute(
            """
            UPDATE email_verifications
            SET used = TRUE,
                reset_token_hash = ?,
                reset_token_expires_at = ?
            WHERE id = ?
            """,
            (
                reset_token_hash,
                reset_token_expires_at,
                verification["id"]
            )
        )
        connection.commit()

        return {
            "success": True,
            "message": "Reset code verified successfully.",
            "reset_token": reset_token
        }

    except HTTPException:
        raise
    except Exception as error:
        connection.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Unable to verify reset code: {error}"
        )
    finally:
        connection.close()


@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest):
    email = str(request.email).strip().lower()
    reset_token = request.reset_token.strip()
    new_password = request.new_password

    if len(new_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters."
        )

    if not reset_token:
        raise HTTPException(
            status_code=400,
            detail="Reset token is required."
        )

    connection = get_connection()
    cursor = connection.cursor()

    try:
        reset_token_hash = hash_reset_value(reset_token)

        cursor.execute(
            """
            SELECT
                id,
                student_id,
                reset_token_expires_at
            FROM email_verifications
            WHERE email = ?
              AND reset_token_hash = ?
              AND used = TRUE
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (email, reset_token_hash)
        )
        verification = cursor.fetchone()

        if not verification:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired reset session."
            )

        try:
            token_expires_at = datetime.fromisoformat(
                verification["reset_token_expires_at"]
            )
        except (ValueError, TypeError):
            token_expires_at = datetime.min

        if datetime.now() > token_expires_at:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired reset session."
            )

        new_password_hash = hash_password(new_password)

        cursor.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE student_id = ? AND email = ?
            """,
            (
                new_password_hash,
                verification["student_id"],
                email
            )
        )

        if cursor.rowcount != 1:
            raise HTTPException(
                status_code=404,
                detail="Student account not found."
            )

        cursor.execute(
            """
            UPDATE email_verifications
            SET reset_token_hash = NULL,
                reset_token_expires_at = NULL
            WHERE id = ?
            """,
            (verification["id"],)
        )

        connection.commit()

        return {
            "success": True,
            "message": "Password reset successfully. You can now log in."
        }

    except HTTPException:
        connection.rollback()
        raise
    except Exception as error:
        connection.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Unable to reset password: {error}"
        )
    finally:
        connection.close()


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
        # CHECK ACCOUNT AND GET PROFILE PICTURE
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

        old_picture = user["profile_picture"]

        # ----------------------------------------------------
        # DELETE USER-OWNED DATA
        #
        # academic_profiles, academic_subjects and
        # academic_semesters already use ON DELETE CASCADE
        # through users(student_id).
        #
        # notifications, feedback and email_verifications
        # are explicitly deleted here for a complete cleanup.
        # ----------------------------------------------------

        # Notifications
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'notifications'
            ) AS table_exists
            """
        )

        notifications_table = cursor.fetchone()

        if notifications_table and notifications_table["table_exists"]:
            cursor.execute(
                """
                DELETE FROM notifications
                WHERE student_id = ?
                """,
                (student_id,)
            )

        # Feedback
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'feedback'
            ) AS table_exists
            """
        )

        feedback_table = cursor.fetchone()

        if feedback_table and feedback_table["table_exists"]:
            cursor.execute(
                """
                DELETE FROM feedback
                WHERE student_id = ?
                """,
                (student_id,)
            )

        # Email verification
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'email_verifications'
            ) AS table_exists
            """
        )

        email_verifications_table = cursor.fetchone()

        if email_verifications_table and email_verifications_table["table_exists"]:
            cursor.execute(
                """
                DELETE FROM email_verifications
                WHERE student_id = ?
                """,
                (student_id,)
            )

        # ----------------------------------------------------
        # DELETE USER
        #
        # This automatically removes:
        #   - academic_profiles
        #   - academic_subjects
        #   - academic_semesters
        #
        # because their foreign keys use ON DELETE CASCADE.
        # ----------------------------------------------------

        cursor.execute(
            """
            DELETE FROM users
            WHERE student_id = ?
            """,
            (student_id,)
        )

        if cursor.rowcount != 1:
            raise HTTPException(
                status_code=404,
                detail="Student account not found."
            )

        # ----------------------------------------------------
        # COMMIT DATABASE CLEANUP FIRST
        # ----------------------------------------------------

        connection.commit()

        # ----------------------------------------------------
        # DELETE PROFILE PICTURE FROM SERVER STORAGE
        #
        # The database stores only the filename. The actual
        # image file must also be removed from disk.
        # ----------------------------------------------------

        profile_picture_deleted = True

        if old_picture:

            old_path = PROFILE_DIR / old_picture

            try:
                if old_path.exists() and old_path.is_file():
                    old_path.unlink()
            except OSError:
                # The account is already deleted from the database.
                # Keep the response successful but report that the
                # physical file could not be removed.
                profile_picture_deleted = False

        return {
            "success": True,
            "message": "Account and all associated data deleted successfully.",
            "student_id": student_id,
            "profile_picture_deleted": profile_picture_deleted
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
