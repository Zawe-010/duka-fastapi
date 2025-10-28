from models import User, session
import bcrypt
from .jwt_handler import JWTHandler
from datetime import timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

db = session()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
jwt_handler = JWTHandler()

# Hash password
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Verify password
def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def register_user(full_name: str, email: str, password: str):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise ValueError("Email already registered")

    # Hash password
    hashed = hash_password(password)

    # Create user
    new_user = User(full_name=full_name, email=email, password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Authenticate user
def authenticate_user(email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if user and verify_password(password, user.password):
        return user
    return None

# Create access token
def create_access_token(email: str, expires_minutes: int = 60):
    return jwt_handler.create_token(email, expires_delta=timedelta(minutes=expires_minutes))

# Get current user dependency
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = jwt_handler.decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
