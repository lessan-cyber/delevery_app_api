# main.py
from fastapi import  Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.models import User
from app.schemas import  UserResponse
from app.db import get_db, store_access_token
from app.core.auth import authenticate_user, create_access_token, get_current_active_user,get_current_user
from app.db.redis import delete_access_token
from datetime import timedelta
from ..utils import log
router = APIRouter(
    prefix="/users",
    tags=['users']
)

@router.post("/token", response_model=dict)
async def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(days=15)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    await store_access_token(user.id, access_token)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me/", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    log.info(current_user.id)
    await delete_access_token(user_id=current_user.id)
    return {"message": "Logged out successfully"}