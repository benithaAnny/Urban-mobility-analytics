# NYC Taxi Pulse - Urban Mobility Data Explorer

A full-stack app that takes raw New York City yellow-taxi trip records, cleans them, stores
them in a relational database, and lets you explore how the city moves: when and where trips
happen, how fast traffic runs, and what a ride costs.

## Project links
- Video walkthrough: <ADD LINK>
- Scrum board: <ADD LINK>
- Technical report: [docs/REPORT.pdf](docs/REPORT.pdf)
---

## 1. The problem
The NYC Taxi and Limousine Commission (TLC) publishes every yellow-taxi trip as open data:
pickup and drop-off times and zones, distance, itemized fare, payment type, passenger count.
The raw file is too big and too messy to read directly. It has duplicate rows, trips that end
before they start, 500-mile rides, and bills that don't add up. And the trips only carry
numeric zone IDs, so you can't tell where anything happened without the zone tables.

This project answers: ** What does the data say about urban mobility, once it's clean?**

## 2. How it works
```
  TLC data files  -->  Pipeline  -->  Database  -->  API  -->  Dashboard
  (raw, messy)         (clean it)     (store it)     (serve)    (explore)
```
In plain words:
1. The **pipeline** loads the three TLC files, cleans them and adds the derived features. It runs once.
2. The cleaned data goes into a **SQLite database**.
3. The **Flask API** reads the database and answers questions, using our own algorithms for ranking and caching.
4. The **dashboard** in the browser asks the API and draws the maps, charts and tables.

A browser can't read a database directly, so the API sits in the middle.

## 3. The data
We use the January 2019 yellow-taxi file. Three files go in `data/raw/`.

