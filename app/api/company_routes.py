from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.company_cruds import create_company, update_company, delete_company
from app.schemas import UserCreate, CompanyProfileCreate, CompanyResponse, UserUpdate, CompanyProfileUpdate
from app.db import get_db
from app.models.user_models import CompanyProfile, User
from app.utils import validate_user, get_user_response, log, validate_company_inputs_on_update
from ..core.auth import get_current_user

router = APIRouter(
    prefix="/companies",
    tags=['companies']
)


@router.post("/", response_model=CompanyResponse)
async def register_company(user_in: UserCreate, company_in: CompanyProfileCreate, db: AsyncSession = Depends(get_db)):
    await validate_user(db, user_in) if callable(getattr(validate_user, '__await__', None)) else validate_user(db, user_in)
    from sqlalchemy import select
    result = await db.execute(select(CompanyProfile).where(CompanyProfile.company_name == company_in.company_name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company name already exists")
    result = await db.execute(select(CompanyProfile).where(CompanyProfile.company_id == company_in.company_id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company id already exists")
    try:
        user = await create_company(db, user_in, company_in)
        result = await db.execute(select(CompanyProfile).where(CompanyProfile.user_id == user.id))
        company_profile = result.scalar_one_or_none()
        if not company_profile:
            raise HTTPException(status_code=500, detail="Company profile creation failed")
        user_response = await get_user_response(user)
        return {
            "user": user_response,
            "company_name": company_profile.company_name,
            "business_type": company_profile.business_type,
            "company_id": company_profile.company_id,
            "address": company_profile.address,
        }
    except Exception as e:
        log.info(f"Error creating company: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/update/{company_id}", response_model=CompanyResponse, status_code=status.HTTP_200_OK)
async def update_company_profile(user_update: UserUpdate, company_update: CompanyProfileUpdate,
                                 db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    from sqlalchemy import select
    result = await db.execute(select(CompanyProfile).where(CompanyProfile.user_id == current_user.id))
    company_profile_old = result.scalar_one_or_none()
    if not company_profile_old:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company profile not found")
    result = await db.execute(select(User).where(User.id == current_user.id))
    company_old = result.scalar_one_or_none()
    if not company_old:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    await validate_company_inputs_on_update(db, current_user.id, user_update, company_update) if callable(getattr(validate_company_inputs_on_update, '__await__', None)) else validate_company_inputs_on_update(db, current_user.id, user_update, company_update)
    try:
        user = await update_company(db, current_user.id, user_update, company_update)
        if not user:
            raise HTTPException(status_code=500, detail="Company update failed")
        result = await db.execute(select(CompanyProfile).where(CompanyProfile.user_id == user.id))
        company_profile = result.scalar_one_or_none()
        if not company_profile:
            raise HTTPException(status_code=500, detail="Company profile update failed")
        user_response = await get_user_response(user)
        return {
            "user": user_response,
            "company_name": company_profile.company_name,
            "business_type": company_profile.business_type,
            "company_id": company_profile.company_id,
            "address": company_profile.address
        }
    except Exception as e:
        log.info(f"Error updating company: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/delete/{company_id}", status_code=status.HTTP_200_OK)
async def delete_company_profile(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    from sqlalchemy import select
    result = await db.execute(select(CompanyProfile).where(CompanyProfile.user_id == current_user.id))
    existing_profile = result.scalar_one_or_none()
    if not existing_profile:
        raise HTTPException(status_code=404, detail="Company profile not found")
    result = await db.execute(select(User).where(User.id == current_user.id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    try:
        await delete_company(db, company, existing_profile)
        return {"detail": "Company deleted successfully"}
    except Exception as e:
        log.info(f"Error deleting company: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
