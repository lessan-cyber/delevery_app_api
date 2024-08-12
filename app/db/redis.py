import redis.asyncio as redis
from ..config import settings
import time
from ..utils import log
redis_client = redis.from_url(
    f"redis://{settings.redis_host}:{settings.redis_port}",
    decode_responses=True
)

async def get_redis():
    return redis_client

async def test_redis_connection():
    log.info("testing redis connection ...")
    while True:
        try:
            await redis_client.ping()
            log.info("Redis connection successful ...")
            break
        except Exception as e:
            log.info(f"Failed to connect to redis: {e}")
            time.sleep(5)
            
async def store_access_token(user_id: str, token: str, expiration: int = 3600):
    try:
        await redis_client.set(f"access_token:{user_id}", token, ex=expiration)
        log.info(f"Access token for user {user_id} stored successfully")
    except Exception as e:
        log.info(f"Failed to store access token: {e}")

async def get_access_token(user_id: str):
    try:
        token = await redis_client.get(f"access_token:{user_id}")
        return token
    except Exception as e:
        log.info(f"Failed to retrieve access token: {e}")
        return None

async def delete_access_token(user_id:str):
    try:
        await redis_client.delete(f"access_token:{user_id}")
        log.info(f"Access token for user {user_id} deleted successfully")
    except Exception as e:
        log.info(f"Failed to delete access token: {e}")