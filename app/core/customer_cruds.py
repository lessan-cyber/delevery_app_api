from app.models.user_models import User, CustomerProfile
from sqlalchemy.orm import Session 
from app.schemas import UserCreate, CustomerProfileCreate
from app.utils import hash_password
from datetime import datetime  
from ..db.redis import delete_access_token

async def create_customer(db: Session, user_in: UserCreate, customer_profile_in: CustomerProfileCreate):
    customer = User(
        **user_in.model_dump(exclude_unset=True, exclude={"password"}),
        hashed_password=hash_password(user_in.password),
        role="customer",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    
    customer_profile = CustomerProfile(
        user_id=customer.id,
        default_address=customer_profile_in.default_address,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(customer_profile)
    db.commit()
    db.refresh(customer_profile)
    return customer

async def update_customer(db: Session, user_id: int, user_update, customer_profile_update):
    # Récupérer l'utilisateur existant
    existing_user = db.query(User).get(user_id)
    
    # Mettre à jour l'utilisateur
    user_update_dict = user_update.dict(exclude_unset=True) if hasattr(user_update, 'dict') else user_update
    for key, value in user_update_dict.items():
        setattr(existing_user, key, value)
    existing_user.updated_at = datetime.now()
    
    # Récupérer le profil client existant
    existing_profile = db.query(CustomerProfile).filter(CustomerProfile.user_id == user_id).first()
    
    # Mettre à jour le profil client
    profile_update_dict = customer_profile_update.dict(exclude_unset=True) if hasattr(customer_profile_update, 'dict') else customer_profile_update
    for key, value in profile_update_dict.items():
        setattr(existing_profile, key, value)
    existing_profile.updated_at = datetime.now()
    
    db.commit()
    db.refresh(existing_user)
    db.refresh(existing_profile)
    return existing_user

async def delete_customer(db: Session, customer, profile):
    await delete_access_token(user_id=customer.id, type="access_token")
    await delete_access_token(user_id=customer.id, type="refresh_token")
    db.delete(customer)
    db.delete(profile)
    db.commit()