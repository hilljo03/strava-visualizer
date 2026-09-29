import json
from pathlib import Path
from sqlalchemy import Connection, select
from src.dependencies import get_db


import requests

ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"
PER_PAGE = 30

DATABASE_URL = "sqlite:///./test.db"



def get_access_token(user_id: int, database):
    query = select(users).where(users.c.id == user_id)
    row = db.execute(query).mappings().first().mapped()['strava_access_token']

    return access_token


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

def get_variables(act):

    row = {}

    row['strava_athlete_id'] = act['athlete']['id']
    row['activity'] = act['type']
    row['start_date_local'] = row['start_date_local']
    row['start_lat'] = act['start_latlng'][0]
    row['start_long'] = act['start_latlng'][1]
    row['avg_heartrate'] = act['average_heartrate']
    row['max_heartrate'] = act['max_heartrate']
    row['suffer_score'] = act['suffer_score']
    row['polyline'] = act['map']['summary_polyline']

    return row

def process_all_activities(all_activities, selected_activities = ['Run', 'Workout', 'Bike']):

    filtered_activities = [activity for activity in all_activities if activity['type'] in selected_activities]

    processed = [get_variables]


if __name__ == "__main__":

    access_token = get_access_token(USER_ID)

    activities = fetch_all_activities(access_token)


    print(f"total activities: {len(activities)}")
    print(f"wrote {OUTPUT_PATH}")
    print("first 30:")
    for activity in activities[:30]:
        print(f"  {activity.get('start_date')}  {activity.get('type')}  {activity.get('name')}")


VARS_TO_KEEP = [athlete id
start time
Activity
start lat long
average heart rate
max heartrate
suffer score
polyline
]

