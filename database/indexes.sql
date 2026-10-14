CREATE INDEX IF NOT EXISTS idx_trips_pickup_date  ON trips(pickup_date);                  -- date filters, daily chart
CREATE INDEX IF NOT EXISTS idx_trips_pickup_dt    ON trips(pickup_datetime);              -- trip table default sort
CREATE INDEX IF NOT EXISTS idx_trips_pu_zone_date ON trips(pu_location_id, pickup_date);  -- zone click + dates
CREATE INDEX IF NOT EXISTS idx_trips_do_zone      ON trips(do_location_id);               -- routes
CREATE INDEX IF NOT EXISTS idx_trips_hour         ON trips(pickup_hour);                  -- hour filters, hourly chart
CREATE INDEX IF NOT EXISTS idx_trips_dow_hour     ON trips(pickup_dow, pickup_hour);      -- heatmap
CREATE INDEX IF NOT EXISTS idx_trips_payment      ON trips(payment_type_id);              -- payment filter and chart
CREATE INDEX IF NOT EXISTS idx_trips_total        ON trips(total_amount);                 -- fare filters and sorting
CREATE INDEX IF NOT EXISTS idx_zones_borough      ON zones(borough_id);                   -- borough filter
ANALYZE;