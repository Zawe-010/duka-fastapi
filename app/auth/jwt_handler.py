from datetime import datetime, timedelta
import jwt
import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES=60
ACCESS_TOKEN_EXPIRE_MINUTES=int(ACCESS_TOKEN_EXPIRE_MINUTES)

class JWTHandler:

    def create_token(self, email: str, expires_delta: timedelta = None):
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  
        payload = {
            "sub": email,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token

    def decode_token(self, token: str):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except:
            return None
