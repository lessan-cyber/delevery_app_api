from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import psycopg2
from psycopg2.extras import RealDictCursor
import time
from app.config import settings 
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession   


logging.basicConfig(level=logging.INFO)

SQLALCHEMY_DATABASE_URL = f'postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}'

engine = create_async_engine(SQLALCHEMY_DATABASE_URL,
                        pool_pre_ping=True,
                        pool_recycle=3600,
                        pool_size=20,
                        max_overflow=20,
                        echo=True)
Base = declarative_base()

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False,
    bind=engine,
    class_ = AsyncSession  
      )

async def init_db():
    """
    creation des tables
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_database_connection():           
    logging.info("Testing database connection...")
    while True:
        try:
            conn = psycopg2.connect(
                host=settings.postgres_host,
                database=settings.postgres_db,
                user=settings.postgres_user,
                password=settings.postgres_password,
                cursor_factory=RealDictCursor
            )
            # print sucess if it suceced
            logging.info("Database connection successful ...s")
            break  # exit the loop if successful
        except Exception as e:
            logging.info(f"Failed to connect to database: {e}")
            time.sleep(5)
        
        
        