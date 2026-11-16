import sys
from pathlib import Path
import pandas as pd
from openf1 import get, to_time

OUT_DIR = Path(__file__).resolve().parent / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def find_race(year, country):
    #session_name Race means no sprints
    races = get("sessions", year=year, country_name=country, session_name="Race")
    if len(races) != 1:
        raise ValueError("found " + str(len(races)) + " races for " + country + " " + str(year))
    return races.iloc[0]


def lap_start_time(laps, lap_no):
    #the leader starts each lap first, so take the earliest start of that lap
    starts = laps[laps["lap_number"] == lap_no]["date_start"].dropna()
    if len(starts) == 0:
        return pd.NaT
    return starts.min()


def is_red_flag(row):
    #2023-2025 use the flag column, 2026 only writes "RED FLAG - RACE SUSPENDED"
    #startswith because "CHEQUERED FLAG" has "RED FLAG" inside it
    if row["flag"] == "RED":
        return True
    return str(row["message"]).upper().startswith("RED FLAG")


def get_sc_events(rc, laps):
    #go through race control in order and keep track of the sc that is out
    #an sc starts with "SAFETY CAR DEPLOYED" and ends one of 3 ways:
    #restart = "SAFETY CAR IN THIS LAP", racing starts when the leader starts the next lap
    #red_flag = race got stopped during the sc
    #race_end = chequered flag under the sc
    rc = rc.sort_values("date").reset_index(drop=True)

    chequered = rc[rc["flag"] == "CHEQUERED"]
    if len(chequered) > 0:
        chequered_time = chequered["date"].min()
    else:
        chequered_time = pd.NaT

    last_lap = laps["lap_number"].max()
    events = []
    active = None

    for _, row in rc.iterrows():
        msg = str(row["message"]).upper()

        #2026 writes "VSC DEPLOYED", older years write "VIRTUAL SAFETY CAR DEPLOYED"
        is_vsc = "VSC" in msg or "VIRTUAL" in msg
        is_sc = row["category"] == "SafetyCar" and not is_vsc

        if is_sc and "DEPLOYED" in msg:
            if active is not None:
                active["flags"].append("duplicate sc deployed")
            elif len(events) > 0 and events[-1]["end_type"] == "restart" and row["date"] < events[-1]["end_time"]:
                #sc got sent out again before the restart happened, so its still the same sc
                active = events.pop()
                active["flags"].append("sc redeployed before restart")
                active["end_type"] = None
                active["end_time"] = pd.NaT
                active["end_message"] = None
                active["restart_lap"] = None
            else:
                active = {
                    "deployed_time": row["date"],
                    "deploy_lap": row["lap_number"],
                    "deploy_message": row["message"],
                    "end_type": None,
                    "end_time": pd.NaT,
                    "end_message": None,
                    "restart_lap": None,
                    "flags": [],
                }

        elif active is not None and is_sc and "IN THIS LAP" in msg:
            restart_lap = int(row["lap_number"]) + 1
            active["end_type"] = "restart"
            active["end_message"] = row["message"]
            active["restart_lap"] = restart_lap
            active["end_time"] = lap_start_time(laps, restart_lap)

            if pd.isna(active["end_time"]):
                if restart_lap > last_lap and pd.notna(chequered_time):
                    #sc came in on the last lap so the race ended before a restart
                    active["end_type"] = "race_end"
                    active["end_time"] = chequered_time
                    active["restart_lap"] = None
                else:
                    active["flags"].append("restart lap missing in lap data")

            events.append(active)
            active = None

        elif active is not None and is_red_flag(row):
            active["end_type"] = "red_flag"
            active["end_message"] = row["message"]
            active["end_time"] = row["date"]
            events.append(active)
            active = None

        elif active is not None and row["flag"] == "CHEQUERED":
            active["end_type"] = "race_end"
            active["end_message"] = row["message"]
            active["end_time"] = row["date"]
            events.append(active)
            active = None

    #sc was still out when the data ended
    if active is not None:
        active["end_type"] = "missing"
        active["flags"].append("no end found")
        events.append(active)

    if len(events) == 0:
        return pd.DataFrame()

    #number the events and work out the extra columns
    number = 1
    for e in events:
        e["sc_event_number"] = number
        number = number + 1

        e["end_found"] = pd.notna(e["end_time"])
        if e["end_found"]:
            e["duration_seconds"] = (e["end_time"] - e["deployed_time"]).total_seconds()
        else:
            e["duration_seconds"] = None

        if len(e["flags"]) == 0:
            e["validation_status"] = "ok"
        else:
            e["validation_status"] = "review"
        e["flags"] = "; ".join(e["flags"])

    sc = pd.DataFrame(events)
    sc["end_time"] = pd.to_datetime(sc["end_time"], utc=True)

    #same column order every time
    sc = sc[["sc_event_number", "deployed_time", "deploy_lap", "deploy_message", "flags", "end_type",
             "end_message", "restart_lap", "end_time", "end_found", "duration_seconds", "validation_status"]]
    return sc


def position_at(pos, driver, t):
    #last position update for this driver at or before time t
    p = pos[(pos["driver_number"] == driver) & (pos["date"] <= t)]
    if len(p) == 0:
        return None
    return p["position"].iloc[-1]


