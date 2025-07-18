from app.db.database import test_database_connection, Base, engine, SessionLocal
import logging
from sqlalchemy import inspect
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utilities.timer.middleware import add_timer_middleware
import time
import asyncio
from collections import defaultdict
from app.api import (
    customer_routes,
    driver_routes,
    company_routes,
    user_routes,
    category_routes,
    product_routes,
    discount_routes,
)
from app.db import test_redis_connection, load_country_currency_into_redis
from app.db.minio import verify_minio_connection
from contextlib import asynccontextmanager
from app.utils.currency_exchange import get_exchange_rates
from fastapi_utilities import repeat_every
from app.utils.utils import create_original_admin

# Configure logging
logging.basicConfig(level=logging.INFO)


async def init_db():
    async with engine.begin() as conn:

        def check_tables(sync_conn):
            inspector = inspect(sync_conn)
            for table_name in Base.metadata.tables.keys():
                if not inspector.has_table(table_name):
                    logging.info(f"Creating table: {table_name}")
                else:
                    logging.info(f"Table already exists: {table_name}")
            Base.metadata.create_all(sync_conn)

        await conn.run_sync(check_tables)
    logging.info("Database created successfully!")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await test_redis_connection()
    await verify_minio_connection()
    await load_country_currency_into_redis()
    await init_db()
    async with SessionLocal() as db:
        await create_original_admin(db)
    await get_exchange_job()
    yield
    yield


app = FastAPI(debug=True, lifespan=lifespan)

# --- Timer Middleware (logs request processing time) ---
add_timer_middleware(app, show_avg=True)

# --- Simple Rate Limiting Middleware (per IP, per minute) ---
RATE_LIMIT = 30  # requests per minute per IP
rate_limit_data = defaultdict(lambda: {'count': 0, 'reset': time.time() + 60})

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    data = rate_limit_data[ip]
    if now > data['reset']:
        data['count'] = 0
        data['reset'] = now + 60
    data['count'] += 1
    if data['count'] > RATE_LIMIT:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Try again later."})
    response = await call_next(request)
    return response


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


app.include_router(customer_routes.router)
app.include_router(driver_routes.router)
app.include_router(company_routes.router)
app.include_router(product_routes.router)
app.include_router(discount_routes.router)
app.include_router(user_routes.router)
app.include_router(category_routes.router)
test_database_connection()
test_database_connection()


@repeat_every(seconds=3600)  # one hour
async def get_exchange_job():
    await get_exchange_rates()
    print("we are good to go")


# TODO  set up geoip2  api
# TODO  get it running for ip converting





