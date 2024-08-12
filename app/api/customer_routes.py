from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.customer_cruds import create_customer, update_customer , delete_customer
from ..core.auth import get_current_user
from app.schemas import UserCreate, CustomerProfileCreate, CustomerResponse , UserUpdate, CustomerProfileUpdate
from app.db import get_db
from app.models.user_models import CustomerProfile, User
from ..utils import validate_user, get_user_response, validate_user_inputs_on_update

router = APIRouter(
    prefix="/customers",
    tags=['Customers']
)

@router.post("/",response_model=CustomerResponse, status_code= status.HTTP_201_CREATED)
def register_customer(user_in: UserCreate, customer_profile_in: CustomerProfileCreate, db: Session = Depends(get_db)):
    validate_user(db, user_in) 
    try:
        user = create_customer(db, user_in, customer_profile_in)
        customer_profile = db.query(CustomerProfile).filter(CustomerProfile.user_id == user.id).first()
        profile_response = customer_profile.default_address
        user_response = get_user_response(user)
        
        return {
            "user": user_response,
            "default_address": profile_response
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/update/{customer_id}", response_model=CustomerResponse,status_code= status.HTTP_200_OK)
def update_customer_profile(user_update: UserUpdate, customer_profile_udate: CustomerProfileUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    customer = db.query(User).filter(User.id == current_user.id).first() 
    existing_profile = db.query(CustomerProfile).filter(CustomerProfile.user_id == current_user.id).first()
    if not existing_profile:
        raise HTTPException(status_code=404, detail="Customer profile not found")
    if not customer:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="Customer not found ")
    validate_user_inputs_on_update(db, current_user.id, user_update)  
    try:
        user = update_customer(db,current_user.id, user_update, customer_profile_udate)
        customer_profile = db.query(CustomerProfile).filter(CustomerProfile.user_id == user.id).first()
        profile_response = customer_profile.default_address
        user_response = get_user_response(user)

        return {
            "user": user_response,
            "default_address": profile_response
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.delete("/delete/{customer_id}", status_code=status.HTTP_200_OK)
async def delete_customer_profile( db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    existing_profile = db.query(CustomerProfile).filter(CustomerProfile.user_id == current_user.id).first()
    if not existing_profile:
        raise HTTPException(status_code=404, detail="Customer profile not found")
    customer = db.query(User).filter(User.id == current_user.id).first() 
    if not customer:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="Customer not found ")
    try:
        await delete_customer(db, customer, existing_profile)
        return {"detail": "Customer and customer profile deleted successfully", 
                "status": status.HTTP_200_OK}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

