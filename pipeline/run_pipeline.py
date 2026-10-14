"""Runs the whole pipeline: raw files -> cleaned SQLite database.

From the project folder:
    python -m pipeline.run_pipeline                    # full file
    python -m pipeline.run_pipeline --sample 300000    # quicker test run
"""
import argparse
import time
from pathlib import Path

from database.db import connect
from database.insert import build_database
from pipeline import config
from pipeline.clean import clean_trips
from pipeline.features import add_features
from pipeline.load import load_trips, load_zone_lookup, load_zone_shapes


def run(trips_path, db_path, zones_path, geojson_path, sample=None):
    start = time.time()

    def say(message):
        print(f"[{time.time() - start:6.1f}s] {message}", flush=True)

    say("Loading zones")
    zones = load_zone_lookup(zones_path)
    shapes = load_zone_shapes(geojson_path)
    say(f"  {len(zones)} zones, {len(shapes)} with shapes")

    say(f"Loading trips from {trips_path}")
    raw = load_trips(trips_path, sample)
    say(f"  {len(raw):,} rows")

    say("Cleaning")
    clean, excluded, log = clean_trips(raw, set(zones["location_id"]))
    log.write(config.LOG_DIR, excluded)
    say(f"  kept {len(clean):,}, removed {len(excluded):,} (logs in data/logs/)")

    say("Adding features")
    trips = add_features(clean, zones)

    db_path = Path(db_path)
    if db_path.exists():
        db_path.unlink()
    say(f"Writing database {db_path}")
    conn = connect(db_path)
    conn.execute("PRAGMA journal_mode = OFF")   # faster bulk loading
    conn.execute("PRAGMA synchronous = OFF")
    build_database(conn, zones, shapes, trips, log.to_frame())
    conn.close()
    say("Done")
    print(log.to_frame().to_string(index=False))


def main():
    parser = argparse.ArgumentParser(description="Build the taxi database")
    parser.add_argument("--trips", default=config.TRIPS_FILE)
    parser.add_argument("--zones", default=config.ZONE_LOOKUP_FILE)
    parser.add_argument("--geojson", default=config.ZONES_GEOJSON_FILE)
    parser.add_argument("--db", default=config.DB_PATH)
    parser.add_argument("--sample", type=int, default=None, help="use a random sample of N trips")
    args = parser.parse_args()
    run(args.trips, args.db, args.zones, args.geojson, args.sample)


if __name__ == "__main__":
    main()
