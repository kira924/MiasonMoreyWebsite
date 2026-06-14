import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Retrieve database URL from environment variables
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost/maison_morey")

# Create the SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a configured session class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for our database models
Base = declarative_base()

# Dependency function to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()