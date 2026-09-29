CLIENT_ID = 249528
CLIENT_SECRET = "81ac630c8926cc5f6ed32d7b04efb25e0193bdca"

ACCESS_TOKEN = "e0fa440b879893278902dd39d3a85d786c014428"
REFRESH_TOKEN = "c22bd3d6f9e0cf1fdfcbfdee560f5c60f513175c"

import json
from pathlib import Path

import requests

TOKEN_URL = "https://www.strava.com/api/v3/oauth/token"
ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"
OUTPUT_PATH = Path(__file__).with_name("all_activities.json")
PER_PAGE = 30


def refresh_tokens(refresh_token: str) -> tuple[str, str]:
    response = requests.post(
        TOKEN_URL,
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
    )
    response.raise_for_status()
    tokens = response.json()
    return tokens["access_token"], tokens["refresh_token"]


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


if __name__ == "__main__":
    access_token, refresh_token = refresh_tokens(REFRESH_TOKEN)
    print("Access Token:", access_token)
    print("Refresh Token:", refresh_token)

    activities = fetch_all_activities(access_token)
    OUTPUT_PATH.write_text(json.dumps(activities, indent=2), encoding="utf-8")
    print(f"total activities: {len(activities)}")
    print(f"wrote {OUTPUT_PATH}")
    print("first 30:")
    for activity in activities[:30]:
        print(f"  {activity.get('start_date')}  {activity.get('type')}  {activity.get('name')}")
