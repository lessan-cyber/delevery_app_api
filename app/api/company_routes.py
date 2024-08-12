from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.company_cruds import create_company, update_company, delete_company
from app.schemas import UserCreate, CompanyProfileCreate, CompanyResponse, UserUpdate, CompanyProfileUpdate
from app.db import get_db, delete_access_token
from app.models.user_models import CompanyProfile, User
from app.utils import validate_user , get_user_response, log , validate_company_inputs_on_update
from ..core.auth import get_current_user

router = APIRouter(
    prefix="/companies",
    tags=['companies']
)

@router.post("/", response_model = CompanyResponse) 
def register_company(user_in: UserCreate, company_in: CompanyProfileCreate, db: Session = Depends(get_db,)):   
    validate_user(db, user_in) 
    if db.query(CompanyProfile).filter(CompanyProfile.company_name == company_in.company_name).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company name already exists")

    if db.query(CompanyProfile).filter(CompanyProfile.company_id == company_in.company_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company id already exists")
    
    try:
        user = create_company(db, user_in, company_in)
        company_profile = db.query(CompanyProfile).filter(CompanyProfile.user_id == user.id).first()
        user_response = get_user_response(user)
        return {
            "user": user_response,
            "company_name":company_profile.company_name,
            "business_type": company_profile.business_type,
            "company_id": company_profile.company_id,
            "address": company_profile.address,
        }
    except Exception as e:
            log.info(f"Error creating company: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

@router.put("/update/{company_id}",response_model= CompanyResponse, status_code=status.HTTP_200_OK)    
async def update_company_profile(user_update: UserUpdate, company_update: CompanyProfileUpdate, db: Session = Depends(get_db), current_user= Depends(get_current_user)):
    company_profile_old = db.query(CompanyProfile).filter(CompanyProfile.user_id == current_user.id).first()
    if not company_profile_old:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company profile not found")
    company_old = db.query(User).filter(User.id == current_user.id).first()
    if not company_old:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    validate_company_inputs_on_update(db, current_user.id, user_update, company_update)
    
    try:
        user = update_company(db, current_user.id, user_update, company_update)
        company_profile = db.query(CompanyProfile).filter(CompanyProfile.user_id == user.id).first()
        user_response = get_user_response(user)
        await delete_access_token(current_user.id)
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
async def delete_company_profile(db: Session = Depends(get_db), current_user= Depends(get_current_user)):
    existing_profile = db.query(CompanyProfile).filter(CompanyProfile.user_id == current_user.id).first()
    if not existing_profile:
        raise HTTPException(status_code=404, detail="Company profile not found")
    company = db.query(User).filter(User.id == current_user.id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    try:
        await delete_company(db, company, existing_profile)
        return {"detail": "Company deleted successfully"}
    except Exception as e:
        log.info(f"Error deleting company: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))