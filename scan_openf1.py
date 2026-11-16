from pathlib import Path
import pandas as pd
from openf1 import get

#quick count of sc, vsc and red flags for every race in one season
YEAR = 2024

OUT_DIR = Path(__file__).resolve().parent / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

races = get("sessions", year=YEAR, session_name="Race")
races = races.sort_values("date_start")

rows = []
for _, race in races.iterrows():
    try:
        rc = get("race_control", session_key=race["session_key"])

        sc = 0
        vsc = 0
        red = 0
        for _, row in rc.iterrows():
            msg = str(row["message"]).upper()
            #2026 writes "VSC" instead of "VIRTUAL"
            is_vsc = "VSC" in msg or "VIRTUAL" in msg

            if row["category"] == "SafetyCar" and "DEPLOYED" in msg:
                if is_vsc:
                    vsc = vsc + 1
                else:
                    sc = sc + 1

            #startswith because "CHEQUERED FLAG" has "RED FLAG" inside it
            if row["flag"] == "RED" or msg.startswith("RED FLAG"):
                red = red + 1

        rows.append({"session_key": race["session_key"], "country": race["country_name"],
                     "circuit": race["circuit_short_name"], "sc": sc, "vsc": vsc, "red": red, "status": "ok"})

    except Exception as e:
        #one bad race shouldnt stop the whole season
        rows.append({"session_key": race["session_key"], "country": race["country_name"],
                     "circuit": race["circuit_short_name"], "status": "failed: " + str(e)})

scan = pd.DataFrame(rows)
print(scan.to_string(index=False))

scan.to_csv(OUT_DIR / ("openf1_season_scan_" + str(YEAR) + ".csv"), index=False)
print("\nsaved openf1_season_scan_" + str(YEAR) + ".csv to data/processed")
