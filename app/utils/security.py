from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user_models import User, DriverProfile, CustomerProfile, CompanyProfile
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


async def validate_user(db, user_in):
    if len(user_in.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password should be at least 8 characters long",
        )

    result = await db.execute(select(User).filter(User.email == user_in.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
        )

    result = await db.execute(
        select(User).filter(
            or_(
                User.username == user_in.username,
                User.phone_number == user_in.phone_number,
            )
        )
    )
    existing_user = result.scalar_one_or_none()
    if existing_user:
        if existing_user.username == user_in.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
            )
        elif existing_user.phone_number == user_in.phone_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already exists",
            )


async def validate_driver(db, driver_in, user_in):
    await validate_user(db, user_in)

    result = await db.execute(
        select(DriverProfile).filter(
            DriverProfile.license_number == driver_in.license_number
        )
    )
    new_profile = result.scalar_one_or_none()

    if new_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="License number already exists",
        )


async def validate_user_inputs_on_update(db: AsyncSession, user_id: int, user_update):
    user_update_dict = user_update.dict(exclude_unset=True)
    print(f"Validating update for user {user_id}")
    print(f"Update data: {user_update_dict}")
    
    filters = []
    if user_update_dict.get("username"):
        filters.append(User.username == user_update_dict["username"])
    if user_update_dict.get("email"):
        filters.append(User.email == user_update_dict["email"])
    if user_update_dict.get("phone_number"):
        filters.append(User.phone_number == user_update_dict["phone_number"])
    if not filters:
        print("No fields to validate")
        return  # Nothing to check
        
    from sqlalchemy import or_, and_, select

    stmt = select(User).where(User.id != user_id, or_(*filters))
    print(f"SQL Query: {stmt}")
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        print(f"Found existing user: {existing_user.id}, {existing_user.username}, {existing_user.email}, {existing_user.phone_number}")
        if existing_user.username == user_update_dict.get("username"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
            )
        elif existing_user.email == user_update_dict.get("email"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
            )
        elif existing_user.phone_number == user_update_dict.get("phone_number"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already exists",
            )
    else:
        print("No conflicts found")


async def validate_driver_inputs_on_update(
    db: AsyncSession, user_id: int, user_update, profile_update
):
    await validate_user_inputs_on_update(db, user_id, user_update)

    profile_update_dict = profile_update.dict(exclude_unset=True)
    if "license_number" in profile_update_dict:
        stmt = select(DriverProfile).filter(
            DriverProfile.user_id != user_id,
            DriverProfile.license_number == profile_update_dict["license_number"],
        )
        result = await db.execute(stmt)
        existing_profile = result.scalar_one_or_none()

        if existing_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="License number already exists",
            )


async def validate_company_inputs_on_update(
    db: AsyncSession, user_id: int, user_update, profile_update
):
    await validate_user_inputs_on_update(db, user_id, user_update)
    profile_update_dict = profile_update.dict(exclude_unset=True)

    if "company_name" in profile_update_dict or "company_id" in profile_update_dict:
        filters = []
        if "company_name" in profile_update_dict:
            filters.append(
                CompanyProfile.company_name == profile_update_dict["company_name"]
            )
        if "company_id" in profile_update_dict:
            filters.append(
                CompanyProfile.company_id == profile_update_dict["company_id"]
            )

        stmt = select(CompanyProfile).filter(
            CompanyProfile.user_id != user_id, or_(*filters)
        )
        result = await db.execute(stmt)
        existing_profile = result.scalar_one_or_none()

        if existing_profile:
            if existing_profile.company_id == profile_update_dict.get("company_id"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Company ID already exists",
                )
            elif existing_profile.company_name == profile_update_dict.get(
                "company_name"
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Company name already exists",
                )
