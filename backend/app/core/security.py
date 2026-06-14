import os
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


# Security constants
SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"

if not SECRET_KEY:
    raise ValueError("No SECRET_KEY set for JWT generation. Check your .env file.")

ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    
    # Set token expiration time
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # Generate the JWT token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt