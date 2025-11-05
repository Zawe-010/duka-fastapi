from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from .auth_service import hash_password, authenticate_user, create_access_token, register_user
from app.models import User, session
from pydantic import BaseModel

router = APIRouter()
db = session()

class UserRegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str

# Register endpoint with token generation
@router.post("/register")
def register(user: UserRegisterRequest):
    try:
        # Create the user
        new_user = register_user(user.full_name, user.email, user.password)
        # Generate JWT token
        token = create_access_token(new_user.email)
        # Return user info + token
        return {
            "user": {
                "id": new_user.id,
                "full_name": new_user.full_name,
                "email": new_user.email
            },
            "access_token": token,
            "token_type": "bearer"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Token endpoint (login)
@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(user.email)
    return {"access_token": access_token, "token_type": "bearer"}
