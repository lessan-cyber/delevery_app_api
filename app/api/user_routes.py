# main.py
from fastapi import Depends, HTTPException, status, APIRouter, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from app.models import User
from app.schemas import UserResponse
from app.db import get_db, store_access_token
from app.core.auth import authenticate_user, create_access_token, get_current_active_user, get_current_user, create_refresh_token, get_access_token
from app.db.redis import delete_access_token
from datetime import timedelta
from jose import JWTError, jwt
from ..config import settings as s
from ..utils import log
from ..db.minio import upload_file
from fastapi import Request
from ..utils.geolocaton import get_user_currency
from sqlalchemy import select
from app.core.user_cruds import create_user, get_user_by_email
from app.schemas.users_schemas import UserCreate

router = APIRouter(
    prefix="/users",
    tags=['users']
)

@router.post("/upload/")
async def upload(file: UploadFile):
    bucket_name = s.minio_bucket  
    object_name = f"products/{file.filename}"
    url = await upload_file(file, bucket_name, object_name)
    return {"url": url}

@router.post("/token", response_model=dict)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=s.access_token_expiration)
    access_token = await create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token = await create_refresh_token(data={"sub": user.email})
    await store_access_token(user.id, access_token, s.access_token_expiration, "access_token")
    await store_access_token(user.id, refresh_token, s.refresh_token_expiration, "refresh_token")
    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}

@router.post("/users/", response_model=UserResponse)
async def create_new_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    db_user = await get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )
    return await create_user(db=db, user=user)

@router.get("/users/me/", response_model=UserResponse)
async def read_users_me(
    current_user: UserResponse = Depends(get_current_active_user),
):
    return current_user

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    log.info(current_user.id)
    await delete_access_token(user_id=current_user.id, type="access_token")
    await delete_access_token(user_id=current_user.id, type="refresh_token")
    return {"message": "Logged out successfully"}

@router.post("/token/refresh", response_model=dict)
async def refresh_token(refresh_token: str, current_user = Depends(get_current_user)):
    user_id = current_user.id
    try:
        stored_refresh_token = await get_access_token(f"refresh_token:{user_id}")
        log.info(stored_refresh_token)
        if stored_refresh_token != refresh_token: 
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid refresh token")
        await delete_access_token(user_id, "access_token")
        await delete_access_token(user_id, "refresh_token")
        new_access_token = await create_access_token({"sub": user_id})
        new_refresh_token = await create_refresh_token({"sub": user_id})
        await store_access_token(user_id, new_access_token, s.access_token_expiration)
        await store_access_token(f"refresh_token:{user_id}", new_refresh_token, s.refresh_token_expiration)
        return {"access_token": new_access_token, "refresh_token": new_refresh_token}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid refresh token")

@router.post("/token/revoke", response_model=dict)
async def revoke_token(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to perform this action")
    payload = jwt.decode(current_user.access_token, s.jwt_secret_key, algorithms=[s.jwt_algorithm])
    user_name: str = payload.get("sub")
    result = await db.execute(select(User.id).filter(User.email == user_name))
    user_id = result.scalar_one_or_none()
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")
    access_token_exists = await get_access_token(user_id, "access_token")
    refresh_token_exists = await get_access_token(user_id, "refresh_token")
    if not access_token_exists and not refresh_token_exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Token has already been revoked")
    try:
        await delete_access_token(user_id, "access_token")
        await delete_access_token(user_id, "refresh_token")
        return {"detail": "Token revoked successfully"}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")

@router.get("/test")
async def test_route(request: Request):
    geo = await get_user_currency(request.headers.get('host'))
    print(request.headers.get('host'))
    print(geo)
    return {"message": "Test route works!"}

