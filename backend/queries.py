import json
from pipeline import config

SPEED = "ROUND(SUM(t.trip_distance) / (SUM(t.duration_min) / 60.0), 2)"
FARE_PER_MILE = "ROUND(SUM(t.fare_amount) / SUM(t.trip_distance), 2)"
def fetch_all(conn, sql, values=()):
    return[dict(row) for row in conn.execute(sql, values)]
def meta(conn):
    first, last, total = conn.execute(
        "SELECT MIN(pickup_date), MAX(pickup_date), COUNT(*) FROM trips").fetchone()
    boroughs = fetch_all(conn, "SELECT name FROM boroughs ORDER BY name")
    return{
        "first_date": first,
        "last_date": last,
        "total_trips":total,
        "boroughs":[row["name"] for row in boroughs],
        "payment_types": fetch_all(conn, "SELECT payment_type_id AS id, description "
                                   "FROM payment_types ORDER BY payment_type_id"),
        "time_bands":[band[0] for band in config.TIME_BANDS],
        "zones": fetch_all(conn, "SELECT z.location_id, z.zone_name, b.name AS borough "
                           "FROM zones z JOIN boroughs b ON b.borough_id = z.borough_id "
                           "ORDER BY z.zone_name"),
        
    }

def summary(conn, where, values):
    row = conn.execute(f"""
      SELECT COUNT(*)                             AS trips,
          ROUND(AVG(t.total_amount) ,2)           AS avg_total,
          ROUND(AVG(t.trip_distance), 2)          AS avg_distance,
          ROUND(AVG(t.duration_min), 1)           AS avg_duration,
          {SPEED}                                 AS avg_speed,
          {FARE_PER_MILE}                         AS fare_per_mile,
          ROUND(AVG(t.tip_pct), 1)                AS avg_tip_pct,
          ROUND(SUM(t.total_amount),0)            AS revenue
    FROM trips t {where}""", values).fetchone()
    return dict(row)

def hourly(conn, where, values):
    return fetch_all(conn, f"""
    SELECT t.pickup_hour AS hour, COUNT(*) AS trips,
    {SPEED} AS avg_speed, {FARE_PER_MILE} AS fare_per_mile,
    ROUND(AVG(t.total_amount), 2) AS avg_total
    FROM trips t {where}
    GROUP BY t.pickup_hour ORDER BY t.pickup_hour""", values)

def daily(conn, where, values):
    return fetch_all(conn, f"""
    SELECT t.pickup_date AS date, COUNT(*) AS trips, ROUND(AVG(t.total_amount), 2) AS avg_total
    FROM trips t {where}
    GROUP BY t.pickup_date ORDER BY t.pickup_date""", values)

def heatmap(conn, where, values):
    return fetch_all(conn, f"""
    SELECT t.pickup_dow AS dow, t.pickup_hour AS hour, COUNT(*) AS trips
    FROM trips t {where}
    GROUP BY t.pickup_dow,t.pickup_hour""", values)
def distance_bands(conn, where, values):
    return fetch_all(conn, f"""
    SELECT CASE WHEN t.trip_distance < 1 THEN '0-1'
                WHEN t.trip_distance < 2 THEN '1-2'
                WHEN t.trip_distance < 3 THEN '2-3'
                WHEN t.trip_distance < 5 THEN '3-5'
                WHEN t.trip_distance < 10 THEN '5-10'
                WHEN t.trip_distance < 20 THEN '10-20'
                ELSE '20+' END AS band,
           MIN(t.trip_distance) AS band_start, COUNT(*) AS trips,
           {FARE_PER_MILE} AS fare_per_mile, ROUND(AVG(t.total_amount), 2) AS avg_total
    FROM trips t {where}
    GROUP BY band ORDER BY band_start""", values)


def payment(conn, where, values):
    return fetch_all(conn, f"""
    SELECT t.payment_type_id, p.description, COUNT(*) AS trips,
           ROUND(AVG(CASE WHEN t.tip_amount > 0 THEN 100.0 ELSE 0 END), 1) AS pct_with_tip,
           ROUND(AVG(t.total_amount), 2) AS avg_total
    FROM trips t
    JOIN payment_types p ON p.payment_type_id = t.payment_type_id
    {where}
    GROUP BY t.payment_type_id, p.description
    ORDER BY trips DESC""", values)

