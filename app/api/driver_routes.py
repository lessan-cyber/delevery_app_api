from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.drivers_cruds import create_driver, update_driver, delete_driver
from app.schemas import DriverProfileCreate, UserCreate, DriverResponse, UserUpdate, DriverProfileUpdate
from app.db import get_db, delete_access_token
from ..core.auth import get_current_user
from app.models.user_models import DriverProfile, User
from app.utils import validate_user, get_user_response, validate_driver_inputs_on_update

router = APIRouter(
    prefix="/drivers",
    tags=['drivers']
)

@router.post("/", response_model=DriverResponse , status_code=status.HTTP_201_CREATED)
def register_driver(user_in: UserCreate,driver_in: DriverProfileCreate, db: Session = Depends(get_db,)):
    validate_user(db, user_in)
    if db.query(DriverProfile).filter(DriverProfile.license_number == driver_in.license_number).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This license number already exists")

    try :
        driver = create_driver(db, driver_in, user_in)
        driver_profile = db.query(DriverProfile).filter(DriverProfile.user_id == driver.id).first()
        user_response = get_user_response(driver)
        return {"user": user_response, 
                "license_number": driver_profile.license_number,
                "vehicle_type": driver_profile.vehicle_type,
                "is_verified": driver_profile.is_verified
                }
    except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        

@router.put("/update/{driver_id}", response_model=DriverResponse , status_code=status.HTTP_200_OK)
async def update_driver_profile(user_update: UserUpdate, driver_update:DriverProfileUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    driver_profile_old = db.query(DriverProfile).filter(DriverProfile.user_id==current_user.id)
    if not driver_profile_old:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="Driver profile not found").first()
    driver_old = db.query(User).filter(User.id == current_user.id).first() 
    if not driver_old:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="driver not found").first() 
    validate_driver_inputs_on_update(db, current_user.id,user_update, driver_update)

    try:
        user = update_driver(db,current_user.id, user_update, driver_update)
        driver_profile = db.query(DriverProfile).filter(DriverProfile.user_id == user.id).first()
        user_response = get_user_response(user)

        await delete_access_token(current_user.id)  
        return {
            "user": user_response,
            "license_number": driver_profile.license_number,
            "vehicle_type": driver_profile.vehicle_type,
            "is_verified": driver_profile.is_verified
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/delete/{driver_id}", status_code=status.HTTP_200_OK)  
async def delete_driver_profile( db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    existing_profile = db.query(DriverProfile).filter(DriverProfile.user_id == current_user.id).first()
    if not existing_profile:
        raise HTTPException(status_code=404, detail="Driver profile not found")
    
    driver = db.query(User).filter(User.id == current_user.id).first() 
    if not driver:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="Driver not found ")
    try:
        await delete_driver(db, driver, existing_profile)
        return {"detail": "Driver deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
