
from flask import Blueprint, abort, current_app, jsonify, request

from backend import queries
from backend.algorithms import merge_sort, top_k
from backend.db import get_db
from backend.filters import build_where

api = Blueprint("api", __name__)

ZONE_METRICS = ["trips", "avg_speed", "fare_per_mile", "avg_total", "avg_tip_pct", "airport_share"]
TRIP_SORT_COLUMNS = ["pickup_datetime", "trip_distance", "duration_min", "avg_speed_mph",
                     "total_amount", "fare_per_mile", "tip_pct"]
ORDERS = ["asc", "desc"]




def send_cached(make_data):
    """Send JSON for this URL. Reuse the saved answer if we've seen this URL before."""
    cache = current_app.extensions["response_cache"]
    key = request.full_path
    data = cache.get(key)
    if data is None:
        data = make_data()
        cache.put(key, data)
    return jsonify(data)


def run_filtered(query_function):
    """Run a query using the filters in the URL."""
    where, values = build_where(request.args)
    return query_function(get_db(), where, values)


def int_arg(name, default, smallest, largest):
    text = request.args.get(name, str(default))
    try:
        value = int(text)
    except ValueError:
        raise ValueError(f"'{name}' must be a whole number")
    if value < smallest or value > largest:
        raise ValueError(f"'{name}' must be between {smallest} and {largest}")
    return value


def choice_arg(name, default, choices):
    value = request.args.get(name, default)
    if value not in choices:
        raise ValueError(f"'{name}' must be one of: {', '.join(choices)}")
    return value




@api.get("/health")
def health():
    return jsonify(status="ok")


@api.get("/meta")
def meta():
    return send_cached(lambda: queries.meta(get_db()))


@api.get("/summary")
def summary():
    return send_cached(lambda: run_filtered(queries.summary))


@api.get("/stats/hourly")
def stats_hourly():
    return send_cached(lambda: run_filtered(queries.hourly))


@api.get("/stats/daily")
def stats_daily():
    return send_cached(lambda: run_filtered(queries.daily))


@api.get("/stats/heatmap")
def stats_heatmap():
    return send_cached(lambda: run_filtered(queries.heatmap))


@api.get("/stats/payment")
def stats_payment():
    return send_cached(lambda: run_filtered(queries.payment))


@api.get("/stats/distance")
def stats_distance():
    return send_cached(lambda: run_filtered(queries.distance_bands))


@api.get("/zones/stats")
def zones_stats():
    sort = choice_arg("sort", "trips", ZONE_METRICS)
    order = choice_arg("order", "desc", ORDERS)

    def make_data():
        rows = run_filtered(queries.zone_stats)
        return merge_sort(rows, key=lambda row: row[sort], reverse=(order == "desc"))

    return send_cached(make_data)


@api.get("/zones/top")
def zones_top():
    metric = choice_arg("metric", "trips", ZONE_METRICS)
    order = choice_arg("order", "desc", ORDERS)
    k = int_arg("k", 10, 1, 50)
    min_trips = int_arg("min_trips", 50, 0, 1_000_000_000)

    def make_data():
        rows = []
        for row in run_filtered(queries.zone_stats):
            if row["trips"] >= min_trips and row[metric] is not None:
                rows.append(row)
        # For "lowest", rank by the negative value: the biggest negative is the smallest value
        sign = 1 if order == "desc" else -1
        return top_k(rows, k, key=lambda row: sign * row[metric])

    return send_cached(make_data)


@api.get("/routes/top")
def routes_top():
    k = int_arg("k", 10, 1, 50)

    def make_data():
        best = top_k(run_filtered(queries.route_stats), k, key=lambda row: row["trips"])
        names = queries.zone_names(get_db())
        for route in best:
            route["pickup_zone"], route["pickup_borough"] = names.get(route["pu_location_id"], ("?", "?"))
            route["dropoff_zone"], route["dropoff_borough"] = names.get(route["do_location_id"], ("?", "?"))
        return best

    return send_cached(make_data)


@api.get("/trips")
def trips():
    sort = choice_arg("sort", "pickup_datetime", TRIP_SORT_COLUMNS)
    order = choice_arg("order", "desc", ORDERS)
    page = int_arg("page", 1, 1, 1_000_000)
    page_size = int_arg("page_size", 25, 1, 100)

    def make_data():
        where, values = build_where(request.args)
        return queries.list_trips(get_db(), where, values, sort, order, page, page_size)

    return send_cached(make_data)


@api.get("/trips/<int:trip_id>")
def trip_detail(trip_id):
    trip = queries.trip_detail(get_db(), trip_id)
    if trip is None:
        abort(404, description=f"Trip {trip_id} not found")
    return jsonify(trip)


@api.get("/geo/zones")
def geo_zones():
    return send_cached(lambda: queries.zone_geojson(get_db()))


@api.get("/data-quality")
def data_quality():
    return send_cached(lambda: queries.cleaning_log(get_db()))
