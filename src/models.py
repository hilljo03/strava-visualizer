from pydantic import BaseModel


class UserIn(BaseModel):
    username: str
    strava_athlete_id: int


class User(UserIn):
    id: int
    strava_access_token: str | None = None
    strava_refresh_token: str | None = None
    strava_token_expires_at: int | None = None


class Activity(BaseModel): 
    id: Optional[int] = None
    strava_athlete_id: int
    activity: str
    start_date_local: datetime
    start_lat: Optional[float] = None
    start_long: Optional[float] = None
    avg_heartrate: Optional[float] = None
    max_heartrate: Optional[float] = None
    suffer_score: Optional[int] = None
    strava_activity_id: int
    polyline: Optional[str] = None
