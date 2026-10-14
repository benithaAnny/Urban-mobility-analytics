"""Adds derived features (explained in docs/REPORT.md section 1).

avg_speed_mph    - how fast the trip moved: a traffic measure
fare_per_mile    - what each mile cost
tip_pct          - tip as % of fare, card trips only (cash tips are not recorded)
time_band        - part of the day (Morning rush, Midday, ...)
is_airport       - trip to or from an airport
is_cross_borough - pickup and drop-off in different boroughs
"""
import numpy as np

from . import config


def get_time_band(hour):
    for name, first_hour, last_hour in config.TIME_BANDS:
        if first_hour <= hour <= last_hour:
            return name
    return "Unknown"


def add_features(df, zones):
    hours = df["duration_min"] / 60
    df["avg_speed_mph"] = (df["trip_distance"] / hours).round(2)
    df["fare_per_mile"] = (df["fare_amount"] / df["trip_distance"]).round(2)

    is_card = (df["payment_type_id"] == 1) & (df["fare_amount"] > 0)
    tip_pct = (df["tip_amount"] / df["fare_amount"] * 100).round(2)
    df["tip_pct"] = np.where(is_card, tip_pct, np.nan)

    pickup = df["pickup_datetime"]
    df["pickup_date"] = pickup.dt.strftime("%Y-%m-%d")
    df["pickup_hour"] = pickup.dt.hour
    df["pickup_dow"] = pickup.dt.dayofweek          # 0 = Monday
    df["is_weekend"] = (df["pickup_dow"] >= 5).astype(int)
    df["time_band"] = df["pickup_hour"].map(get_time_band)

    borough_of_zone = dict(zip(zones["location_id"], zones["borough"]))
    pickup_borough = df["pu_location_id"].map(borough_of_zone)
    dropoff_borough = df["do_location_id"].map(borough_of_zone)
    both_known = (pickup_borough != "Unknown") & (dropoff_borough != "Unknown")
    df["is_cross_borough"] = (both_known & (pickup_borough != dropoff_borough)).astype(int)

    airport = (df["rate_code_id"].isin([2, 3])
               | df["pu_location_id"].isin(config.AIRPORT_ZONE_IDS)
               | df["do_location_id"].isin(config.AIRPORT_ZONE_IDS))
    df["is_airport"] = airport.astype(int)

    # Store times as text in one standard format (NYC local time)
    df["pickup_datetime"] = pickup.dt.strftime("%Y-%m-%d %H:%M:%S")
    df["dropoff_datetime"] = df["dropoff_datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df