def driver_positions(sc_row, laps, pos, pits, drivers, results):
    start = sc_row["deployed_time"]
    end = sc_row["end_time"]

    #only normal restarts get a before vs after comparison
    is_restart = sc_row["end_type"] == "restart" and pd.notna(end)

    #after = end of the first racing lap = when the leader starts the lap after the restart
    if is_restart:
        after_time = lap_start_time(laps, sc_row["restart_lap"] + 1)
    else:
        after_time = pd.NaT

    rows = []
    for _, d in drivers.iterrows():
        driver = d["driver_number"]
        d_laps = laps[laps["driver_number"] == driver]
        d_pits = pits[pits["driver_number"] == driver]
        res = results[results["driver_number"] == driver]

        before = position_at(pos, driver, start)
        if pd.notna(after_time):
            after = position_at(pos, driver, after_time)
        else:
            after = None

        #pitted if they came in while the sc was out
        pitted = False
        if pd.notna(end):
            in_window = (d_pits["date"] >= start) & (d_pits["date"] <= end)
            pitted = bool(in_window.any())

        #a driver is still running if they started a lap after that time
        running_at_start = (d_laps["date_start"] > start).any()
        if pd.notna(end):
            running_after = (d_laps["date_start"] > end).any()
        else:
            running_after = False

        #why this driver cant be compared, None means they can
        if not is_restart:
            reason = "sc ended by " + sc_row["end_type"]
        elif pd.isna(after_time):
            reason = "no lap after restart"
        elif not running_at_start:
            #this includes the drivers whose crash brought the sc out
            reason = "out at or before sc start"
        elif not running_after:
            reason = "retired during sc"
        elif before is None or after is None:
            reason = "missing position"
        else:
            reason = None

        status = "finished"
        finish = None
        if len(res) > 0:
            finish = res["position"].iloc[0]
            if res["dsq"].iloc[0]:
                status = "dsq"
            elif res["dns"].iloc[0]:
                status = "dns"
            elif res["dnf"].iloc[0]:
                status = "dnf"

        if reason is None:
            position_after = after
            gain = before - after
        else:
            position_after = None
            gain = None

        rows.append({
            "sc_event_number": sc_row["sc_event_number"],
            "driver_number": driver,
            "driver": d["name_acronym"],
            "team": d["team_name"],
            "position_before": before,
            "position_after": position_after,
            "position_gain": gain,
            "pitted_during_sc": pitted,
            "finish_position": finish,
            "race_status": status,
            "eligible_for_position_comparison": reason is None,
            "exclusion_reason": reason,
        })

    return rows


def process_race(race):
    #all the data for one race, gets saved to data/raw/openf1 the first time
    key = race["session_key"]
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
    if len(pits) > 0:
        pits["date"] = to_time(pits["date"])
    else:
        pits = pd.DataFrame(columns=["driver_number", "date"])

    sc = get_sc_events(rc, laps)
    if len(sc) == 0:
        return sc, pd.DataFrame(), rc

    all_rows = []
    for _, sc_row in sc.iterrows():
        all_rows = all_rows + driver_positions(sc_row, laps, pos, pits, drivers, results)
    impact = pd.DataFrame(all_rows)

    #race info on both tables
    for table in [sc, impact]:
        table.insert(0, "season", race["year"])
        table.insert(1, "session_key", key)
        table.insert(2, "country", race["country_name"])
        table.insert(3, "circuit", race["circuit_short_name"])
    sc["source"] = "openf1"

    return sc, impact, rc


#this part only runs when i run this file myself, not when run_all.py uses it
if __name__ == "__main__":
    #python sc_openf1.py Qatar 2024, or nothing for canada 2024
    country = "Canada"
    year = 2024
    if len(sys.argv) > 1:
        country = sys.argv[1]
    if len(sys.argv) > 2:
        year = int(sys.argv[2])

    race = find_race(year, country)
    print()
    print(year, race["country_name"], race["circuit_short_name"], "session_key", race["session_key"])

    sc, impact, rc = process_race(race)

    #raw sc and red flag messages to check the matching
    check = rc[(rc["category"] == "SafetyCar") | (rc["flag"] == "RED")]
    print("\n--- safety car / red flag messages ---")
    print(check[["date", "lap_number", "category", "flag", "message"]].to_string(index=False))

    if len(sc) == 0:
        print("\nno full safety car in this race")
    else:
        print("\nfull safety cars:", len(sc))
        print(sc[["sc_event_number", "deploy_lap", "end_type", "restart_lap", "duration_seconds",
                  "validation_status", "flags"]].to_string(index=False))

        show = ["driver", "team", "position_before", "position_after", "position_gain",
                "pitted_during_sc", "finish_position", "exclusion_reason"]
        for num in sc["sc_event_number"]:
            print("\n--- sc", num, "---")
            one = impact[impact["sc_event_number"] == num]
            print(one.sort_values("position_gain", ascending=False)[show].to_string(index=False))

        tag = str(year) + "_" + country.replace(" ", "_").lower()
        sc.to_csv(OUT_DIR / ("openf1_sc_events_" + tag + ".csv"), index=False)
        impact.to_csv(OUT_DIR / ("openf1_driver_sc_impact_" + tag + ".csv"), index=False)
        print("\nsaved to data/processed")
