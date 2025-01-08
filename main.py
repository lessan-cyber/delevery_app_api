from app.db.database import test_database_connection, Base, engine
import logging
from sqlalchemy import inspect
from fastapi import FastAPI
from app.api import customer_routes, driver_routes, company_routes, user_routes, category_routes, product_routes, discount_routes
from app.db import test_redis_connection
from app.db.minio import verify_minio_connection
from contextlib import asynccontextmanager
from app.utils.currency_exchange import get_exchange_rates
from fastapi_utilities import repeat_every
# Configure logging
logging.basicConfig(level=logging.INFO)



def init_db():
    inspector = inspect(engine)
    for table_name in Base.metadata.tables.keys():
        if not inspector.has_table(table_name):
            logging.info(f"Creating table: {table_name}")
        else:
            logging.info(f"Table already exists: {table_name}")
    Base.metadata.create_all(engine)
    logging.info("Database created successfully!")


@asynccontextmanager
async def lifespan(app: FastAPI) :
    await test_redis_connection()
    await verify_minio_connection()
    await get_exchange_job()
    yield


    
app = FastAPI(debug=True, 
              lifespan=lifespan)

@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(customer_routes.router)
app.include_router(driver_routes.router)
app.include_router(company_routes.router)
app.include_router(user_routes.router)
app.include_router(category_routes.router)
app.include_router(product_routes.router)
app.include_router(discount_routes.router)
test_database_connection()  
init_db()

@repeat_every(seconds=3600) # one hour 
async def get_exchange_job():
    print("hooooooo")
    await get_exchange_rates()