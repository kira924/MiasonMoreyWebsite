from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Address(Base):
    __tablename__ = "addresses"

    # Define columns for the addresses table
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    title = Column(String, nullable=False) 
    city = Column(String, nullable=False)
    street = Column(String, nullable=False)
    details = Column(String, nullable=True)
    phone_number = Column(String, nullable=False)

    # Establish relationship back to the User model
    owner = relationship("User", backref="addresses")