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
    access_token_expire_minites: int = 60 
    redis_host: str
    redis_port: int
settings = Settings()

