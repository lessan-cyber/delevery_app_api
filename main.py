from fastapi import FastAPI
from app.db.database import test_database_connection

app = FastAPI()

@app.on_event("startup")
def startup_event():
    test_database_connection()

@app.get("/")
def read_root():
    return {"Hello": "World boby"}


