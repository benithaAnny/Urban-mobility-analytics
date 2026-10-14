import pandas as pd

from . import config
from .load import REQUIRED_COLUMNS

NUMBER_COLUMNS = [
    "vendor_id", "passenger_count", "trip_distance", "rate_code_id",
    "pu_location_id", "do_location_id", "payment_type_id",
] + config.MONEY_COLUMNS

WHOLE_NUMBER_COLUMNS = [ 
    "vendor_id", "passenger_count", "rate_code_id", "payment_type_id",
    "pu_location_id", "do_location_id",
]

class CleaningLog:
    """A list of every cleaning step and how many rows it affected."""

    def __init__(self):
        self.rows = []

    def add(self, reason, count, action, description):
        self.rows.append({
            "reason": reason,
            "record_count": int(count),
            "action": action,
            "description": description,
        })

    def to_frame(self):
        return pd.DataFrame(self.rows, columns=["reason", "record_count", "action", "description"])

    def write(self, log_dir, excluded):
        """Save the summary and some example removed rows as CSV files."""
        log_dir.mkdir(parents=True, exist_ok=True)
        self.to_frame().to_csv(log_dir / "cleaning_summary.csv", index=False)
        examples = excluded.groupby("exclusion_reason").head(config.SAMPLE_ROWS_PER_REASON)
        examples.to_csv(log_dir / "excluded_records_sample.csv", index=False)

def clean_trips(raw, valid_zone_ids):
    """Return (clean rows, removed rows, CleaningLog)."""
    log = CleaningLog()
    removed_parts = []
    df = raw.copy()
    log.add("rows_loaded", len(df), "info", "Rows read from the trip parquet file")

    def remove(df, is_bad, reason, description):
        """Take out the rows where is_bad is True and record them."""
        bad_rows = df[is_bad].copy()
        bad_rows["exclusion_reason"] = reason
        removed_parts.append(bad_rows)
        log.add(reason, len(bad_rows), "excluded", description)
        return df[~is_bad].copy()

    # ---- 1. Fix data types ----
    df["pickup_datetime"] = pd.to_datetime(df["pickup_datetime"], errors="coerce")
    df["dropoff_datetime"] = pd.to_datetime(df["dropoff_datetime"], errors="coerce")
    for column in NUMBER_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    # ---- 2. Remove bad rows ----
    df = remove(df, df.duplicated(), "duplicate",
                "Exact copy of an earlier row")
    df = remove(df, df[REQUIRED_COLUMNS].isna().any(axis=1), "missing_critical",
                "Missing or unreadable time, location, distance or fare")

    month = df["pickup_datetime"].dt.to_period("M")
    main_month = month.mode()[0] if len(df) else None
    df = remove(df, month != main_month, "out_of_period",
                f"Pickup outside the file's month ({main_month}): device clock errors")

    df["duration_min"] = (df["dropoff_datetime"] - df["pickup_datetime"]).dt.total_seconds() / 60
    df = remove(df, df["duration_min"] <= 0, "non_positive_duration",
                "Drop-off at or before pickup")
    
    df = remove(df, df["duration_min"] < config.MIN_DURATION_MIN, "too_short",
                f"Under {config.MIN_DURATION_MIN:g} minute: meter tests or cancelled trips")
    
    df = remove(df, df["duration_min"] > config.MAX_DURATION_MIN, "too_long",
                f"Over {config.MAX_DURATION_MIN:g} minutes: meter left running")
    df = remove(df, df["trip_distance"] <= 0, "zero_distance",
                "Zero or negative distance")
    
    df = remove(df, df["trip_distance"] > config.MAX_DISTANCE_MI, "distance_outlier",
                f"Over {config.MAX_DISTANCE_MI:g} miles: GPS or odometer error")

    speed_mph = df["trip_distance"] / (df["duration_min"] / 60)
    df = remove(df, speed_mph > config.MAX_SPEED_MPH, "impossible_speed",
                f"Average speed over {config.MAX_SPEED_MPH:g} mph is impossible in NYC")
    
    df = remove(df, (df["fare_amount"] < 0) | (df["total_amount"] < 0), "negative_amount",
                "Negative fare or total: refunds, not real trips")
    df = remove(df, df["fare_amount"] > config.MAX_FARE, "fare_outlier",
                f"Fare over ${config.MAX_FARE:,.0f}: typing error")

    unknown_zone = ~df["pu_location_id"].isin(valid_zone_ids) | ~df["do_location_id"].isin(valid_zone_ids)
    df = remove(df, unknown_zone, "unknown_location",
                "Pickup or drop-off zone ID not in the zone lookup")

    excluded = pd.concat(removed_parts)
    df["duration_min"] = df["duration_min"].round(2)

    # ---- 3. Repair small problems (rows are kept) ----
    bad_passengers = (df["passenger_count"].isna()
                      | (df["passenger_count"] < 1)
                      | (df["passenger_count"] > config.MAX_PASSENGERS))
    df["passenger_imputed"] = bad_passengers.astype(int)
    df.loc[bad_passengers, "passenger_count"] = 1
    log.add("passenger_count_imputed", bad_passengers.sum(), "imputed",
            f"Missing, 0 or more than {config.MAX_PASSENGERS} passengers set to 1 and flagged")

    unknown_rate = ~df["rate_code_id"].isin(list(config.RATE_CODES))
    df.loc[unknown_rate, "rate_code_id"] = 99
    log.add("rate_code_unknown", unknown_rate.sum(), "imputed",
            "Missing or unknown rate code set to 99 (Unknown)")

    unknown_payment = ~df["payment_type_id"].isin(list(config.PAYMENT_TYPES))
    df.loc[unknown_payment, "payment_type_id"] = 5
    log.add("payment_type_unknown", unknown_payment.sum(), "imputed",
            "Missing or unknown payment type set to 5 (Unknown)")

    missing_vendor = df["vendor_id"].isna()
    df.loc[missing_vendor, "vendor_id"] = 0
    log.add("vendor_missing", missing_vendor.sum(), "imputed",
            "Missing vendor stored as 0 (Unknown vendor)")

    missing_amounts = df[config.EXTRA_AMOUNT_COLUMNS].isna().any(axis=1)
    df[config.EXTRA_AMOUNT_COLUMNS] = df[config.EXTRA_AMOUNT_COLUMNS].fillna(0.0)
    log.add("surcharge_missing", missing_amounts.sum(), "imputed",
            "Missing surcharges set to $0 (charge not applied)")

    df["store_and_fwd"] = (df["store_and_fwd_flag"].astype(str).str.upper() == "Y").astype(int)
    df = df.drop(columns=["store_and_fwd_flag"])
    for column in WHOLE_NUMBER_COLUMNS:
        df[column] = df[column].astype("int64")

    # ---- 4. Flag odd rows (kept) ----
    bill_total = df[config.BILL_COMPONENTS].sum(axis=1)
    total_mismatch = (df["total_amount"] - bill_total).abs() > config.TOTAL_TOLERANCE
    tip_too_big = (df["tip_amount"] > df["fare_amount"]) & (df["fare_amount"] > 0)
    df["is_suspicious"] = (total_mismatch | tip_too_big).astype(int)
    log.add("total_mismatch", total_mismatch.sum(), "flagged",
            "Bill items don't add up to the total (kept, flagged)")
    log.add("tip_exceeds_fare", tip_too_big.sum(), "flagged",
            "Tip bigger than the fare (kept, flagged)")

    log.add("rows_excluded", len(excluded), "info", "Total rows removed")
    log.add("rows_kept", len(df), "info", "Rows written to the database")
    return df.reset_index(drop=True), excluded, log