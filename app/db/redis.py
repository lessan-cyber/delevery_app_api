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
            
async def store_access_token(user_id: int , token: str, expiration: int, type: str):
    try:
        await redis_client.set(f"{type}:{user_id}", token, ex=expiration)
        log.info(f"{type} for user {user_id} stored successfully")
    except Exception as e:
        log.info(f"Failed to store {type}: {e}")

async def get_access_token(user_id: int, type: str):
    try:
        token = await redis_client.get(f"{type}:{user_id}")
        return token
    except Exception as e:
        log.info(f"Failed to retrieve {type}: {e}")
        return None

async def delete_access_token(user_id:int, type: str):

    try:
        is_token_deleted = await redis_client.delete(f"{type}:{user_id}")
        if is_token_deleted:
            log.info(f"{type} for user {user_id} deleted successfully")
        else:
            log.info(f"{type} for user {user_id} not found")
    except Exception as e:
        log.info(f"Failed to delete {type}: {e}")

async def store_exchange_rate(exchange):
    pass
    try:
        await redis_client.set("exchange_rate", exchange)
        log.info("Exchange rate stored successfully")
    except Exception as e:
        log.info(f"Failed to store exchange rate: {e}")