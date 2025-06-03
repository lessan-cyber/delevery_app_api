from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user_models import User
from app.schemas.users_schemas import UserCreate
from app.utils.security import hash_password, verify_password
from fastapi import HTTPException


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: UserCreate):
    hashed_password = hash_password(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False,
        is_enterprise=False,
        preferred_currency=user.preferred_currency or "USD"
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()


async def update_user(db: AsyncSession, user_id: int, user_data: dict):
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, value in user_data.items():
        if hasattr(db_user, key):
            setattr(db_user, key, value)
    
    await db.commit()
    await db.refresh(db_user)
    return db_user 