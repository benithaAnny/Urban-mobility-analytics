import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
LOG_DIR = ROOT / "data" / "logs"

TRIPS_FILE = Path(os.environ.get("TRIPS_FILE", RAW_DIR / "yellow_tripdata.parquet"))
ZONE_LOOKUP_FILE = Path(os.environ.get("ZONE_LOOKUP_FILE", RAW_DIR / "taxi_zone_lookup.csv"))
ZONES_GEOJSON_FILE = Path(os.environ.get("ZONES_GEOJSON_FILE", RAW_DIR / "taxi_zones.geojson"))
DB_PATH = Path(os.environ.get("MOBILITY_DB", ROOT / "database" / "mobility.db"))

# Cleaning thresholds
MIN_DURATION_MIN = 1.0     
MAX_DURATION_MIN = 300.0   
MAX_DISTANCE_MI = 100.0   
MAX_SPEED_MPH = 80.0       
MAX_FARE = 1000.0         
MAX_PASSENGERS = 6         
TOTAL_TOLERANCE = 0.05     
SAMPLE_ROWS_PER_REASON = 200

AIRPORT_ZONE_IDS = [1, 132, 138]   

# Money columns. Older files may not have all of them; missing ones become 0.
EXTRA_AMOUNT_COLUMNS = [
    "extra", "mta_tax", "tip_amount", "tolls_amount", "improvement_surcharge",
    "congestion_surcharge", "airport_fee", "cbd_congestion_fee",
]
BILL_COMPONENTS = ["fare_amount"] + EXTRA_AMOUNT_COLUMNS
MONEY_COLUMNS = BILL_COMPONENTS + ["total_amount"]

# Code tables from the TLC yellow-trip data dictionary
VENDORS = {
    1: "Creative Mobile Technologies",
    2: "Curb Mobility",
    6: "Myle Technologies",
    7: "Helix",
}
RATE_CODES = {
    1: "Standard rate", 2: "JFK", 3: "Newark", 4: "Nassau or Westchester",
    5: "Negotiated fare", 6: "Group ride", 99: "Unknown",
}
PAYMENT_TYPES = {
    0: "Flex fare", 1: "Credit card", 2: "Cash", 3: "No charge",
    4: "Dispute", 5: "Unknown", 6: "Voided trip",
}

# Time-of-day groups: (name, first hour, last hour)
TIME_BANDS = [
    ("Late night", 0, 5),
    ("Morning rush", 6, 9),
    ("Midday", 10, 15),
    ("Evening rush", 16, 19),
    ("Night", 20, 23),
]