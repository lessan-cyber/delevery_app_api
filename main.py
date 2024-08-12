from app.db.database import test_database_connection, Base, engine
import logging
from sqlalchemy import inspect
from fastapi import FastAPI
from app.api import customer_routes, driver_routes, company_routes, user_routes
from app.db import test_redis_connection
# Configure logging
logging.basicConfig(level=logging.INFO)

app = FastAPI(debug=True)

def init_db():
    inspector = inspect(engine)
    for table_name in Base.metadata.tables.keys():
        if not inspector.has_table(table_name):
            logging.info(f"Creating table: {table_name}")
        else:
            logging.info(f"Table already exists: {table_name}")
    Base.metadata.create_all(engine)
    logging.info("Database created successfully!")

@app.on_event("startup")
async def startup_event():
    await test_redis_connection()
    


@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(customer_routes.router)
app.include_router(driver_routes.router)
app.include_router(company_routes.router)
app.include_router(user_routes.router)
test_database_connection()  # Ensure the database is 
# initialise the db
init_db()

# TODO implementer les roles et permision 
# TODO integrer une solution de stockage de donnée 
# TODO integrer les routes update get et delete pour les users
# TODO integrer les routes update get et delete pour les customers
# TODO integrer les routes update get et delete pour les drivers
# TODO integrer les routes update get et delete pour les companies
# TODO integrer la modification des mot de passe