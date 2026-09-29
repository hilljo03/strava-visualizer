from contextlib import asynccontextmanager

import httpx
import os
import secrets
from urllib.parse import urlencode

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from sqlalchemy import Connection, select, insert
from starlette.middleware.sessions import SessionMiddleware
from src.database import users, create_tables
from src.dependencies import get_db

# CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_ID = 249528
# CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
CLIENT_SECRET = "81ac630c8926cc5f6ed32d7b04efb25e0193bdca"
REDIRECT_URI = os.getenv("STRAVA_REDIRECT_URI", "http://localhost:8000/callback")
# Falling back to an ephemeral secret keeps local dev working; sessions are
# invalidated on restart, so set SESSION_SECRET for anything longer-lived.
SESSION_SECRET = os.getenv("SESSION_SECRET") or secrets.token_urlsafe(32)


async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)


# @app.get("/login")


# @app.get("/auth")


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


class UserIn(BaseModel):
    username: str


class User(UserIn):
    id: int


@app.get("/login")
def login(request: Request):
    if not CLIENT_ID:
        raise HTTPException(status_code=500, detail="STRAVA_CLIENT_ID is not set")

    print(REDIRECT_URI)

    state = secrets.token_urlsafe(16)
    request.session["state"] = state
    params = urlencode(
        {
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "approval_prompt": "auto",
            "scope": "read,activity:read",
            "state": state,
        }
    )
    return RedirectResponse(
        "https://www.strava.com/oauth/authorize?" + params, status_code=302
    )

@app.get("/callback")
async def callback(request: Request, code: str = "", state: str = "", scope: str = "", error: str = ""):
    if error or state != request.session.pop("state", None):
        raise HTTPException(400, "Authorization failed")
    if "activity:read" not in scope:
        raise HTTPException(403, "Activity access is required")

    if not CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="STRAVA_CLIENT_SECRET is not set")

    async with httpx.AsyncClient() as c:
        response = await c.post("https://www.strava.com/api/v3/oauth/token", data={
            "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
            "code": code, "grant_type": "authorization_code"})

    print(response.json())
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        print(exc)
        raise HTTPException(502, "Token exchange with Strava failed")

    tok = response.json()
    print(tok)
    # save_tokens(tok["athlete"]["id"], tok["access_token"],
    #             tok["refresh_token"], tok["expires_at"])  # your DB helper
    request.session["athlete_id"] = tok["athlete"]["id"]

    return RedirectResponse("/")


@app.post("/users", status_code=201)
def create_user(data: UserIn, db: Connection = Depends(get_db)):
    query = insert(users).values(**data.model_dump())
    result = db.execute(query)
    db.commit()
    return {"id": result.inserted_primary_key[0]}


@app.get("/")
def read_root():
    return {"Hello": "World"}
