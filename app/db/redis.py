"""
Async Redis utilities for token storage, currency caching, and country-currency mapping.

Uses redis.asyncio for all operations. Provides functions for storing and retrieving tokens, exchange rates, and country-currency data.
"""

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
    """Get the global async Redis client.

    Returns:
        redis.asyncio.Redis: The async Redis client instance.
    """
    return redis_client

async def test_redis_connection():
    """Test the Redis connection, retrying until successful."""
    log.info("testing redis connection ...")
    while True:
        try:
            await redis_client.ping()
            log.info("Redis connection successful ...")
            break
        except Exception as e:
            log.info(f"Failed to connect to redis: {e}")
            time.sleep(5)

async def store_access_token(token_id: str, token: str, expiration: int, type: str = "access_token"):
    """Store an access or refresh token in Redis with expiration.

    Args:
        token_id (str): The user or session identifier.
        token (str): The token value.
        expiration (int): Expiration time in seconds.
        type (str, optional): Token type ("access_token" or "refresh_token"). Defaults to "access_token".
    """
    try:
        await redis_client.set(f"{type}:{token_id}", token, ex=expiration)
        log.info(f"{type} with ID {token_id} stored successfully")
    except Exception as e:
        log.info(f"Failed to store {type}: {e}")

async def get_access_token(token_id: str, type: str = "access_token"):
    """Retrieve an access or refresh token from Redis.

    Args:
        token_id (str): The user or session identifier.
        type (str, optional): Token type. Defaults to "access_token".

    Returns:
        str or None: The token value, or None if not found.
    """
    try:
        token = await redis_client.get(f"{type}:{token_id}")
        return token
    except Exception as e:
        log.info(f"Failed to retrieve {type}: {e}")
        return None

async def delete_access_token(token_id: str, type: str = "access_token"):
    """Delete an access or refresh token from Redis.

    Args:
        token_id (str): The user or session identifier.
        type (str, optional): Token type. Defaults to "access_token".
    """
    try:
        is_token_deleted = await redis_client.delete(f"{type}:{token_id}")
        if is_token_deleted:
            log.info(f"{type} with ID {token_id} deleted successfully")
        else:
            log.info(f"{type} with ID {token_id} not found")
    except Exception as e:
        log.info(f"Failed to delete {type}: {e}")

async def store_exchange_rate(exchange):
    """Store the exchange rate data in Redis.

    Args:
        exchange: The exchange rate data (should be serializable).
    """
    try:
        await redis_client.set("exchange_rate", exchange)
        log.info("Exchange rate stored successfully")
    except Exception as e:
        log.info(f"Failed to store exchange rate: {e}")

async def get_stored_exchange_rate():
    """Retrieve the stored exchange rate from Redis.

    Returns:
        The exchange rate data, or None if not found.
    """
    try :
        exchange_rate = await redis_client.get("exchange_rate")
        return exchange_rate
    except Exception as e:
        log.info(f"Failed to get stored exchange rate: {e}")

async def load_country_currency_into_redis():
    """Load country-currency mapping from a JSON file into Redis as hashes."""
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
    """Get the currency code for a given country code from Redis.

    Args:
        code (str): The country code.

    Returns:
        str: The currency code, or "USD" if not found.
    """
    try:
        currency_code = await redis_client.hget(f"country:{code}", "currencyCode")
        if currency_code:
            return currency_code
        else:
            log.info(f"No currency found for country code: {code}, using USD by default")
            return "USD"
    except Exception as e:
        log.info(f"Failed to get currency for country code {code}: {e}")
        return "USD"