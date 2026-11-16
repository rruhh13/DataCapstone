import sqlite3
from pathlib import Path
import pandas as pd
from openf1 import get, to_time

#run run_all.py first, this puts its csvs into sqlite
BASE_DIR = Path(__file__).resolve().parent
PROCESSED = BASE_DIR / "data" / "processed"
SQL_DIR = BASE_DIR / "sql"
DB_DIR = BASE_DIR / "database"
DB_DIR.mkdir(exist_ok=True)
DB_FILE = DB_DIR / "f1_safety_car.db"

sc = pd.read_csv(PROCESSED / "all_sc_events.csv")
impact = pd.read_csv(PROCESSED / "all_driver_sc_impact.csv")
log = pd.read_csv(PROCESSED / "run_log.csv")

#race table, every race that worked even if it had no sc
ok_keys = log[log["status"] == "ok"]["session_key"]

season_lists = []
for season in log["season"].unique():
    season_lists.append(get("sessions", year=season, session_name="Race"))
sessions = pd.concat(season_lists)

race = sessions[sessions["session_key"].isin(ok_keys)].copy()
race["date_start"] = to_time(race["date_start"])
race = race.sort_values("date_start")

#round number = 1, 2, 3... inside each season
race["round"] = race.groupby("year").cumcount() + 1
race["race_date"] = race["date_start"].dt.strftime("%Y-%m-%d")
race = race.rename(columns={"year": "season", "country_name": "country", "circuit_short_name": "circuit"})

#how many sc in each race
sc_per_race = sc["session_key"].value_counts()
race["sc_count"] = race["session_key"].map(sc_per_race).fillna(0).astype(int)
race = race[["session_key", "season", "round", "country", "circuit", "race_date", "sc_count"]]

#sc_event table
sc_event = sc[["session_key", "sc_event_number", "deploy_lap", "deployed_time", "end_type",
               "restart_lap", "end_time", "duration_seconds", "validation_status", "flags"]].copy()

#driver_sc_impact table, sqlite wants 1/0 instead of true/false
impact = impact.rename(columns={"eligible_for_position_comparison": "eligible"})
impact["pitted_during_sc"] = impact["pitted_during_sc"].astype(int)
impact["eligible"] = impact["eligible"].astype(int)
impact = impact[["session_key", "sc_event_number", "driver_number", "driver", "team",
                 "position_before", "position_after", "position_gain", "pitted_during_sc",
                 "finish_position", "race_status", "eligible", "exclusion_reason"]]

#team colors from the saved drivers files
color_rows = []
for _, r in race.iterrows():
    drivers = get("drivers", session_key=r["session_key"])
    for _, d in drivers.iterrows():
        if pd.notna(d["team_name"]) and pd.notna(d["team_colour"]):
            color_rows.append({"season": r["season"], "team": d["team_name"],
                               "team_colour": "#" + str(d["team_colour"]).lstrip("#")})
colors = pd.DataFrame(color_rows)

#a team can show a slightly different color sometimes, keep the most common one
counts = colors.value_counts().reset_index(name="times")
counts = counts.sort_values(["season", "team", "times", "team_colour"], ascending=[True, True, False, True])
team_color = counts.drop_duplicates(["season", "team"])[["season", "team", "team_colour"]]

#make the tables from schema.sql then put the data in
con = sqlite3.connect(DB_FILE)
con.execute("pragma foreign_keys = on")
con.executescript((SQL_DIR / "schema.sql").read_text())

race.to_sql("race", con, if_exists="append", index=False)
sc_event.to_sql("sc_event", con, if_exists="append", index=False)
impact.to_sql("driver_sc_impact", con, if_exists="append", index=False)
team_color.to_sql("team_color", con, if_exists="append", index=False)

con.executescript((SQL_DIR / "views.sql").read_text())
con.commit()

#check the row counts match
print("database:", DB_FILE)
checks = [("race", len(race)), ("sc_event", len(sc_event)),
          ("driver_sc_impact", len(impact)), ("team_color", len(team_color))]
for table, expected in checks:
    n = con.execute("select count(*) from " + table).fetchone()[0]
    if n == expected:
        print(table + ":", n, "rows ok")
    else:
        print(table + ":", n, "rows, MISMATCH, csv has", expected)

bad = con.execute("pragma foreign_key_check").fetchall()
print("foreign key problems:", len(bad))
con.close()