**Raw data file needed:** `yellow_tripdata.parquet` is too large for GitHub, so it is **not in the repository**. We shared a download link instead:
[Download yellow_tripdata.parquet](https://drive.google.com/file/d/1oAkdP_gE8k-sRF2Hxb-3qcE-1T1wCcoA/view?usp=sharing)
The parquet file was derived from the original csv file [yellow_tripdata-2019.csv](https://alueducation.instructure.com/courses/3138/files/581082?wrap=1)

Download it and save it in `data/raw/` with that exact name before running the program. The other two files (the zone lookup and the zone shapes) come from the course assignment page (Dataset section: Dimension Table, Spatial Metadata). Save all three with these exact names:

| File | What it is |
|---|---|
| `yellow_tripdata.parquet` | One row per trip (the fact table) |
| `taxi_zone_lookup.csv` | Zone ID to borough, zone name and service zone (the dimension table) |
| `taxi_zones.geojson` | The shape of each zone, used to draw the map |

**If a file comes in another format**
- *Trips as a CSV:* convert it to parquet (change the CSV name to match yours):
```bash
  python -c "import pandas as pd; pd.read_csv('data/raw/yellow_tripdata_2019-01.csv').to_parquet('data/raw/yellow_tripdata.parquet')"
```
- *Zones as a shapefile zip:* the app needs GeoJSON. Open https://mapshaper.org, drag the zip in,
  click Export, choose GeoJSON, and save the result as `data/raw/taxi_zones.geojson`.
  (The coordinates may be in feet; the pipeline converts them automatically.)

## 4. Data cleaning
Every rule is applied in `pipeline/clean.py`, and the thresholds live in `pipeline/config.py`.
Nothing is dropped silently: each rule's count goes into a cleaning log, and a sample of the
excluded rows is saved so the decisions can be reviewed.

**Excluded** (the trip is removed):

| Rule | What it catches |
|---|---|
| Duplicate | Exact copy of an earlier row |
| Missing critical field | No time, zone, distance or fare |
| Out of period | Pickup outside the file's month (clock errors) |
| Non-positive duration | Drop-off at or before pickup |
| Too short / too long | Under 1 minute, or over 300 minutes |
| Zero distance | Distance of zero or less |
| Distance outlier | Over 100 miles |
| Impossible speed | Average speed over 80 mph |
| Negative amount | Negative fare or total (refunds, not trips) |
| Fare outlier | Fare over $1,000 |
| Unknown location | Zone ID missing from the lookup |

**Repaired** (the trip is kept and the change is counted): missing or invalid passenger count
becomes 1 and is flagged; unknown rate code, payment type or vendor become an "Unknown"
category; missing surcharges become $0.

**Flagged** (the trip is kept and marked suspicious): the bill items don't add up to the
total, or the tip is bigger than the fare.

The log is saved in `data/logs/` (`cleaning_summary.csv` and `excluded_records_sample.csv`)
and is also shown in the dashboard's data-quality table.

## 5. Derived features
Calculated in `pipeline/features.py` and stored so the dashboard reads them quickly:

| Feature | Meaning | Why it's useful |
|---|---|---|
| `avg_speed_mph` | distance / duration | A traffic measure: slow speeds mean congestion |
| `fare_per_mile` | fare / distance | Shows how pricing changes with trip length |
| `tip_pct` | tip / fare, card trips only | Cash tips aren't recorded, so cash is left out |
| `time_band` | Late night, morning rush, midday, evening rush, night | Groups the 24 hours into patterns |
| `is_airport` | Trip to or from JFK, LaGuardia or Newark | Airport trips behave differently |
| `is_cross_borough` | Pickup and drop-off in different boroughs | Separates local from long-haul trips |

Pickup date, hour, day of week and weekend flag are stored too, for fast filtering.

## 6. Database design
SQLite. The main table is `trips`. Everything else is a small lookup table that `trips` points to, so each category is stored only once.

```
  zones          -->
  vendors        -->
  rate codes     -->    trips
  payment types  -->
```
A separate `cleaning_log` table records what the cleaning step removed or fixed.

`CHECK` rules reject impossible values, and indexes (`database/indexes.sql`) speed up the common filters. The full tables are in `database/schema.sql`.

## 7. The API
A Flask REST API with 15 endpoints, all sharing the same optional filters (date range,
borough, pickup and drop-off zone, hour, distance, fare, payment type, time band, weekend,
airport). Bad input returns a clear `400` error. The endpoints are defined in
`backend/routes.py`.

## 8. Algorithms written by hand
Required by the assignment, and written without `heapq`, `sorted()` or `Counter`
(all in `backend/algorithms/`):

| Algorithm | Used for | Cost |
|---|---|---|
| Min-heap top-K | Top 10 busiest zones and routes | O(n log k) time, O(k) space |
| Merge sort | Ordering the zone table by any column the user picks | O(n log n) time, O(n) space |
| LRU cache (dictionary + doubly linked list) | Remembering recent API answers so repeated filters are instant | O(1) per lookup |

Why a heap for top-K: sorting all the routes would cost O(n log n). Keeping only the best K in
a heap means each new row just has to beat the weakest of the current best K.

## 9. The dashboard
Open it in the browser and you get:
- **Filters** for date, borough, hour, distance, fare, payment type, time band, weekend and airport trips
- **KPI cards and a short "What the data says" summary** that updates with the filters
- **Zone map:** pickup zones coloured by trips, average speed or $/mile (your choice). Click a zone to filter everything to it
- **The daily rhythm:** trips per hour with average speed
- **Week x hour heatmap** of demand
- **Price per mile by trip length**, and **how riders pay and tip** (share of trips and share with a recorded tip)
- **Trips per day** and **busiest routes**
- **Explore trips:** a sortable, paged table. Click a row to see the full trip
- **Data quality and transparency:** the cleaning log, in the app itself

## 10. Setup and run
**Requirements:** Python 3.10+, about 4 GB free RAM for a full month of data (use `--sample`
on smaller machines), and internet access in the browser (Leaflet, Chart.js and map tiles
load from CDNs).

**Install**
```bash
git clone <REPO_URL>
cd urban-mobility-explorer
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Add the data.** Put the three files in `data/raw/` as described in section 3.

**Build the database**
```bash
python -m pipeline.run_pipeline --sample 300000    # quick run, a few minutes
```
This creates `database/mobility.db` and writes the cleaning logs to `data/logs/`.

For more data, use a bigger sample, for example `--sample 1000000` (the one our dashboard and
report use; it took about 16 minutes on our machines). We cleaned the full month (7.7 million
trips) too, but writing all of it to the database is slow, so we did not load it.

**Run the app**
```bash
python -m backend.app
```
Open http://localhost:5000. Flask serves both the API and the dashboard.

**Optional speed-up.** If the dashboard feels slow because the project is in a synced or Windows
folder (for example OneDrive), copy the database to a faster disk and point the app at it:
```bash
cp database/mobility.db ~/mobility.db
MOBILITY_DB=~/mobility.db python -m backend.app
```
The first load of each chart is the slowest; repeats are fast because answers are cached.

**Run the tests**
```bash
pytest -q
```
The tests build a small temporary database from synthetic trips, so they don't need the real data.

## 11. Project structure
```
pipeline/    load, clean, add features, run the pipeline
database/    schema.sql, indexes.sql, insert code
backend/     Flask app, filters, SQL queries, algorithms
frontend/    dashboard (HTML/CSS/JS)
tests/       pytest tests
docs/        technical report
data/logs/   cleaning summary and excluded-record samples
```

## 12. Troubleshooting
- "Database ... not found": run the build step first.
- Map is empty: `taxi_zones.geojson` was missing when the pipeline ran. Add it and rebuild.
- MemoryError during the pipeline: use `--sample 500000`.
- Map is grey with no streets: the browser needs internet access for the map tiles.
- Charts time out or load slowly: use the optional speed-up in section 10.
- Port in use: `PORT=5050 python -m backend.app` (Windows: `set PORT=5050` first).
