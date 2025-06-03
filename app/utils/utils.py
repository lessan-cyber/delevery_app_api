from datetime import datetime, timezone
from ..schemas import UserResponse
from app.models.user_models import User
import logging


async def get_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        phone_number=user.phone_number,
        is_active=user.is_active,
        created_at=user.created_at,
        preferred_currency=user.preferred_currency,
    )


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
