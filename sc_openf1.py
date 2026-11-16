from pathlib import Path
import pandas as pd
from openf1 import get, to_time

#race to look at, change these to test other races
YEAR = 2024
COUNTRY = "Canada"

OUT_DIR = Path(__file__).resolve().parent / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def find_race(year, country):
    #sprints are called "Sprint" so this only gets the main race
    s = get("sessions", year=year, country_name=country, session_name="Race")
    if len(s) != 1:
        raise ValueError(f"found {len(s)} races for {country} {year}, need exactly 1")
    return s.iloc[0]


def lap_start_time(laps, lap_no):
    #when the leader started this lap = earliest start of that lap number
    starts = laps.loc[laps["lap_number"] == lap_no, "date_start"].dropna()
    return starts.min() if not starts.empty else pd.NaT


def get_sc_events(rc, laps):
    #same idea as the fastf1 version, go row by row and track if a sc is out
    #start = "SAFETY CAR DEPLOYED", end = "SAFETY CAR IN THIS LAP"
    #the restart is when the leader starts the next lap
    rc = rc.sort_values("date").reset_index(drop=True)
    events = []
    active = None

    for _, row in rc.iterrows():
        msg = str(row["message"]).upper()
        is_sc = row["category"] == "SafetyCar" and "VIRTUAL" not in msg

        if is_sc and "DEPLOYED" in msg:
            if active is None:
                active = {
                    "deployed_time": row["date"],
                    "deploy_lap": row["lap_number"],
                    "deploy_message": row["message"],
                    "flags": []
                }
            else:
                active["flags"].append("duplicate sc deployed")

        elif active is not None and is_sc and "IN THIS LAP" in msg:
            restart_lap = int(row["lap_number"]) + 1
            active["end_message"] = row["message"]
            active["restart_lap"] = restart_lap
            active["restart_time"] = lap_start_time(laps, restart_lap)
            if pd.isna(active["restart_time"]):
                active["flags"].append("restart lap missing in lap data")
            events.append(active)
            active = None

        elif active is not None and row["flag"] == "RED":
            active["flags"].append("red flag during sc")

    if active is not None:
        active["flags"].append("no sc in this lap found")
        events.append(active)

    sc = pd.DataFrame(events)
    if sc.empty:
        return sc

    for col in ["end_message", "restart_lap", "restart_time"]:
        if col not in sc:
            sc[col] = None
    sc["restart_time"] = pd.to_datetime(sc["restart_time"], utc=True)

    sc.insert(0, "sc_event_number", range(1, len(sc) + 1))
    sc["end_found"] = sc["restart_time"].notna()
    sc["duration_seconds"] = (sc["restart_time"] - sc["deployed_time"]).dt.total_seconds()
    sc["validation_status"] = sc["flags"].apply(lambda f: "ok" if len(f) == 0 else "review")
    sc["flags"] = sc["flags"].apply(lambda f: "; ".join(f))
    return sc


def pos_at(pos, drv, t):
    #last position update for this driver at or before time t
    p = pos[(pos["driver_number"] == drv) & (pos["date"] <= t)]
    return p["position"].iloc[-1] if not p.empty else None


