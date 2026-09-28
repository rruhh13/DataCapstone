import os
import fastf1

#create a folder for downloaded F1 data
os.makedirs("f1_cache", exist_ok=True)

#use the folder as FastF1 cache
fastf1.Cache.enable_cache("f1_cache")

#load 2024 Canadian Grand Prix to try
session = fastf1.get_session(2024, "Canadian Grand Prix", "R")

print("Loading data...")
session.load(telemetry=False, weather=False)

print("\nRace loaded!")
print("Race:", session.event["EventName"])
print("Date:", session.event["EventDate"])

print("\n--- Race Results ---")
print(session.results.head())

print("\n--- Lap Data ---")
print(session.laps.head())

print("\n--- Track Status ---")
print(session.track_status.head(20))

session.track_status.to_csv("track_status_test.csv", index=False)

print("\nTrack status saved.")