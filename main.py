from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import Connection, select, insert
from src.database import users, create_tables
from src.dependencies import get_db


async def lifespan(app: FastAPI):
    create_tables
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/users")
def list_users(db: Connection = Depends(get_db)):
    rows = db.execute(select(users)).mappings().all()
    return rows


@app.get("/users/{user_id}")
def get_user(user_id: int, db: Connection = Depends(get_db)):
    query = select(users).where(users.c.id == user_id)
    row = db.execute(query).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return row


@app.post("/users", status_code=201)
def create_user(data: dict, db: Connection = Depends(get_db)):
    query = insert(users).values(**data)
    result = db.execute(query)
    db.commit()
    return {"id": result.inserted_primary_key[0]}


@app.get("/")
def read_root():
    return {"Hello": "World"}
