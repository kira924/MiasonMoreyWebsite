from pydantic import BaseModel
from typing import Optional

# Base schema for address fields
class AddressBase(BaseModel):
    title: str
    city: str
    street: str
    details: Optional[str] = None
    phone_number: str

# Schema for creating a new address
class AddressCreate(AddressBase):
    pass

# Schema for returning an address in the response
class AddressResponse(AddressBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

# Schema for updating an existing address
class AddressUpdate(BaseModel):
    title: Optional[str] = None
    city: Optional[str] = None
    street: Optional[str] = None
    details: Optional[str] = None
    phone_number: Optional[str] = None