from app.models.user_models import User, DriverProfile
from sqlalchemy.orm import Session
from app.schemas import DriverProfileCreate, UserCreate
from app.utils import hash_password
from datetime import datetime  
from ..db.redis import delete_access_token

def create_driver(db: Session, driver_in: DriverProfileCreate, user_in: UserCreate):
    driver = User(
        **user_in.model_dump(exclude_unset=True, exclude={"password"}),
        hashed_password=hash_password(user_in.password),
        role="driver",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)
    
    driver_profile = DriverProfile(
        user_id=driver.id,
        license_number=driver_in.license_number,
        vehicle_type=driver_in.vehicle_type,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(driver_profile)
    db.commit()
    db.refresh(driver_profile)
    return driver

def update_driver(db: Session, user_id: int, user_update, driver_profile_update):
    # Get the existing user
    existing_user = db.query(User).get(user_id)
    
    # Update the user
    user_update_dict = user_update.dict(exclude_unset=True) if hasattr(user_update, 'dict') else user_update
    for key, value in user_update_dict.items():
        setattr(existing_user, key, value)
    existing_user.updated_at = datetime.now()
    existing_profile = db.query(DriverProfile).filter(DriverProfile.user_id == user_id).first()
    # Update the driver profile
    profile_update_dict = driver_profile_update.dict(exclude_unset=True) if hasattr(driver_profile_update, 'dict') else driver_profile_update
    for key, value in profile_update_dict.items():
        setattr(existing_profile, key, value)
    existing_profile.updated_at = datetime.now()
    db.commit()
    db.refresh(existing_user)
    db.refresh(existing_profile)
    return existing_user

async def delete_driver(db: Session, driver, profile):
    await delete_access_token(user_id=driver.id, type="access_token")
    await delete_access_token(user_id=driver.id, type="refresh_token")
    db.delete(driver)
    db.delete(profile)
    db.commit()
    
