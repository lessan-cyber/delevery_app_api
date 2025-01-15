from pathlib import Path
import redis.asyncio as redis
from ..config import settings
import time , json
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
    try:
        await redis_client.set("exchange_rate", exchange)
        log.info("Exchange rate stored successfully")
    except Exception as e:
        log.info(f"Failed to store exchange rate: {e}")

async def get_stored_exchange_rate():
    try :
        exchange_rate = await redis_client.get("exchange_rate")
        return exchange_rate
    except Exception as e:
        log.info(f"Failed to get stored exchange rate: {e}")

async def load_country_currency_into_redis():
    try:
        project_root = Path(__file__).resolve().parent.parent.parent
        json_file_path = project_root / "country_currency.json"
        with open(json_file_path, "r") as file:
            country_data = json.load(file)
            for country in country_data.get('countries', {}).get('country', []):
                    if isinstance(country, dict):
                        key = f"country:{country['countryCode']}"
                        await redis_client.hmset(key, {
                            "countryName": country["countryName"],
                            "currencyCode": country["currencyCode"]
                        })
                    else :  
                        log.error("Invalid JSON format: Expected a list of dictionaries")
            log.info("Countries codes and currencies are loaded in redis successfully")
    except Exception as e:
        log.info(f"Failed to load country currency data into redis: {e}")


async def get_currency_by_country_code(code: str) -> str:
    try:
        country_currency = await redis_client.hmget(f"country:{code}", "currencyCode")
        if country_currency:
            return country_currency[0]  # hmget returns a list of values
        else:
            log.info(f"No currency found for country code: {code}, using USD by default")
            return "USD"
    except Exception as e:
        log.info(f"Failed to get currency for country code {code}: {e}")
        return "USD"