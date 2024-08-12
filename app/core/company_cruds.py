from app.models.user_models import User, CompanyProfile
from sqlalchemy.orm import Session
from app.schemas import CompanyProfileCreate, UserCreate
from app.utils import hash_password
from datetime import datetime  
from app.db import delete_access_token
def create_company(db: Session, user_in: UserCreate, customer_profile_in: CompanyProfileCreate):
    company = User(
        username=user_in.username,
        email=user_in.email,
        phone_number=user_in.phone_number,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(company)
    db.commit()
    db.refresh(company)

    company_profile = CompanyProfile(
        user_id=company.id,
        company_name=customer_profile_in.company_name,
        business_type=customer_profile_in.business_type,
        address=customer_profile_in.address,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow())
    db.add(company_profile)
    db.commit()
    db.refresh(company_profile)
    return company

def update_company(db: Session,user_id, user_update,company_update):
    # Get the existing user
    existing_user = db.query(User).get(user_id)
    
    # Update the user
    user_update_dict = user_update.dict(exclude_unset=True) if hasattr(user_update, 'dict') else user_update
    for key, value in user_update_dict.items():
        setattr(existing_user, key, value)
    existing_user.updated_at = datetime.utcnow()
    existing_profile = db.query(CompanyProfile).filter(CompanyProfile.user_id == user_id).first()
    # Update the driver profile
    profile_update_dict = company_update.dict(exclude_unset=True) if hasattr(company_update, 'dict') else company_update
    for key, value in profile_update_dict.items():
        setattr(existing_profile, key, value)
    existing_profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(existing_user)
    db.refresh(existing_profile)
    return existing_user

async def delete_company(db: Session, company, profile):
    await delete_access_token(user_id=company.id)
    db.delete(company)
    db.delete(profile)
    db.commit()