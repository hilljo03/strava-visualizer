from contextlib import asynccontextmanager

import httpx
import os
import secrets
from pathlib import Path
from urllib.parse import urlencode

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from fastapi.requests import Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import Connection, select, insert, update
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

from src.models import User, UserIn

load_dotenv()  # Must run before src imports so TOKEN_ENCRYPTION_KEY is set

from src.crypto import encrypt_token, decrypt_token
from src.database import users, create_tables
from src.dependencies import get_db

STATIC_DIR = Path(__file__).resolve().parent / "static"
DATA_DIR = Path(__file__).resolve().parent / "data"

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/callback")
# Falling back to an ephemeral secret keeps local dev working; sessions are
# invalidated on restart, so set SESSION_SECRET for anything longer-lived.
SESSION_SECRET = os.getenv("SESSION_SECRET") or secrets.token_urlsafe(32)


async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")



def save_tokens(
    db: Connection,
    athlete_id: int,
    username: str,
    access_token: str,
    refresh_token: str,
    expires_at: int,
) -> User:
    existing = db.execute(
        select(users).where(users.c.strava_athlete_id == athlete_id)
    ).first()

    token_values = {
        "strava_access_token": encrypt_token(access_token),
        "strava_refresh_token": encrypt_token(refresh_token),
        "strava_token_expires_at": expires_at,
    }

    if existing:
        db.execute(
            update(users)
            .where(users.c.strava_athlete_id == athlete_id)
            .values(**token_values)
        )
    else:
        db.execute(
            insert(users).values(
                strava_athlete_id=athlete_id,
                username=username,
                **token_values,
            )
        )
    db.commit()

    row = (
        db.execute(select(users).where(users.c.strava_athlete_id == athlete_id))
        .mappings()
        .first()
    )

    return User(
        id=row["id"],
        strava_athlete_id=row["strava_athlete_id"],
        username=row["username"],
        strava_access_token=decrypt_token(row["strava_access_token"]),
        strava_refresh_token=decrypt_token(row["strava_refresh_token"]),
        strava_token_expires_at=row["strava_token_expires_at"],
    )


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


@app.get("/login")
def login(request: Request):
    if not CLIENT_ID:
        raise HTTPException(status_code=500, detail="CLIENT_ID is not set")

    print(REDIRECT_URI)

    state = secrets.token_urlsafe(16)
    request.session["state"] = state
    params = urlencode(
        {
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "approval_prompt": "auto",
            "scope": "read,activity:read_all",
            "state": state,
        }
    )
    return RedirectResponse(
        "https://www.strava.com/oauth/authorize?" + params, status_code=302
    )


@app.get("/callback")
async def callback(
    request: Request,
    code: str = "",
    state: str = "",
    scope: str = "",
    error: str = "",
    db: Connection = Depends(get_db),
):

    if error: # or state != request.session.pop("state", None):
        raise HTTPException(400, "Authorization failed")
    if "activity:read" not in scope:
        raise HTTPException(403, "Activity access is required")

    if not CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="CLIENT_SECRET is not set")

    async with httpx.AsyncClient() as c:
        response = await c.post(
            "https://www.strava.com/api/v3/oauth/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
            },
        )

    print(response.json())
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        print(exc)
        raise HTTPException(502, "Token exchange with Strava failed")

    tok = response.json()
    save_tokens(
        db,
        athlete_id=tok["athlete"]["id"],
        username=tok["athlete"]["username"],
        access_token=tok["access_token"],
        refresh_token=tok["refresh_token"],
        expires_at=tok["expires_at"],
    )
    request.session["athlete_id"] = tok["athlete"]["id"]

    return RedirectResponse("/static/index.html")


@app.post("/users", status_code=201)
def create_user(data: UserIn, db: Connection = Depends(get_db)):
    query = insert(users).values(**data.model_dump())
    result = db.execute(query)
    db.commit()
    return {"id": result.inserted_primary_key[0]}


@app.get("/")
def read_root():
    return FileResponse(STATIC_DIR / "homepage.html")
