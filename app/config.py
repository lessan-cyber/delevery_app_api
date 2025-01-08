from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    redis_host: str
    redis_port: int
    access_token_expiration:int
    refresh_token_expiration:int
    minio_access_key: str
    minio_secret_key: str
    minio_endpoint: str
    minio_port: int
    minio_use_ssl: bool
    minio_bucket: str
    minio_url: str
    exchange_api_id:str


settings = Settings()

