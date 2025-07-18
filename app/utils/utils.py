from datetime import datetime, timezone
from ..schemas import UserResponse
from app.models.user_models import User
import logging
from app.config import settings
from app.utils.security import hash_password
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession


async def get_user_response(user: User) -> UserResponse:
    # Defensive: only use instance attributes, not columns, and provide defaults for missing values
    return UserResponse(
        id=getattr(user, 'id', 0) or 0,
        username=getattr(user, 'username', '') or '',
        email=getattr(user, 'email', '') or '',
        full_name=getattr(user, 'full_name', '') or '',
        phone_number=getattr(user, 'phone_number', '') or '',
        is_active=bool(getattr(user, 'is_active', True)),
        created_at=getattr(user, 'created_at', None) or get_utc_now(),
        preferred_currency=getattr(user, 'preferred_currency', 'USD') or 'USD',
    )


async def create_original_admin(db: AsyncSession):
    """Create the original admin user if not already present."""
    required_fields = [
        settings.original_admin_username,
        settings.original_admin_email,
        settings.original_admin_phone,
        settings.original_admin_password,
        settings.original_admin_full_name,
    ]
    if not all(isinstance(f, str) and f for f in required_fields):
        log.warning("Original admin credentials are not fully set in the environment. Skipping admin creation.")
        return
    result = await db.execute(
        select(User).where(
            or_(
                User.username == settings.original_admin_username,
                User.email == settings.original_admin_email,
                User.phone_number == settings.original_admin_phone,
            )
        )
    )
    admin = result.scalar_one_or_none()
    if admin:
        log.info("Original admin already exists. Skipping creation.")
        return
    password = settings.original_admin_password
    if not isinstance(password, str):
        log.warning("Original admin password is not a string. Skipping admin creation.")
        return
    admin_user = User(
        username=str(settings.original_admin_username),
        email=str(settings.original_admin_email),
        phone_number=str(settings.original_admin_phone),
        hashed_password=hash_password(password),
        full_name=str(settings.original_admin_full_name),
        is_active=True,
        is_superuser=True,
        role="admin",
        created_at=get_utc_now(),
        updated_at=get_utc_now(),
        preferred_currency="USD"
    )
    db.add(admin_user)
    await db.commit()
    await db.refresh(admin_user)
    log.info("Original admin created: %s", admin_user.username)


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
    return logging.getLogger("my_app_logger")


log = configure_logging()


def get_utc_now():
    """Get current UTC time with timezone information"""
    return datetime.now(timezone.utc)
