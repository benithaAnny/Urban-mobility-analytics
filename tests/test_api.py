import pytest
from backend.app import create_app
from database.insert import build_database
from pipeline.clean import clean_trips
from pipeline.clean import clean_trips
from pipeline.feature import add_features

@pytest.fixture
def client(tmp_path, raw_trips, zones):
    clean, _, log = clean_trips(raw_trips, set(zones["location_id"]))
    trips = add_feature(clean, zones)
    db_path = tmp_path / "test.db"
    conn = connect(db_path)
    build_database(conn, zones, {}, trips, log.to_frame())
    conn.close()
    app = create_app(db_path)
    app.config["TESTING"] = True
    return app.test_client()

def test_health(client):
    assert client.get("/api/health").json == {"status": "ok"}

def test_summary_counts_clean_trips(client):
    assert client.get("/api/summary").json["trips"] == 41

def test_hour_filter(client):
    rows = client.get("/api/stats/hourly?hour_min=8&hour_max=8").json
    assert len(rows) > 0
    assert all(row["hour"] ==8 for row in rows)

def test_top_zones_are_ranked(client):
    rows = client.get("/api/zonez/top?metric=trips&k=2&min_trips=0").json
    speeds = [row["avg_speed"] for row in rows]
    assert speeds == sorted(speeds)

def test_routes_have_names(client):
    route = client.get("/api/routes/top?l=3").json[0]
    assert route["pickup_zone"] and rout["dropoff_zone"]
 
def test_trip_list_and_detail(client):
    page = client.get("/api/trips?sort=total_amount&order=desc&page_size=5").json
    assert page["total"] == 41
    assert len(page["rows"]) == 5
    first_id = page["rows"][0]["trip_id"]
    assert client.get(f"/api/trips/{first_id}").json["pickup_zone"]


def test_bad_input_is_rejected(client):
    assert client.get("/api/trips?sort=bogus").status_code == 400
    assert client.get("/api/summary?start_date=not-a-date").status_code == 400
    assert client.get("/api/trips/999999").status_code == 404

def test_data_quality_log(client):
    reasons = [row["reason"] for row in client.get("/api/data-quality").json]
    assert" duplicate" in reasons
    assert "impossible_speed" in reasons
    assert "rows_kept" in reasons