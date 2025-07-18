from app.models.user_models import User, CompanyProfile
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import CompanyProfileCreate, UserCreate
from app.utils import hash_password
from datetime import datetime  
from app.db import delete_access_token
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

default_company_role = "company"

async def create_company(db: AsyncSession, user_in: UserCreate, customer_profile_in: CompanyProfileCreate):
    try:
        company = User(
            **user_in.model_dump(exclude={"password"}),
            hashed_password=hash_password(user_in.password),
            role=default_company_role,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(company)
        await db.commit()
        await db.refresh(company)

        company_profile = CompanyProfile(
            user_id=company.id,
            company_name=customer_profile_in.company_name,
            business_type=customer_profile_in.business_type,
            address=customer_profile_in.address,
            created_at=datetime.now(),
            updated_at=datetime.now())
        db.add(company_profile)
        await db.commit()
        await db.refresh(company_profile)
        return company
    except IntegrityError as e:
        await db.rollback()
        msg = str(e.orig)
        if 'company_profiles_company_name_key' in msg:
            raise Exception("Company name already exists.")
        elif 'company_profiles_company_id_key' in msg:
            raise Exception("Company ID already exists.")
        elif 'users_email_key' in msg:
            raise Exception("Email already exists.")
        elif 'users_phone_number_key' in msg:
            raise Exception("Phone number already exists.")
        elif 'users_username_key' in msg:
            raise Exception("Username already exists.")
        else:
            raise Exception("A unique constraint was violated.")

async def update_company(db: AsyncSession, user_id, user_update, company_update):
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
        result = await db.execute(select(CompanyProfile).where(CompanyProfile.user_id == user_id))
        existing_profile = result.scalar_one_or_none()
        if existing_profile is None:
            return None
        # Update the company profile
        profile_update_dict = company_update.dict(exclude_unset=True) if hasattr(company_update, 'dict') else company_update
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
        if 'company_profiles_company_name_key' in msg:
            raise Exception("Company name already exists.")
        elif 'company_profiles_company_id_key' in msg:
            raise Exception("Company ID already exists.")
        elif 'users_email_key' in msg:
            raise Exception("Email already exists.")
        elif 'users_phone_number_key' in msg:
            raise Exception("Phone number already exists.")
        elif 'users_username_key' in msg:
            raise Exception("Username already exists.")
        else:
            raise Exception("A unique constraint was violated.")

async def delete_company(db: AsyncSession, company, profile):
    await delete_access_token(token_id=str(company.id), type='access_token')
    await delete_access_token(token_id=str(company.id), type="refresh_token")
    await db.delete(company)
    await db.delete(profile)
    await db.commit()