import json
from pathlib import Path

FILEPATH = "sample_api_output.json"


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def filter_json(json): 

    filtered = json[json]


if __name__ == "__main__":
    activities = read_json(FILEPATH)
    print(type(activities), len(activities))
    print(activities[0]["name"], activities[0]["type"])(p)