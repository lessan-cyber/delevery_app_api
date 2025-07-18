from app.models.user_models import User, CustomerProfile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import UserCreate, CustomerProfileCreate
from app.utils import hash_password
from datetime import datetime
from ..db.redis import delete_access_token
from ..utils.currency_exchange import supported_currencies
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException


async def create_customer(
    db: AsyncSession, user_in: UserCreate, customer_profile_in: CustomerProfileCreate
):
    # Create the user first with preferred currency
    customer = User(
        **user_in.model_dump(exclude_unset=True, exclude={"password", "preferred_currency"}),
        hashed_password=hash_password(user_in.password),
        role="customer",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        preferred_currency=user_in.preferred_currency or "USD"
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)

    # Create customer profile without preferred_currency
    customer_profile = CustomerProfile(
        user_id=customer.id,
        default_address=customer_profile_in.default_address,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(customer_profile)
    await db.commit()
    await db.refresh(customer_profile)
    # Eagerly load user with profile for safe async access
    user_with_profile = await get_user_with_profile(db, int(customer.id))
    return user_with_profile, customer_profile

async def update_customer(
    db: AsyncSession, user_id: int, user_update, customer_profile_update
):
    # Get the existing user
    result = await db.execute(
        select(User).options(selectinload(User.customer_profile)).where(User.id == user_id)
    )
    existing_user = result.scalar_one_or_none()
    
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update the user
    user_update_dict = (
        user_update.dict(exclude_unset=True)
        if hasattr(user_update, "dict")
        else user_update
    )
    for key, value in user_update_dict.items():
        setattr(existing_user, key, value)
    existing_user.updated_at = datetime.now()

    # Get the existing profile
    result_profile = await db.execute(
        select(CustomerProfile).where(CustomerProfile.user_id == user_id)
    )
    existing_profile = result_profile.scalar_one_or_none()

    if not existing_profile:
        raise HTTPException(status_code=404, detail="Customer profile not found")

    # Update the customer profile
    profile_update_dict = (
        customer_profile_update.dict(exclude_unset=True)
        if hasattr(customer_profile_update, "dict")
        else customer_profile_update
    )
    for key, value in profile_update_dict.items():
        setattr(existing_profile, key, value)
    existing_profile.updated_at = datetime.now()

    await db.commit()
    await db.refresh(existing_user)
    await db.refresh(existing_profile)
    
    # Eagerly reload user with profile for safe async access
    user_with_profile = await get_user_with_profile(db, user_id)
    return user_with_profile


async def delete_customer(db: AsyncSession, customer, profile):
    # Delete tokens first
    await delete_access_token(str(customer.id), "access_token")
    await delete_access_token(str(customer.id), "refresh_token")
    
    # Then delete the database records
    await db.delete(profile)
    await db.delete(customer)
    await db.commit()


async def get_user_with_profile(db: AsyncSession, some_id: int):
    result = await db.execute(
        select(User)
        .options(selectinload(User.customer_profile))
        .where(User.id == some_id)
    )
    user = result.scalar_one_or_none()
    return user
