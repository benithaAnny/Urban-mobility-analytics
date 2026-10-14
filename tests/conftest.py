"""Small made-up data shared by the tests (no real files needed)."""
import pandas as pd
import pytest

COLUMNS = [
    "vendor_id", "pickup_datetime", "dropoff_datetime", "passenger_count", "trip_distance",
    "rate_code_id", "store_and_fwd_flag", "pu_location_id", "do_location_id", "payment_type_id",
    "fare_amount", "extra", "mta_tax", "tip_amount", "tolls_amount", "improvement_surcharge",
    "congestion_surcharge", "airport_fee", "cbd_congestion_fee", "total_amount",
]


def make_trip(minutes_after_start, duration_min, distance, pu, do, payment=1, fare=None):
    start = pd.Timestamp("2019-01-01 06:00:00") + pd.Timedelta(minutes=minutes_after_start)
    end = start + pd.Timedelta(minutes=duration_min)
    fare = round(3 + distance * 2.5, 2) if fare is None else fare
    tip = round(fare * 0.2, 2) if payment == 1 else 0.0
    extra, mta, improve = 0.5, 0.5, 0.3
    total = round(fare + extra + mta + tip + improve, 2)
    return [1, start, end, 1, distance, 1, "N", pu, do, payment,
            fare, extra, mta, tip, 0.0, improve, 0.0, 0.0, 0.0, total]


@pytest.fixture
def zones():
    return pd.DataFrame({
        "location_id": [1, 61, 79, 132, 161, 237],
        "borough": ["EWR", "Brooklyn", "Manhattan", "Queens", "Manhattan", "Manhattan"],
        "zone_name": ["Newark Airport", "Crown Heights North", "East Village",
                      "JFK Airport", "Midtown Center", "Upper East Side South"],
        "service_zone": ["EWR", "Boro Zone", "Yellow Zone", "Airports", "Yellow Zone", "Yellow Zone"],
    })


@pytest.fixture
def raw_trips():
    pairs = [(161, 237), (79, 161), (237, 79), (61, 161), (132, 161), (161, 1)]
    rows = []
    # 41 good trips, spread over several days and hours (some start in hour 8)
    for i in range(41):
        pu, do = pairs[i % len(pairs)]
        payment = 1 if i % 3 else 2
        rows.append(make_trip(i * 97, 10 + i % 20, 1.5 + i * 0.2, pu, do, payment))
    # bad rows that cleaning must remove
    rows.append(list(rows[0]))                                   # exact duplicate
    rows.append(make_trip(5000, 10, 60.0, 161, 237))             # impossible speed (360 mph)
    rows.append(make_trip(5100, 10, 0.0, 161, 237))              # zero distance
    rows.append(make_trip(5200, 10, 2.0, 161, 999))              # unknown zone
    rows.append(make_trip(5300, 10, 2.0, 161, 237, fare=-5.0))   # negative fare
    return pd.DataFrame(rows, columns=COLUMNS)