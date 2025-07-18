from app.models.user_models import User, DriverProfile
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import DriverProfileCreate, UserCreate
from app.utils import hash_password
from datetime import datetime  
from ..db.redis import delete_access_token
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

async def create_driver(db: AsyncSession, driver_in: DriverProfileCreate, user_in: UserCreate):
    try:
        driver = User(
            **user_in.model_dump(exclude_unset=True, exclude={"password"}),
            hashed_password=hash_password(user_in.password),
            role="driver",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(driver)
        await db.commit()
        await db.refresh(driver)
        
        driver_profile = DriverProfile(
            user_id=driver.id,
            license_number=driver_in.license_number,
            vehicle_type=driver_in.vehicle_type,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(driver_profile)
        await db.commit()
        await db.refresh(driver_profile)
        return driver
    except IntegrityError as e:
        await db.rollback()
        msg = str(e.orig)
        if 'users_phone_number_key' in msg:
            raise Exception("Phone number already exists.")
        elif 'users_email_key' in msg:
            raise Exception("Email already exists.")
        elif 'users_username_key' in msg:
            raise Exception("Username already exists.")
        elif 'driver_profiles_license_number_key' in msg:
            raise Exception("License number already exists.")
        else:
            raise Exception("A unique constraint was violated.")

async def update_driver(db: AsyncSession, user_id: int, user_update, driver_profile_update):
    try:
        # Get the existing user
        result = await db.execute(select(User).where(User.id == user_id))
        existing_user = result.scalar_one_or_none()
        if existing_user is None:
            return None
        # Update the user
        user_update_dict = user_update.dict(exclude_unset=True) if hasattr(user_update, 'dict') else user_update
        for key, value in user_update_dict.items():
            setattr(existing_user, key, value)
        # updated_at will be set automatically by onupdate=func.now()
        result = await db.execute(select(DriverProfile).where(DriverProfile.user_id == user_id))
        existing_profile = result.scalar_one_or_none()
        if existing_profile is None:
            return None
        # Update the driver profile
        profile_update_dict = driver_profile_update.dict(exclude_unset=True) if hasattr(driver_profile_update, 'dict') else driver_profile_update
        for key, value in profile_update_dict.items():
            setattr(existing_profile, key, value)
        # updated_at will be set automatically by onupdate=func.now()
        await db.commit()
        await db.refresh(existing_user)
        await db.refresh(existing_profile)
        return existing_user
    except IntegrityError as e:
        await db.rollback()
        msg = str(e.orig)
        if 'users_phone_number_key' in msg:
            raise Exception("Phone number already exists.")
        elif 'users_email_key' in msg:
            raise Exception("Email already exists.")
        elif 'users_username_key' in msg:
            raise Exception("Username already exists.")
        elif 'driver_profiles_license_number_key' in msg:
            raise Exception("License number already exists.")
        else:
            raise Exception("A unique constraint was violated.")

async def delete_driver(db: AsyncSession, driver, profile):
    await delete_access_token(token_id=str(driver.id), type="access_token")
    await delete_access_token(token_id=str(driver.id), type="refresh_token")
    await db.delete(driver)
    await db.delete(profile)
    await db.commit()
    
