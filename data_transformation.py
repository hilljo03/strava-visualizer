import json
from pathlib import Path
from sqlalchemy import Connection, select, MetaData, inspect, create_engine
from fastapi import Depends
from sqlalchemy.orm import Session
from src.dependencies import get_db
from src.models import Activity
from src.database import users
from src.crypto import encrypt_token, decrypt_token


import src.models
import requests

ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"
PER_PAGE = 30
DATABASE_URL = "sqlite:///./test.db"
USER_ID = 2
OUTPUT_PATH = "WOOHOO.json"


def get_access_token(user_id: int, db_path):

    engine = create_engine(db_path, echo=True)
    session = Session(engine)

    # Query specific column using the User ORM model
    query = select(users.c.strava_access_token).where(users.c.id == user_id)

    # db.scalar() returns the single column value or None
    access_token = session.scalars(query).first()

    return decrypt_token(access_token)


def fetch_activity_page(access_token: str, page: int, per_page: int = PER_PAGE) -> list:
    response = requests.get(
        ACTIVITIES_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        params={"page": page, "per_page": per_page},
    )
    response.raise_for_status()
    return response.json()


def fetch_all_activities(access_token: str, per_page: int = PER_PAGE) -> list:
    activities = []
    page = 1
    while True:
        batch = fetch_activity_page(access_token, page=page, per_page=per_page)
        print(f"page {page}: {len(batch)} activities")
        if not batch:
            break
        activities.extend(batch)
        page += 1
    return activities


def get_activities_model(act: dict[str, any]) -> Activity:
    start_latlng = act.get("start_latlng") or []
    start_lat = start_latlng[0] if len(start_latlng) > 0 else None
    start_long = start_latlng[1] if len(start_latlng) > 1 else None

    summary_polyline = act.get("map", {}).get("summary_polyline")

    return Activity(
        strava_athlete_id=act["athlete"]["id"],
        activity=act["type"],
        start_date_local=act["start_date_local"],  # Assuming ISO format string or datetime
        start_lat=start_lat,
        start_long=start_long,
        avg_heartrate=act.get("average_heartrate"),
        max_heartrate=act.get("max_heartrate"),
        suffer_score=act.get("suffer_score"),
        strava_activity_id=act.get("id"),
        polyline=summary_polyline,
    )


def process_all_activities(all_activities, selected_activities = ['Run', 'Bike']):
    filtered_activities = [activity for activity in all_activities if activity['type'] in selected_activities]
    processed = [get_activities_model(f) for f in filtered_activities]

    return processed


if __name__ == "__main__":
    access_token = get_access_token(USER_ID, DATABASE_URL)

    activities = fetch_all_activities(access_token)

    processed = process_all_activities(activities)

    with open(OUTPUT_PATH, 'w') as f:
        json.dump(activities, f)

    print(f"total activities: {len(activities)}")
    print(f"wrote {OUTPUT_PATH}")
