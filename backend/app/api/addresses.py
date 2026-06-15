from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.address import Address
from app.models.user import User
from app.schemas.address import AddressCreate, AddressResponse, AddressUpdate
from app.api.deps import get_current_active_user

# Initialize the router for addresses
router = APIRouter(
    prefix="/api/addresses",
    tags=["Addresses"]
)

@router.post("/", response_model=AddressResponse)
def create_address(
    address: AddressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Create the address and link it to the currently logged in user
    new_address = Address(**address.model_dump(), user_id=current_user.id)
    db.add(new_address)
    db.commit()
    db.refresh(new_address)
    return new_address

@router.get("/", response_model=List[AddressResponse])
def get_user_addresses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Retrieve only the addresses belonging to the current user
    return db.query(Address).filter(Address.user_id == current_user.id).all()

@router.delete("/{address_id}")
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Find the address ensuring it belongs to the current user
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == current_user.id).first()
    
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    
    db.delete(address)
    db.commit()
    return {"message": "Address deleted successfully"}

@router.patch("/{address_id}", response_model=AddressResponse)
def update_address(
    address_id: int,
    address_in: AddressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Find the address ensuring it belongs to the current user
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == current_user.id).first()
    
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    
    # Extract only the fields that were provided in the request
    update_data = address_in.model_dump(exclude_unset=True)
    
    # Update the address model with the new values
    for field, value in update_data.items():
        setattr(address, field, value)
        
    db.commit()
    db.refresh(address)
    
    return address