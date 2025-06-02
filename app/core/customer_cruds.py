from app.models.user_models import User, CustomerProfile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import UserCreate, CustomerProfileCreate
from app.utils import hash_password
from datetime import datetime
from ..db.redis import delete_access_token
from ..utils.currency_exchange import supported_currencies


async def create_customer(
    db: AsyncSession, user_in: UserCreate, customer_profile_in: CustomerProfileCreate
):
    # Create the user first with preferred currency
    customer = User(
        **user_in.model_dump(exclude_unset=True, exclude={"password"}),
        hashed_password=hash_password(user_in.password),
        role="customer",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        preferred_currency=customer_profile_in.preferred_currency or "USD",
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
    return customer


async def update_customer(
    db: AsyncSession, user_id: int, user_update, customer_profile_update
):
    # Récupérer l'utilisateur existant
    result = await db.execute(select(User).where(User.id == user_id))
    existing_user = result.scalar_one_or_none()

    # Mettre à jour l'utilisateur
    user_update_dict = (
        user_update.dict(exclude_unset=True)
        if hasattr(user_update, "dict")
        else user_update
    )
    for key, value in user_update_dict.items():
        setattr(existing_user, key, value)
    existing_user.updated_at = datetime.now()

    # Récupérer le profil client existant
    result_profile = await db.execute(
        select(CustomerProfile).where(CustomerProfile.user_id == user_id)
    )
    existing_profile = result_profile.scalar_one_or_none()

    # Mettre à jour le profil client
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
    return existing_user


async def delete_customer(db: AsyncSession, customer, profile):
    await delete_access_token(user_id=customer.id, type="access_token")
    await delete_access_token(user_id=customer.id, type="refresh_token")
    await db.delete(customer)
    await db.delete(profile)
    await db.commit()
