"""Loads the three raw files.

1. yellow_tripdata (.parquet) - one row per trip
2. taxi_zone_lookup (.csv)    - zone ID -> borough, zone name, service zone
3. taxi_zones (.geojson)      - the shape (polygon) of each zone
"""
import json
import warnings
from pathlib import Path

import pandas as pd

from . import config

# Raw column name (lower case) -> the name we use everywhere
TRIP_COLUMNS = {
    "vendorid": "vendor_id",
    "tpep_pickup_datetime": "pickup_datetime",
    "tpep_dropoff_datetime": "dropoff_datetime",
    "passenger_count": "passenger_count",
    "trip_distance": "trip_distance",
    "ratecodeid": "rate_code_id",
    "store_and_fwd_flag": "store_and_fwd_flag",
    "pulocationid": "pu_location_id",
    "dolocationid": "do_location_id",
    "payment_type": "payment_type_id",
    "fare_amount": "fare_amount",
    "extra": "extra",
    "mta_tax": "mta_tax",
    "tip_amount": "tip_amount",
    "tolls_amount": "tolls_amount",
    "improvement_surcharge": "improvement_surcharge",
    "congestion_surcharge": "congestion_surcharge",
    "airport_fee": "airport_fee",
    "cbd_congestion_fee": "cbd_congestion_fee",
    "total_amount": "total_amount",
}
REQUIRED_COLUMNS = [
    "pickup_datetime", "dropoff_datetime", "pu_location_id", "do_location_id",
    "trip_distance", "fare_amount", "total_amount",
]


def load_trips(path=config.TRIPS_FILE, sample=None):
    """Read the trips file and give every column our standard name."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Trip file not found: {path}. See README step 2.")

    df = pd.read_parquet(path)
    df.columns = [name.lower() for name in df.columns]
    df = df.rename(columns=TRIP_COLUMNS)

    missing = [name for name in REQUIRED_COLUMNS if name not in df.columns]
    if missing:
        raise ValueError(f"Trip file is missing required columns: {missing}")

    # Add any optional column this file doesn't have
    for name in TRIP_COLUMNS.values():
        if name not in df.columns:
            df[name] = 0.0 if name in config.MONEY_COLUMNS else None

    df = df[list(TRIP_COLUMNS.values())]
    if sample and sample < len(df):
        df = df.sample(n=sample, random_state=42)
    return df.reset_index(drop=True)


def load_zone_lookup(path=config.ZONE_LOOKUP_FILE):
    """Read the zone table. Blank or 'N/A' values become 'Unknown'."""
    zones = pd.read_csv(path)
    zones.columns = [name.strip().lower() for name in zones.columns]
    zones = zones.rename(columns={"locationid": "location_id", "zone": "zone_name"})
    for column in ["borough", "zone_name", "service_zone"]:
        zones[column] = zones[column].fillna("Unknown").astype(str).str.strip()
        zones[column] = zones[column].replace({"N/A": "Unknown", "": "Unknown"})
    zones["location_id"] = zones["location_id"].astype(int)
    zones = zones.drop_duplicates("location_id").sort_values("location_id")
    return zones.reset_index(drop=True)


def load_zone_shapes(path=config.ZONES_GEOJSON_FILE):
    """Return {location_id: MultiPolygon} with coordinates as longitude/latitude.

    Two things in the raw file need fixing:
    - some zones are split across several features, so we join their polygons
    - files made from the TLC shapefile use NY State Plane feet, not lon/lat,
      so we convert them
    """
    path = Path(path)
    if not path.exists():
        warnings.warn(f"{path} not found - the map will be empty. See README.")
        return {}

    with open(path, encoding="utf-8") as file:
        data = json.load(file)

    polygons_by_zone = {}
    for feature in data["features"]:
        properties = {key.lower(): value for key, value in feature["properties"].items()}
        zone_id = properties.get("locationid", properties.get("location_id"))
        geometry = feature["geometry"]
        if zone_id is None or geometry is None:
            continue
        zone_id = int(float(zone_id))
        if geometry["type"] == "Polygon":
            polygons = [geometry["coordinates"]]
        else:
            polygons = geometry["coordinates"]
        polygons_by_zone.setdefault(zone_id, []).extend(polygons)

    if polygons_by_zone and coordinates_are_in_feet(polygons_by_zone):
        polygons_by_zone = convert_to_lon_lat(polygons_by_zone)

    shapes = {}
    for zone_id, polygons in polygons_by_zone.items():
        shapes[zone_id] = {"type": "MultiPolygon", "coordinates": polygons}
    return shapes


def coordinates_are_in_feet(polygons_by_zone):
    """Longitudes are between -180 and 180; much bigger numbers mean feet."""
    first_polygon = next(iter(polygons_by_zone.values()))[0]
    first_x = first_polygon[0][0][0]
    return abs(first_x) > 180


def convert_to_lon_lat(polygons_by_zone):
    """Convert NY State Plane (EPSG:2263) coordinates to lon/lat (EPSG:4326)."""
    from pyproj import Transformer
    transformer = Transformer.from_crs("EPSG:2263", "EPSG:4326", always_xy=True)

    converted = {}
    for zone_id, polygons in polygons_by_zone.items():
        new_polygons = []
        for polygon in polygons:
            new_rings = []
            for ring in polygon:
                xs = [point[0] for point in ring]
                ys = [point[1] for point in ring]
                lons, lats = transformer.transform(xs, ys)
                new_rings.append([[round(lon, 5), round(lat, 5)] for lon, lat in zip(lons, lats)])
            new_polygons.append(new_rings)
        converted[zone_id] = new_polygons
    return converted


def centroid(shape):
    """Rough centre of a zone: the average of the points on its biggest outline."""
    outlines = [polygon[0] for polygon in shape["coordinates"] if polygon]
    if not outlines:
        return None, None
    biggest = max(outlines, key=len)
    lon = sum(point[0] for point in biggest) / len(biggest)
    lat = sum(point[1] for point in biggest) / len(biggest)
    return round(lat, 6), round(lon, 6)
