import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib import error as urllib_error
from urllib import request as urllib_request

ROOT = Path(__file__).resolve().parents[1]
FILE_PATH = ROOT / "data.json"
ZPID = os.environ.get("ZPID")
API_KEY = os.environ.get("DATA_API_KEY")

def load_history():
    if not FILE_PATH.exists():
        return []

    try:
        with FILE_PATH.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except (json.JSONDecodeError, OSError):
        return []

    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return payload["data"]
    return []


def read_metric(api_data, *keys):
    payload = api_data.get("data", {}) if isinstance(api_data, dict) else {}

    for key in keys:
        value = payload.get(key)
        if value is not None:
            return value

    for key in keys:
        value = api_data.get(key)
        if value is not None:
            return value

    return 0


API_URL = f"https://api.openwebninja.com/realtime-zillow-data/property-details?zpid={ZPID}"

try:
    request = urllib_request.Request(API_URL, headers={"x-api-key": API_KEY})
    with urllib_request.urlopen(request, timeout=20) as response:
        api_data = json.loads(response.read().decode("utf-8"))

    today_views = read_metric(api_data, "pageViewCount", "pageViews", "views", "totalViews")
    today_saves = read_metric(api_data, "favoriteCount", "favorites", "saves", "totalSaves")
    today_date = datetime.now().strftime("%Y-%m-%d")

    new_entry = {
        "date": today_date,
        "views": int(today_views),
        "saves": int(today_saves),
    }

    data_list = load_history()
    data_list = [entry for entry in data_list if entry.get("date") != today_date]
    data_list.append(new_entry)
    data_list.sort(key=lambda entry: entry.get("date", ""))

    with FILE_PATH.open("w", encoding="utf-8") as file:
        json.dump(data_list, file, indent=2)
        file.write("\n")

    print(f"Successfully appended data for {today_date}: Views={today_views}, Saves={today_saves}")
except (urllib_error.HTTPError, urllib_error.URLError, ValueError) as exc:
    print(f"Error executing data fetch: {exc}")
    sys.exit(1)
