import os 
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

BREVO_SMTP_USERNAME = os.getenv("BREVO_SMTP_USERNAME")
BREVO_SMTP_PASSWORD = os.getenv("BREVO_SMTP_PASSWORD")
BREVO_SMTP_SERVER = os.getenv("BREVO_SMTP_SERVER")
BREVO_SMTP_PORT = os.getenv("BREVO_SMTP_PORT")

AT_USERNAME = os.getenv("AT_USERNAME")
AT_API_KEY = os.getenv("AT_API_KEY")