def driver_positions(sc_row, laps, pos, pits, drivers, results):
    start = sc_row["deployed_time"]
    restart = sc_row["restart_time"]
    #after = end of the first racing lap, so when the leader starts the lap after the restart
    after_time = lap_start_time(laps, sc_row["restart_lap"] + 1) if pd.notna(restart) else pd.NaT
    rows = []

    for _, d in drivers.iterrows():
        drv = d["driver_number"]
        d_laps = laps[laps["driver_number"] == drv]
        res = results[results["driver_number"] == drv]
        d_pits = pits[pits["driver_number"] == drv]

        before = pos_at(pos, drv, start)
        after = pos_at(pos, drv, after_time) if pd.notna(after_time) else None

        #pitted if a pit entry happened while the sc was out
        pitted = bool(((d_pits["date"] >= start) & (d_pits["date"] <= restart)).any()) if pd.notna(restart) else False

        #running after a time = started some lap after that time
        running_at_start = (d_laps["date_start"] > start).any()
        running_after = (d_laps["date_start"] > restart).any() if pd.notna(restart) else False

        if pd.isna(after_time):
            reason = "sc end not found"
        elif not running_at_start:
            #includes drivers whose crash brought the sc out
            reason = "out at or before sc start"
        elif not running_after:
            reason = "retired during sc"
        elif before is None or after is None:
            reason = "missing position"
        else:
            reason = None

        status = "finished"
        if not res.empty:
            for s in ["dsq", "dns", "dnf"]:
                if res[s].iloc[0]:
                    status = s
                    break

        rows.append({
            "sc_event_number": sc_row["sc_event_number"],
            "driver_number": drv,
            "driver": d["name_acronym"],
            "team": d["team_name"],
            "position_before": before,
            "position_after": after if reason is None else None,
            "position_gain": before - after if reason is None else None,
            "pitted_during_sc": pitted,
            "finish_position": res["position"].iloc[0] if not res.empty else None,
            "race_status": status,
            "eligible_for_position_comparison": reason is None,
            "exclusion_reason": reason,
        })

    return rows


#pull everything for the race, saved to data/raw/openf1 the first time
race = find_race(YEAR, COUNTRY)
key = race["session_key"]
print(f"\n{YEAR} {race['country_name']} ({race['circuit_short_name']}), session_key {key}")

rc = get("race_control", session_key=key)
laps = get("laps", session_key=key)
pos = get("position", session_key=key)
pits = get("pit", session_key=key)
drivers = get("drivers", session_key=key)
results = get("session_result", session_key=key)

#text dates to real times
rc["date"] = to_time(rc["date"])
laps["date_start"] = to_time(laps["date_start"])
pos["date"] = to_time(pos["date"])
pos = pos.sort_values("date")
if not pits.empty:
    pits["date"] = to_time(pits["date"])
else:
    pits = pd.DataFrame(columns=["driver_number", "date"])

#raw sc and red flag messages so we can check the matching worked
check = rc[(rc["category"] == "SafetyCar") | (rc["flag"] == "RED")]
print("\n--- safety car / red flag messages ---")
print(check[["date", "lap_number", "category", "flag", "message"]].to_string(index=False))

sc = get_sc_events(rc, laps)

if sc.empty:
    print("\nno full safety car in this race")
else:
    sc.insert(0, "season", YEAR)
    sc.insert(1, "session_key", key)
    sc.insert(2, "event_name", race["country_name"])
    sc["source"] = "openf1"

    print(f"\nfull safety cars: {len(sc)}")
    print(sc[["sc_event_number", "deploy_lap", "restart_lap", "duration_seconds",
              "validation_status", "flags"]].to_string(index=False))

    all_rows = []
    for _, sc_row in sc.iterrows():
        all_rows.extend(driver_positions(sc_row, laps, pos, pits, drivers, results))
    impact = pd.DataFrame(all_rows)
    impact.insert(0, "season", YEAR)
    impact.insert(1, "session_key", key)

    show = ["driver", "team", "position_before", "position_after", "position_gain",
            "pitted_during_sc", "finish_position", "exclusion_reason"]
    for num, grp in impact.groupby("sc_event_number"):
        print(f"\n--- sc {num} ---")
        print(grp.sort_values("position_gain", ascending=False)[show].to_string(index=False))

    tag = f"{YEAR}_{COUNTRY.replace(' ', '_').lower()}"
    sc.to_csv(OUT_DIR / f"openf1_sc_events_{tag}.csv", index=False)
    impact.to_csv(OUT_DIR / f"openf1_driver_sc_impact_{tag}.csv", index=False)
    print(f"\nsaved openf1_sc_events_{tag}.csv and openf1_driver_sc_impact_{tag}.csv to data/processed")
