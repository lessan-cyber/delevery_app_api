from ..schemas import UserResponse
import logging
def get_user_response(user):
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        phone_number=user.phone_number,  
        is_active=user.is_active,
        created_at=user.created_at
    )

def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("my_app_logger")


log = configure_logging()