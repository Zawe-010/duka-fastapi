from datetime import datetime, timedelta
import jwt

SECRET_KEY = "JBL2025"
ALGORITHM = "HS256"

class JWTHandler:

    def create_token(self, email: str, expires_delta: timedelta = None):
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=60)  
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
