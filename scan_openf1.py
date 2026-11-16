from pathlib import Path
import pandas as pd
from openf1 import get

#season to scan
YEAR = 2024

OUT_DIR = Path(__file__).resolve().parent / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

races = get("sessions", year=YEAR, session_name="Race").sort_values("date_start")

rows = []
for _, race in races.iterrows():
    try:
        rc = get("race_control", session_key=race["session_key"])
        msg = rc["message"].astype(str).str.upper()
        is_sc = rc["category"] == "SafetyCar"
        rows.append({
            "session_key": race["session_key"],
            "country": race["country_name"],
            "circuit": race["circuit_short_name"],
            "sc": (is_sc & msg.str.contains("DEPLOYED") & ~msg.str.contains("VIRTUAL")).sum(),
            "vsc": (is_sc & msg.str.contains("VIRTUAL SAFETY CAR DEPLOYED")).sum(),
            "red": (rc["flag"] == "RED").sum(),
            "status": "ok"
        })
    except Exception as e:
        #one bad race shouldnt stop the whole season
        rows.append({"session_key": race["session_key"], "country": race["country_name"],
                     "circuit": race["circuit_short_name"], "status": f"failed: {e}"})

scan = pd.DataFrame(rows)
print(scan.to_string(index=False))

scan.to_csv(OUT_DIR / f"openf1_season_scan_{YEAR}.csv", index=False)
print(f"\nsaved openf1_season_scan_{YEAR}.csv to data/processed")
