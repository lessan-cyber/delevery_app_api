from pydantic import BaseModel
from typing import Optional
from .base import TimestampModel
from .users_schemas import User, UserResponse

class CustomerProfileBase(BaseModel):
    default_address: Optional[str] = None

class CustomerProfileCreate(CustomerProfileBase):
    pass

class CustomerProfileUpdate(CustomerProfileBase):
    pass

class CustomerProfileInDB(CustomerProfileBase, TimestampModel):
    user_id: int

class CustomerProfile(CustomerProfileInDB):
    user: User

    class Config:
        from_attribute = True

class CustomerResponse(BaseModel):
    user: UserResponse
    default_address: str
    class Config:
        orm_mode = True

class DriverProfileBase(BaseModel):
    license_number: str
    vehicle_type: str
    is_verified: bool = False

class DriverProfileCreate(DriverProfileBase):
    pass

class DriverProfileUpdate(DriverProfileBase):
    license_number: Optional[str] = None
    vehicle_type: Optional[str] = None
    is_verified: Optional[bool] = None

class DriverProfileInDB(DriverProfileBase, TimestampModel):
    user_id: int

class DriverProfile(DriverProfileInDB):
    user: User

    class Config:
        orm_mode = True

class DriverResponse(BaseModel):
    user: UserResponse
    license_number: str
    vehicle_type: str
    is_verified: bool
    class Config:
        from_attributes = True
class CompanyProfileBase(BaseModel):
    company_name: str
    business_type: Optional[str] = None
    company_id: str
    address: str

class CompanyProfileCreate(CompanyProfileBase):
    pass

class CompanyProfileUpdate(CompanyProfileBase):
    company_name: Optional[str] = None
    business_type: Optional[str] = None
    company_id: Optional[str] = None
    address: Optional[str] = None

class CompanyProfileInDB(CompanyProfileBase, TimestampModel):
    user_id: int

class CompanyResponse(BaseModel):
    user: UserResponse
    company_name: str
    business_type: str
    company_id: Optional[str] = None
    address: str
    class Config:
        from_attributes = True

class CompanyProfile(CompanyProfileInDB):
    user: User

    class Config:
        from_attributes = True