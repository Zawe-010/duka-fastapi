from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from random import randint
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import africastalking
import os
from dotenv import load_dotenv

from app.models import User, OTP, session
from .auth_service import (
    hash_password,
    authenticate_user,
    create_access_token,
    register_user,
)

router = APIRouter()
load_dotenv()
db = session()

# ---------------- ENV ----------------
BREVO_SMTP_USERNAME = os.getenv("BREVO_SMTP_USERNAME")
BREVO_SMTP_PASSWORD = os.getenv("BREVO_SMTP_PASSWORD")
BREVO_SMTP_SERVER = os.getenv("BREVO_SMTP_SERVER")
BREVO_SMTP_PORT = int(os.getenv("BREVO_SMTP_PORT", 587))

AT_USERNAME = os.getenv("AT_USERNAME")
AT_API_KEY = os.getenv("AT_API_KEY")

# ---------------- SMS INIT ----------------
try:
    africastalking.initialize(AT_USERNAME, AT_API_KEY)
    sms = africastalking.SMS()
except Exception as e:
    print("Africastalking init failed:", e)
    sms = None

# ---------------- SCHEMAS ----------------
class UserRegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    method: str          # email | sms
    identifier: str      # email or phone

class VerifyOTPRequest(BaseModel):
    otp: str

class ResetPasswordRequest(BaseModel):
    new_password: str

# ---------------- REGISTER ----------------
@router.post("/register", tags=["auth"])
def register(user: UserRegisterRequest):
    try:
        new_user = register_user(
            user.full_name,
            user.email,
            user.password,
        )
        token = create_access_token(new_user.email)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "full_name": new_user.full_name,
            },
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# ---------------- LOGIN (JSON – FRONTEND) ----------------
@router.post("/login", tags=["auth"])
def login(data: LoginRequest):
    user = authenticate_user(data.email, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
        },
    }

# ---------------- LOGIN (OAUTH2 – SWAGGER) ----------------
@router.post("/token", tags=["auth"])
def login_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
    }

# ---------------- FORGOT PASSWORD ----------------
@router.post("/forgot-password", tags=["auth"])
def forgot_password(data: ForgotPasswordRequest):
    method = data.method.lower()
    identifier = data.identifier

    if method == "email":
        user = db.query(User).filter(User.email == identifier).first()
    elif method == "sms":
        user = db.query(User).filter(User.phone == identifier).first()
    else:
        raise HTTPException(status_code=400, detail="Invalid method")

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp_code = str(randint(1000, 9999))
    db.add(OTP(user_id=user.id, otp=otp_code, created_at=datetime.utcnow()))
    db.commit()

    if method == "email":
        msg = MIMEMultipart()
        msg["From"] = BREVO_SMTP_USERNAME
        msg["To"] = user.email
        msg["Subject"] = "Password Reset OTP"
        msg.attach(MIMEText(f"Your OTP is {otp_code}", "plain"))

        server = smtplib.SMTP(BREVO_SMTP_SERVER, BREVO_SMTP_PORT)
        server.starttls()
        server.login(BREVO_SMTP_USERNAME, BREVO_SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()

    else:
        sms.send(message=f"Your OTP is {otp_code}", recipients=[user.phone])

    return {"message": "OTP sent", "user_id": user.id}

# ---------------- VERIFY OTP ----------------
@router.post("/verify-code/{user_id}", tags=["auth"])
def verify_otp(user_id: int, data: VerifyOTPRequest):
    record = (
        db.query(OTP)
        .filter(OTP.user_id == user_id, OTP.otp == data.otp)
        .order_by(OTP.created_at.desc())
        .first()
    )

    if not record:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if datetime.utcnow() - record.created_at > timedelta(minutes=10):
        raise HTTPException(status_code=400, detail="OTP expired")

    return {"message": "OTP verified"}

# ---------------- RESET PASSWORD ----------------
@router.post("/reset-password/{user_id}", tags=["auth"])
def reset_password(user_id: int, data: ResetPasswordRequest):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password = hash_password(data.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Password updated"}
