import json
import time
from pathlib import Path
import pandas as pd
import requests

BASE_URL = "https://api.openf1.org/v1"
RAW_DIR = Path(__file__).resolve().parent / "data" / "raw" / "openf1"
RAW_DIR.mkdir(parents=True, exist_ok=True)

#free tier allows 30 requests a minute so wait a bit after each call
WAIT = 2.1
HEADERS = {"User-Agent": "DataCapstone-F1-SafetyCar/0.1 (student capstone)"}


def get(endpoint, **params):
    #every response gets saved as raw json so we only download it once
    name = endpoint + "_" + "_".join(f"{k}-{v}" for k, v in sorted(params.items()))
    raw_file = RAW_DIR / f"{name}.json"
    if raw_file.exists():
        return pd.DataFrame(json.loads(raw_file.read_text()))

    for attempt in range(3):
        r = requests.get(f"{BASE_URL}/{endpoint}", params=params, headers=HEADERS, timeout=30)
        time.sleep(WAIT)

        if r.status_code == 429:
            #too many requests, chill and try again
            time.sleep(20)
            continue
        if r.status_code == 404:
            #openf1 gives 404 when nothing matches
            data = []
        else:
            r.raise_for_status()
            data = r.json()

        raw_file.write_text(json.dumps(data))
        return pd.DataFrame(data)

    raise RuntimeError(f"openf1 kept rate limiting {endpoint} {params}")


def to_time(col):
    #openf1 dates are utc text, some have milliseconds and some dont
    return pd.to_datetime(col, utc=True, format="ISO8601")
