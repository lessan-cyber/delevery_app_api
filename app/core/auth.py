# auth.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.core.user_cruds import get_user_by_email
from app.config import settings
from app.models.user_models import User
from ..db import get_db, delete_access_token, get_access_token, store_access_token
from sqlalchemy import select
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def authenticate_user(db: AsyncSession, email: str, password: str):
    user = await get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    token_type: str = "access_token"
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": token_type})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expiration)
    
    to_encode = data.copy()
    to_encode.update({
        "exp": expire,
        "type": "access_token",
        "jti": str(uuid.uuid4())
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    await store_access_token(to_encode["jti"], encoded_jwt, settings.access_token_expiration * 60)
    return encoded_jwt


async def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.refresh_token_expiration)
    
    to_encode = data.copy()
    to_encode.update({
        "exp": expire,
        "type": "refresh_token",
        "jti": str(uuid.uuid4())
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    await store_access_token(to_encode["jti"], encoded_jwt, settings.refresh_token_expiration * 60, "refresh_token")
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        print(f"Attempting to decode token with key: {settings.jwt_secret_key} and algorithm: {settings.jwt_algorithm}")
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        print(f"Decoded payload: {payload}")
        
        email: str = payload.get("sub")
        if email is None:
            print("No email in token")
            raise credentials_exception
            
        token_type: str = payload.get("type")
        if token_type != "access_token":
            print(f"Invalid token type: {token_type}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        exp: int = payload.get("exp")
        if exp is None or datetime.fromtimestamp(exp) < datetime.utcnow():
            print("Token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        jti: str = payload.get("jti")
        if jti is None:
            print("No JTI in token")
            raise credentials_exception
            
        stored_token = await get_access_token(jti)
        print(f"Stored token: {stored_token}")
        if stored_token is None:
            print("Token not found in storage")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        user = await get_user_by_email(db, email)
        if user is None:
            print(f"No user found for email: {email}")
            raise credentials_exception
            
        return user
        
    except JWTError as e:
        print(f"JWT Error: {e}")
        raise credentials_exception
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action"
        )
    return current_user


async def get_current_enterprise_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.is_enterprise:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action"
        )
    return current_user


async def store_tokens(user_id: int, access_token: str, refresh_token: str):
    # Store tokens with their unique IDs
    access_payload = jwt.decode(access_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    refresh_payload = jwt.decode(refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    
    await store_access_token(
        access_payload["jti"],
        access_token,
        expiration=settings.access_token_expiration
    )
    await store_access_token(
        refresh_payload["jti"],
        refresh_token,
        expiration=settings.refresh_token_expiration
    )


async def refresh_tokens(user_id: int, refresh_token: str):
    try:
        # Verify refresh token
        payload = jwt.decode(refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
            
        # Create new tokens
        new_access_token = await create_access_token({"sub": user_id})
        new_refresh_token = await create_refresh_token({"sub": user_id})
        
        # Store new tokens
        await store_tokens(user_id, new_access_token, new_refresh_token)
        
        # Invalidate old refresh token
        await delete_access_token(payload["jti"])
        
        return new_access_token, new_refresh_token
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )