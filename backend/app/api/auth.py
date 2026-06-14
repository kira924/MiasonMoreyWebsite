from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token
from app.core.security import create_access_token

# Initialize the router for authentication endpoints
router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if the email is already registered in the database
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash the user password
    hashed_password = pwd_context.hash(user.password)
    
    # Create a new user instance
    new_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    
    # Save the new user to the database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Find the user by email 
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # Verify user exists and password is correct
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create the JWT token
    access_token = create_access_token(data={"sub": user.email})
    
    return {"access_token": access_token, "token_type": "bearer"}