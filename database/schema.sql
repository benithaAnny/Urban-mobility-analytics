-- Urban Mobility Data Explorer: database tables (SQLite)
-- Lookup tables store each category once; the trips table points to them.

DROP TABLE IF EXISTS trips;
DROP TABLE IF EXISTS zone_geometries;
DROP TABLE IF EXISTS zones;
DROP TABLE IF EXISTS boroughs;
DROP TABLE IF EXISTS service_zones;
DROP TABLE IF EXISTS vendors;
DROP TABLE IF EXISTS rate_codes;
DROP TABLE IF EXISTS payment_types;
DROP TABLE IF EXISTS cleaning_log;

CREATE TABLE boroughs (
    borough_id INTEGER PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE
);

CREATE TABLE service_zones (
    service_zone_id INTEGER PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE
);

CREATE TABLE zones (
    location_id     INTEGER PRIMARY KEY,
    zone_name       TEXT    NOT NULL,
    borough_id      INTEGER NOT NULL REFERENCES boroughs(borough_id),
    service_zone_id INTEGER NOT NULL REFERENCES service_zones(service_zone_id),
    centroid_lat    REAL,
    centroid_lon    REAL
);

-- Shapes are large, so they live in their own table (only the map needs them)
CREATE TABLE zone_geometries (
    location_id INTEGER PRIMARY KEY REFERENCES zones(location_id),
    geojson     TEXT NOT NULL
);

CREATE TABLE vendors       (vendor_id       INTEGER PRIMARY KEY, name        TEXT NOT NULL);
CREATE TABLE rate_codes    (rate_code_id    INTEGER PRIMARY KEY, description TEXT NOT NULL);
CREATE TABLE payment_types (payment_type_id INTEGER PRIMARY KEY, description TEXT NOT NULL);

CREATE TABLE trips (
    trip_id               INTEGER PRIMARY KEY,
    vendor_id             INTEGER NOT NULL REFERENCES vendors(vendor_id),
    pickup_datetime       TEXT    NOT NULL,          -- 'YYYY-MM-DD HH:MM:SS', NYC local time
    dropoff_datetime      TEXT    NOT NULL,
    pu_location_id        INTEGER NOT NULL REFERENCES zones(location_id),
    do_location_id        INTEGER NOT NULL REFERENCES zones(location_id),
    passenger_count       INTEGER NOT NULL CHECK (passenger_count BETWEEN 1 AND 6),
    passenger_imputed     INTEGER NOT NULL DEFAULT 0 CHECK (passenger_imputed IN (0, 1)),
    trip_distance         REAL    NOT NULL CHECK (trip_distance > 0),
    rate_code_id          INTEGER NOT NULL REFERENCES rate_codes(rate_code_id),
    payment_type_id       INTEGER NOT NULL REFERENCES payment_types(payment_type_id),
    store_and_fwd         INTEGER NOT NULL DEFAULT 0 CHECK (store_and_fwd IN (0, 1)),
    -- the bill
    fare_amount           REAL NOT NULL CHECK (fare_amount >= 0),
    extra                 REAL NOT NULL DEFAULT 0,
    mta_tax               REAL NOT NULL DEFAULT 0,
    tip_amount            REAL NOT NULL DEFAULT 0,
    tolls_amount          REAL NOT NULL DEFAULT 0,
    improvement_surcharge REAL NOT NULL DEFAULT 0,
    congestion_surcharge  REAL NOT NULL DEFAULT 0,
    airport_fee           REAL NOT NULL DEFAULT 0,
    cbd_congestion_fee    REAL NOT NULL DEFAULT 0,
    total_amount          REAL NOT NULL CHECK (total_amount >= 0),
    -- derived features (stored so the dashboard reads them quickly)
    duration_min          REAL    NOT NULL CHECK (duration_min > 0),
    avg_speed_mph         REAL    NOT NULL,
    fare_per_mile         REAL    NOT NULL,
    tip_pct               REAL,                       -- empty for non-card trips
    pickup_date           TEXT    NOT NULL,
    pickup_hour           INTEGER NOT NULL CHECK (pickup_hour BETWEEN 0 AND 23),
    pickup_dow            INTEGER NOT NULL CHECK (pickup_dow BETWEEN 0 AND 6),
    is_weekend            INTEGER NOT NULL CHECK (is_weekend IN (0, 1)),
    time_band             TEXT    NOT NULL,
    is_airport            INTEGER NOT NULL CHECK (is_airport IN (0, 1)),
    is_cross_borough      INTEGER NOT NULL CHECK (is_cross_borough IN (0, 1)),
    is_suspicious         INTEGER NOT NULL DEFAULT 0 CHECK (is_suspicious IN (0, 1))
);

CREATE TABLE cleaning_log (
    step_order   INTEGER PRIMARY KEY,
    reason       TEXT    NOT NULL,
    record_count INTEGER NOT NULL,
    action       TEXT    NOT NULL CHECK (action IN ('info', 'excluded', 'imputed', 'flagged')),
    description  TEXT    NOT NULL
);
