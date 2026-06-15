from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

class Category(Base):
    __tablename__ = "categories"

    # Define columns for the categories table
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    # Establish a relationship to the Product model
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"

    # Define columns for the products table
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Define foreign key to link with categories
    category_id = Column(Integer, ForeignKey("categories.id"))

    # Establish a relationship back to the Category model
    category = relationship("Category", back_populates="products")