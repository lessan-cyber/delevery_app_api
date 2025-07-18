from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.drivers_cruds import create_driver, update_driver, delete_driver
from app.schemas import DriverProfileCreate, UserCreate, DriverResponse, UserUpdate, DriverProfileUpdate
from app.db import get_db, delete_access_token
from ..core.auth import get_current_user
from app.models.user_models import DriverProfile, User
from app.utils import validate_user, get_user_response, validate_driver_inputs_on_update
from sqlalchemy import select
router = APIRouter(
    prefix="/drivers",
    tags=['drivers']
)

@router.post("/", response_model=DriverResponse , status_code=status.HTTP_201_CREATED)
async def register_driver(user_in: UserCreate, driver_in: DriverProfileCreate, db: AsyncSession = Depends(get_db)):
    await validate_user(db, user_in) if callable(getattr(validate_user, '__await__', None)) else validate_user(db, user_in)
    
    result = await db.execute(select(DriverProfile).where(DriverProfile.license_number == driver_in.license_number))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This license number already exists")
    try:
        driver = await create_driver(db, driver_in, user_in)
        result = await db.execute(select(DriverProfile).where(DriverProfile.user_id == driver.id))
        driver_profile = result.scalar_one_or_none()
        user_response = await get_user_response(driver)
        if not driver_profile:
            raise HTTPException(status_code=500, detail="Driver profile creation failed")
        return {"user": user_response,
                "license_number": driver_profile.license_number,
                "vehicle_type": driver_profile.vehicle_type,
                "is_verified": driver_profile.is_verified
                }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/update/{driver_id}", response_model=DriverResponse , status_code=status.HTTP_200_OK)
async def update_driver_profile(user_update: UserUpdate, driver_update: DriverProfileUpdate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    result = await db.execute(select(DriverProfile).where(DriverProfile.user_id == current_user.id))
    driver_profile_old = result.scalar_one_or_none()
    if not driver_profile_old:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver profile not found")
    result = await db.execute(select(User).where(User.id == current_user.id))
    driver_old = result.scalar_one_or_none()
    if not driver_old:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="driver not found")
    await validate_driver_inputs_on_update(db, current_user.id, user_update, driver_update) if callable(getattr(validate_driver_inputs_on_update, '__await__', None)) else validate_driver_inputs_on_update(db, current_user.id, user_update, driver_update)
    try:
        user = await update_driver(db, current_user.id, user_update, driver_update)
        if not user:
            raise HTTPException(status_code=500, detail="Driver update failed")
        result = await db.execute(select(DriverProfile).where(DriverProfile.user_id == user.id))
        driver_profile = result.scalar_one_or_none()
        if not driver_profile:
            raise HTTPException(status_code=500, detail="Driver profile update failed")
        user_response = await get_user_response(user)
        return {
            "user": user_response,
            "license_number": driver_profile.license_number,
            "vehicle_type": driver_profile.vehicle_type,
            "is_verified": driver_profile.is_verified
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/delete/{driver_id}", status_code=status.HTTP_200_OK)
async def delete_driver_profile(db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    result = await db.execute(select(DriverProfile).where(DriverProfile.user_id == current_user.id))
    existing_profile = result.scalar_one_or_none()
    if not existing_profile:
        raise HTTPException(status_code=404, detail="Driver profile not found")
    result = await db.execute(select(User).where(User.id == current_user.id))
    driver = result.scalar_one_or_none()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found ")
    try:
        await delete_driver(db, driver, existing_profile)
        return {"detail": "Driver deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
