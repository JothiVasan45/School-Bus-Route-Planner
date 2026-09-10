"""
CLI script to generate realistic synthetic dataset for School-Bus Route Planner.
Exports to CSV and JSON formats in data/synthetic and data/cleaned.
"""
import os
import sys
import json
import pandas as pd

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.services.data_generator import data_generator

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    synthetic_dir = os.path.join(root_dir, "data", "synthetic")
    cleaned_dir = os.path.join(root_dir, "data", "cleaned")
    raw_dir = os.path.join(root_dir, "data", "raw")

    for d in [synthetic_dir, cleaned_dir, raw_dir]:
        os.makedirs(d, exist_ok=True)

    print("Generating full synthetic dataset (75 stops, 350 students, 10 buses, 10 drivers)...")
    dataset = data_generator.generate_all(
        n_stops=75,
        n_students=350,
        n_buses=10,
        n_drivers=10,
        seed=42
    )

    # Save stops CSV & JSON
    df_stops = pd.DataFrame(dataset["stops"])
    df_stops.to_csv(os.path.join(synthetic_dir, "stops.csv"), index=False)
    df_stops.to_csv(os.path.join(cleaned_dir, "stops.csv"), index=False)

    # Save students CSV & JSON
    df_students = pd.DataFrame(dataset["students"])
    df_students.to_csv(os.path.join(synthetic_dir, "students.csv"), index=False)
    df_students.to_csv(os.path.join(cleaned_dir, "students.csv"), index=False)

    # Save buses CSV & JSON
    df_buses = pd.DataFrame(dataset["buses"])
    df_buses.to_csv(os.path.join(synthetic_dir, "buses.csv"), index=False)
    df_buses.to_csv(os.path.join(cleaned_dir, "buses.csv"), index=False)

    # Save drivers CSV & JSON
    df_drivers = pd.DataFrame(dataset["drivers"])
    df_drivers.to_csv(os.path.join(synthetic_dir, "drivers.csv"), index=False)
    df_drivers.to_csv(os.path.join(cleaned_dir, "drivers.csv"), index=False)

    # Save travel times CSV & JSON
    df_tt = pd.DataFrame(dataset["travel_times"])
    df_tt.to_csv(os.path.join(synthetic_dir, "travel_times.csv"), index=False)
    df_tt.to_csv(os.path.join(cleaned_dir, "travel_times.csv"), index=False)

    # Save complete JSON bundle
    with open(os.path.join(synthetic_dir, "full_dataset.json"), "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    print(f"Dataset generated successfully!")
    print(f"  Stops: {len(df_stops)} rows -> {synthetic_dir}/stops.csv")
    print(f"  Students: {len(df_students)} rows -> {synthetic_dir}/students.csv")
    print(f"  Buses: {len(df_buses)} rows -> {synthetic_dir}/buses.csv")
    print(f"  Drivers: {len(df_drivers)} rows -> {synthetic_dir}/drivers.csv")
    print(f"  Travel-time pairs: {len(df_tt)} rows -> {synthetic_dir}/travel_times.csv")
    print(f"  Full JSON: {synthetic_dir}/full_dataset.json")

if __name__ == "__main__":
    main()
