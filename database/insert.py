"""Puts the cleaned data into the database tables."""
import json

from database.db import create_indexes, create_schema
from pipeline import config
from pipeline.load import centroid

TRIP_TABLE_COLUMNS = [
    "vendor_id", "pickup_datetime", "dropoff_datetime", "pu_location_id", "do_location_id",
    "passenger_count", "passenger_imputed", "trip_distance", "rate_code_id", "payment_type_id",
    "store_and_fwd", "fare_amount", "extra", "mta_tax", "tip_amount", "tolls_amount",
    "improvement_surcharge", "congestion_surcharge", "airport_fee", "cbd_congestion_fee",
    "total_amount", "duration_min", "avg_speed_mph", "fare_per_mile", "tip_pct",
    "pickup_date", "pickup_hour", "pickup_dow", "is_weekend", "time_band",
    "is_airport", "is_cross_borough", "is_suspicious",
]

def insert_lookup_tables(conn, zones, shapes, trips):
    # Give each borough and service zone a number
    borough_ids = {}
    for number, name in enumerate(sorted(zones["borough"].unique()), start=1):
        borough_ids[name] = number
    service_ids = {}
    for number, name in enumerate(sorted(zones["service_zone"].unique()), start=1):
        service_ids[name] = number

    conn.executemany("INSERT INTO boroughs VALUES (?, ?)",
                     [(number, name) for name, number in borough_ids.items()])
    conn.executemany("INSERT INTO service_zones VALUES (?, ?)",
                     [(number, name) for name, number in service_ids.items()])

    zone_rows = []
    shape_rows = []
    for zone in zones.itertuples(index=False):
        zone_id = int(zone.location_id)
        shape = shapes.get(zone_id)
        lat, lon = centroid(shape) if shape else (None, None)
        zone_rows.append((zone_id, zone.zone_name, borough_ids[zone.borough],
                          service_ids[zone.service_zone], lat, lon))
        if shape:
            shape_rows.append((zone_id, json.dumps(shape)))
    conn.executemany("INSERT INTO zones VALUES (?, ?, ?, ?, ?, ?)", zone_rows)
    conn.executemany("INSERT INTO zone_geometries VALUES (?, ?)", shape_rows)

    # Vendors: the known ones plus any other ID found in the data
    vendor_ids = set(config.VENDORS)
    for vendor_id in trips["vendor_id"].unique():
        vendor_ids.add(int(vendor_id))
    vendor_rows = [(v, config.VENDORS.get(v, "Unknown vendor")) for v in sorted(vendor_ids)]
    conn.executemany("INSERT INTO vendors VALUES (?, ?)", vendor_rows)

    conn.executemany("INSERT INTO rate_codes VALUES (?, ?)", list(config.RATE_CODES.items()))
    conn.executemany("INSERT INTO payment_types VALUES (?, ?)", list(config.PAYMENT_TYPES.items()))


def insert_trips(conn, trips):
    table = trips[TRIP_TABLE_COLUMNS].copy()
    table.insert(0, "trip_id", range(1, len(table) + 1))
    table.to_sql("trips", conn, if_exists="append", index=False, chunksize=100_000)


def insert_cleaning_log(conn, log_frame):
    rows = []
    for number, step in enumerate(log_frame.itertuples(index=False), start=1):
        rows.append((number, step.reason, int(step.record_count), step.action, step.description))
    conn.executemany("INSERT INTO cleaning_log VALUES (?, ?, ?, ?, ?)", rows)


def build_database(conn, zones, shapes, trips, log_frame):
    """Create the tables, load everything, then add indexes."""
    create_schema(conn)
    insert_lookup_tables(conn, zones, shapes, trips)
    insert_trips(conn, trips)
    insert_cleaning_log(conn, log_frame)
    conn.commit()
    create_indexes(conn)
    conn.commit()
