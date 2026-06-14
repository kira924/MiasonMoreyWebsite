from sqlalchemy import Boolean, Column, Integer, String
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    # Define columns for the users table
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)