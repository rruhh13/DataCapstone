import json
import time
from pathlib import Path
import pandas as pd
import requests

#openf1 has every race since 2023 for free
BASE_URL = "https://api.openf1.org/v1"

#raw files get saved here so i only download each one once
RAW_DIR = Path(__file__).resolve().parent / "data" / "raw" / "openf1"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def get(endpoint, use_cache=True, **params):
    #file name like laps_session_key-9531.json
    name = endpoint
    for key in sorted(params):
        name = name + "_" + key + "-" + str(params[key])
    raw_file = RAW_DIR / (name + ".json")

    #already downloaded, just read it
    if use_cache and raw_file.exists():
        with open(raw_file) as f:
            data = json.load(f)
        return pd.DataFrame(data)

    #try 3 times in case openf1 says too many requests
    for attempt in range(3):
        r = requests.get(BASE_URL + "/" + endpoint, params=params, timeout=30)

        #free plan is 30 requests a minute so wait after every call
        time.sleep(2.1)

        if r.status_code == 429:
            time.sleep(20)
            continue

        if r.status_code == 404:
            #404 just means nothing found
            data = []
        else:
            r.raise_for_status()
            data = r.json()

        with open(raw_file, "w") as f:
            json.dump(data, f)
        return pd.DataFrame(data)

    raise RuntimeError("openf1 kept saying too many requests for " + endpoint)


def to_time(col):
    #dates come as text, some with milliseconds and some without
    return pd.to_datetime(col, utc=True, format="ISO8601")
