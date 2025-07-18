from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    postgres_db: Optional[str] = None
    postgres_host: Optional[str] = None
    postgres_port: Optional[int] = None
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    redis_host: Optional[str] = None
    redis_port: Optional[int] = None
    access_token_expiration: Optional[int] = None
    refresh_token_expiration: Optional[int] = None
    minio_access_key: Optional[str] = None
    minio_secret_key: Optional[str] = None
    minio_endpoint: Optional[str] = None
    minio_port: Optional[int] = None
    minio_use_ssl: Optional[bool] = None
    minio_bucket: Optional[str] = None
    minio_url: Optional[str] = None
    exchange_api_id: Optional[str] = None
    geoip_api_host: Optional[str] = None
    geoip_api_port: Optional[str] = None
    fake_ip: Optional[str] = None
    original_admin_username: Optional[str] = None
    original_admin_email: Optional[str] = None
    original_admin_phone: Optional[str] = None
    original_admin_password: Optional[str] = None
    original_admin_full_name: Optional[str] = None

settings = Settings()

