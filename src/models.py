from pydantic import BaseModel


class UserIn(BaseModel):
    username: str
    strava_athlete_id: int


class User(UserIn):
    id: int
    strava_access_token: str | None = None
    strava_refresh_token: str | None = None
    strava_token_expires_at: int | None = None
