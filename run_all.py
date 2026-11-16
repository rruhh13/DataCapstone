from pathlib import Path
import pandas as pd
from openf1 import get, to_time
from sc_openf1 import process_race

#openf1 starts in 2023
YEARS = [2023, 2024, 2025, 2026]

OUT_DIR = Path(__file__).resolve().parent / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

#skip races from the last day, their data might not be complete yet
cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=1)

all_sc = []
all_impact = []
log = []

for year in YEARS:
    #use_cache=False so new races this season show up
    races = get("sessions", use_cache=False, year=year, session_name="Race")
    if len(races) == 0:
        print(year, "no races found")
        continue

    races["date_end"] = to_time(races["date_end"])
    races = races[races["date_end"] < cutoff]
    races = races.sort_values("date_end")
    if "is_cancelled" in races.columns:
        races = races[races["is_cancelled"] != True]

    for _, race in races.iterrows():
        name = str(year) + " " + race["country_name"] + " (" + race["circuit_short_name"] + ")"
        try:
            sc, impact, rc = process_race(race)

            #only keep tables that have rows
            if len(sc) > 0:
                all_sc.append(sc)
                all_impact.append(impact)
                needs_review = (sc["validation_status"] == "review").sum()
            else:
                needs_review = 0

            log.append({"season": year, "session_key": race["session_key"], "race": name,
                        "sc_events": len(sc), "needs_review": needs_review, "status": "ok"})
            print(name + ":", len(sc), "sc")

        except Exception as e:
            #one bad race shouldnt stop the rest
            log.append({"season": year, "session_key": race["session_key"], "race": name,
                        "status": "failed: " + str(e)})
            print(name + ": FAILED", e)

sc_all = pd.concat(all_sc, ignore_index=True)
impact_all = pd.concat(all_impact, ignore_index=True)
log = pd.DataFrame(log)

sc_all.to_csv(OUT_DIR / "all_sc_events.csv", index=False)
impact_all.to_csv(OUT_DIR / "all_driver_sc_impact.csv", index=False)
log.to_csv(OUT_DIR / "run_log.csv", index=False)

#summary
ok = log[log["status"] == "ok"]
print()
print("races processed:", len(ok), "failed:", len(log) - len(ok))
print("full safety cars found:", len(sc_all))
print(sc_all["season"].value_counts().sort_index().to_string())

print("\n--- how each sc ended ---")
print(pd.crosstab(sc_all["season"], sc_all["end_type"]).to_string())

print("\n--- sc events that need review ---")
review = sc_all[sc_all["validation_status"] == "review"]
if len(review) == 0:
    print("none")
else:
    print(review[["season", "country", "sc_event_number", "deploy_lap", "end_type", "restart_lap", "flags"]].to_string(index=False))

failed = log[log["status"] != "ok"]
if len(failed) > 0:
    print("\n--- failed races ---")
    print(failed[["race", "status"]].to_string(index=False))

print("\nsaved all_sc_events.csv, all_driver_sc_impact.csv and run_log.csv to data/processed")