def zone_stats(conn,where, values):
    return fetch_all(conn, f"""
        SELECT z.location_id, z.zone_name AS zone, b.name AS borough, COUNT(*) AS trips,
            {SPEED} AS avg_speed, {FARE_PER_MILE} AS fare_per_mile,
            ROUND(AVG(t.total_amount), 2) AS avg_total,
            ROUND(AVG(t.tip_pct), 1) AS avg_tip_pct,
            ROUND(AVG(t.is_airport) * 100, 1) AS airport_share
        FROM trips t
        JOIN zones z ON z.location_id = t.pu_location_id
        JOIN boroughs b ON b.borough_id = z.borough_id
        {where}
        GROUP BY z.location_id""", values)

    
def route_stats(conn, where, values):
    return fetch_all(conn, f"""
        SELECT t.pu_location_id, t.do_location_id, COUNT(*) AS trips,
                ROUND(AVG(t.duration_min), 1) AS avg_duration,
                ROUND(AVG(t.total_amount),2) AS avg_total, {SPEED} AS avg_speed
        FROM trips t {where}
        GROUP BY t.pu_location_id, t.do_location_id""", values)

def zone_names(conn):
    rows = conn.execute("SELECT z.location_id, z.zone_name, b.name AS borough "
                        "FROM zones z JOIN boroughs b ON b.borough_id = z.borough_id")
    names = {}
    for row in rows:
        names[row["location_id"]] = (row["zone_name"], row["borough"])
    return names

def list_trips(conn, where, values, sort, order, page, page_size):
    total = conn.execute(f"SELECT COUNT(*) FROM trips t {where}", values).fetchone()[0]
    offset = (page -1) * page_size
    rows = fetch_all(conn, f"""
        SELECT t.trip_id, t.pickup_datetime, pz.zone_name AS pickup_zone, dz.zone_name AS dropoff_zone,
                t.trip_distance, t.duration_min, t.avg_speed_mph, t.total_amount, t.fare_per_mile,
                t.tip_pct, t.passenger_count, p.description AS payment, t.is_suspicious
        FROM trips t
        JOIN zones pz ON pz.location_id = t.pu_location_id
        JOIN zones dz ON dz.location_id = t.do_location_id
        JOIN payment_types p ON p.payment_type_id = t.payment_type_id
        {where}
        ORDER BY t.{sort} {order.upper()}, t.trip_id
        LIMIT ? OFFSET ?""", values + [page_size, offset])
    return {"total": total, "page": page, "page_size": page_size, "rows":rows}

def trip_detail(conn, trip_id):
    row = conn.execute("""
        SELECT t.*, pz.zone_name AS pickup_zone, pb.name AS pickup_borough,
                dz.zone_name AS dropoff_zone, db.name AS dropoff_borough,
                v.name AS vendor, r.description AS rate_code, p.description AS payment
        FROM trips t
        JOIN zones pz ON pz.location_id = t.pu_location_id
        JOIN boroughs pb ON pb.borough_id = pz.borough_id
        JOIN zones dz ON dz.location_id = t.do_location_id
        JOIN boroughs db ON db.borough_id = dz.borough_id
        JOIN vendors v ON v.vendor_id = t.vendor_id
        JOIN rate_codes r ON r.rate_code_id = t.rate_code_id
        JOIN payment_types p ON p.payment_type_id = t.payment_type_id
        WHERE t.trip_id = ?""", (trip_id,)).fetchone()
    if row is None:
        return None
    return dict(row)


def zone_geojson(conn):
    rows = conn.execute("""
        SELECT g.location_id, g.geojson, z.zone_name, b.name AS borough
        FROM zone_geometries g
        JOIN zones z ON z.location_id = g.location_id
        JOIN boroughs b ON b.borough_id = z.borough_id""")
    features = []
    for row in rows:
        features.append({
            "type": "Feature",
            "properties": {"location_id": row["location_id"], "zone": row["zone_name"],
                           "borough": row["borough"]},
            "geometry":json.loads(row["geojson"]),

        })
    return {"type": "FeatureCollection", "features": features}
def cleaning_log(conn):
    return fetch_all(conn,"select reason, record_count, action, description "
                     "FROM cleaning_log ORDER BY step_order")