from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.products import Product, Category
from app.schemas.products import ProductCreate, ProductResponse, CategoryCreate, CategoryResponse
from app.api.deps import get_current_admin_user
from app.models.user import User

# Initialize the router for products and categories
router = APIRouter(
    prefix="/api",
    tags=["Products & Categories"]
)

@router.post("/categories", response_model=CategoryResponse)
def create_category(
    category: CategoryCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Check if category name already exists
    db_category = db.query(Category).filter(Category.name == category.name).first()
    if db_category:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    new_category = Category(**category.model_dump())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    # Retrieve all categories
    return db.query(Category).all()

@router.post("/products", response_model=ProductResponse)
def create_product(
    product: ProductCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Verify that the linked category exists
    category = db.query(Category).filter(Category.id == product.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    new_product = Product(**product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@router.get("/products", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    # Retrieve all products
    return db.query(Product).all()