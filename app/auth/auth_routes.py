from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from random import randint
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import africastalking  # Africastalking SMS

from app.models import User, OTP, session
from .auth_service import hash_password, authenticate_user, create_access_token, register_user
import os
from dotenv import load_dotenv

router = APIRouter()
load_dotenv()
db = session()

# Brevo SMTP
BREVO_SMTP_USERNAME = os.getenv("BREVO_SMTP_USERNAME")
BREVO_SMTP_PASSWORD = os.getenv("BREVO_SMTP_PASSWORD")
BREVO_SMTP_SERVER = os.getenv("BREVO_SMTP_SERVER")
BREVO_SMTP_PORT = int(os.getenv("BREVO_SMTP_PORT", 587))

# Africastalking SMS
AT_USERNAME = os.getenv("AT_USERNAME")
AT_API_KEY = os.getenv("AT_API_KEY")

# Initialize Africastalking SMS service
try:
    africastalking.initialize(AT_USERNAME, AT_API_KEY)
    sms = africastalking.SMS()  # Initialize the SMS service correctly
except Exception as e:
    print("Africastalking initialization failed:", e)
    sms = None  # Set to None if the initialization fails

# --- Pydantic Models ---
class UserRegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class LoginRequest(BaseModel):
    email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str
    method: str  # 'email' or 'sms'

class ResetPasswordRequest(BaseModel):
    new_password: str

class VerifyOTPRequest(BaseModel):
    otp: str

# -----------------------------
# 1. REGISTER
# -----------------------------
@router.post("/register", response_model=TokenResponse, tags=["auth"])
def register(user: UserRegisterRequest):
    try:
        new_user = register_user(user.full_name, user.email, user.password)
        token = create_access_token(new_user.email)
        return {
            "user": {"id": new_user.id, "full_name": new_user.full_name, "email": new_user.email},
            "access_token": token,
            "token_type": "bearer",
        }
    except Exception as e:
        db.rollback()  # <-- this fixes the transaction error
        raise HTTPException(status_code=400, detail=str(e))

# -----------------------------
# 2a. LOGIN (OAuth2 - Postman/API)
# -----------------------------
@router.post("/token", response_model=TokenResponse, tags=["auth"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(user.email)
    return {
        "user": {"id": user.id, "full_name": user.full_name, "email": user.email},
        "access_token": token,
        "token_type": "bearer",
    }

# -----------------------------
# 2b. LOGIN (JSON - Browser/React)
# -----------------------------
@router.post("/login", response_model=TokenResponse, tags=["auth"])
async def login_with_json(data: LoginRequest):
    user = authenticate_user(data.email, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(user.email)
    return {
        "user": {"id": user.id, "full_name": user.full_name, "email": user.email},
        "access_token": token,
        "token_type": "bearer",
    }

# -----------------------------
# 3. FORGOT PASSWORD (flexible: email or SMS)
# -----------------------------
@router.post("/forgot-password", response_model=dict, tags=["auth"])
def forgot_password(data: ForgotPasswordRequest):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp_code = f"{randint(1000, 9999)}"
    otp_entry = OTP(user_id=user.id, otp=otp_code, created_at=datetime.utcnow())
    db.add(otp_entry)
    db.commit()

    method = data.method.lower()
    if method == "email":
        try:
            message = MIMEMultipart()
            message['From'] = BREVO_SMTP_USERNAME
            message['To'] = user.email
            message['Subject'] = "Password Reset OTP"
            body = f"Hello {user.full_name},\n\nYour password reset OTP is: {otp_code}\nThis code expires in 10 minutes."
            message.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(BREVO_SMTP_SERVER, BREVO_SMTP_PORT)
            server.starttls()
            server.login(BREVO_SMTP_USERNAME, BREVO_SMTP_PASSWORD)
            server.send_message(message)
            server.quit()
            return {"message": "OTP sent to your email"}
        except Exception as e:
            print("Email sending error:", e)
            raise HTTPException(status_code=500, detail="Failed to send OTP email")

    elif method == "sms":
        if not user.phone:
            raise HTTPException(status_code=400, detail="No phone number found for this user")
        if sms is None:
            raise HTTPException(status_code=500, detail="Africastalking SMS service is not initialized correctly")

        try:
            # Africastalking SMS integration
            response = sms.send(
                message=f"Your password reset code is {otp_code}",
                recipients=[user.phone]
            )
            print("SMS sent:", response)
            return {"message": "OTP sent via SMS"}
        except Exception as e:
            print("Africastalking SMS error:", e)
            raise HTTPException(status_code=500, detail="Failed to send OTP via SMS")
    else:
        raise HTTPException(status_code=400, detail="Invalid method. Choose 'email' or 'sms'")

# -----------------------------
# 4. VERIFY OTP
# -----------------------------
@router.post("/verify-code/{user_id}", response_model=dict, tags=["auth"])
def verify_code(user_id: int, data: VerifyOTPRequest):
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

    return {"message": "OTP verified successfully"}

# -----------------------------
# 5. RESET PASSWORD
# -----------------------------
@router.post("/reset-password/{user_id}", response_model=dict, tags=["auth"])
def reset_password(user_id: int, data: ResetPasswordRequest):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password = hash_password(data.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Password updated successfully"}
