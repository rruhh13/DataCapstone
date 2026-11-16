import sqlite3
from pathlib import Path
import pandas as pd
from openf1 import get, to_time

#run run_all.py first, this loads its csvs into sqlite
BASE_DIR = Path(__file__).resolve().parent
PROCESSED = BASE_DIR / "data" / "processed"
SQL_DIR = BASE_DIR / "sql"
DB_DIR = BASE_DIR / "database"
DB_DIR.mkdir(exist_ok=True)
DB_FILE = DB_DIR / "f1_safety_car.db"

sc = pd.read_csv(PROCESSED / "all_sc_events.csv")
impact = pd.read_csv(PROCESSED / "all_driver_sc_impact.csv")
log = pd.read_csv(PROCESSED / "run_log.csv")

#race table: every race that processed ok, including ones with no sc
ok_keys = log.loc[log["status"] == "ok", "session_key"]
sessions = pd.concat([get("sessions", year=y, session_name="Race") for y in log["season"].unique()])
race = sessions[sessions["session_key"].isin(ok_keys)].copy()
race["date_start"] = to_time(race["date_start"])
race = race.sort_values("date_start")
race["round"] = race.groupby("year").cumcount() + 1
race["race_date"] = race["date_start"].dt.strftime("%Y-%m-%d")
race = race.rename(columns={"year": "season", "country_name": "country", "circuit_short_name": "circuit"})

counts = sc.groupby("session_key").size()
race["sc_count"] = race["session_key"].map(counts).fillna(0).astype(int)
race = race[["session_key", "season", "round", "country", "circuit", "race_date", "sc_count"]]

#sc_event table
sc_event = sc[["session_key", "sc_event_number", "deploy_lap", "deployed_time", "end_type",
               "restart_lap", "end_time", "duration_seconds", "validation_status", "flags"]].copy()

#driver_sc_impact table, true/false to 1/0 for sqlite
impact = impact.rename(columns={"eligible_for_position_comparison": "eligible"})
impact["pitted_during_sc"] = impact["pitted_during_sc"].astype(int)
impact["eligible"] = impact["eligible"].astype(int)
impact = impact[["session_key", "sc_event_number", "driver_number", "driver", "team",
                 "position_before", "position_after", "position_gain", "pitted_during_sc",
                 "finish_position", "race_status", "eligible", "exclusion_reason"]]

#build the db from the sql files then insert
con = sqlite3.connect(DB_FILE)
con.execute("pragma foreign_keys = on")
con.executescript((SQL_DIR / "schema.sql").read_text())

race.to_sql("race", con, if_exists="append", index=False)
sc_event.to_sql("sc_event", con, if_exists="append", index=False)
impact.to_sql("driver_sc_impact", con, if_exists="append", index=False)

con.executescript((SQL_DIR / "views.sql").read_text())
con.commit()

#quick check that row counts match the csvs
print(f"database: {DB_FILE}")
for table, expected in [("race", len(race)), ("sc_event", len(sc_event)), ("driver_sc_impact", len(impact))]:
    n = con.execute(f"select count(*) from {table}").fetchone()[0]
    print(f"{table}: {n} rows {'ok' if n == expected else f'MISMATCH, csv has {expected}'}")

bad_fk = con.execute("pragma foreign_key_check").fetchall()
print(f"foreign key problems: {len(bad_fk)}")
con.close()
