# NYC Taxi Analytics

End-to-end data analytics pipeline using the NYC TLC Yellow Taxi dataset (January 2024, ~2.7M rows). Built with Python, DuckDB, MySQL, and Tableau Public.

The project covers real-world data ingestion, SQL transformation, aggregated view creation, CSV export, and interactive dashboard delivery — from raw parquet files to published visualisations.

---

## Stack

| Layer | Tool |
|---|---|
| Raw data | NYC TLC Yellow Taxi parquet (Jan 2024) |
| Extraction | DuckDB (reads parquet over HTTP) |
| Storage | MySQL 8.0 (via Docker) |
| Transformation | SQL views inside MySQL |
| Export | Python + pandas |
| Dashboards | Tableau Public 2026.2 |
| Version control | Git + GitHub |
| Environment | Windows, Git Bash, Python 3.14 |

---

## Project Structure

```
nyc-taxi-analytics/
├── scripts/
│   ├── data_pipeline.py      # Main ETL: extract → transform → load → views
│   ├── export_csv.py         # Exports MySQL views to CSV for Tableau
│   └── config.py             # Reads .env config (if separated)
├── sql/
│   ├── schema.sql            # trips table DDL
│   └── views.sql             # All 5 aggregated views
├── data/
│   └── exports/              # Generated CSVs (gitignored)
├── dashboards/               # Tableau .twbx files
├── docker-compose.yml        # MySQL 8.0 container
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── .gitignore
└── README.md
```

---

## Dataset

**Source:** NYC Taxi and Limousine Commission (TLC)
**File:** `yellow_tripdata_2024-01.parquet`
**URL:** https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet
**Rows:** ~2.7 million trips
**Period:** January 2024

The pipeline filters out invalid rows: zero fares, zero distance, zero passengers, and trips outside the 1–300 minute duration range.

---

## Quickstart

### 1. Prerequisites

- Python 3.9+
- Docker Desktop (must be running)
- Git Bash (Windows)

### 2. Clone the repo

```bash
git clone https://github.com/ashwinbasil/nyc-taxi-analytics.git
cd nyc-taxi-analytics
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set your MySQL credentials:

```
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root_password
MYSQL_DATABASE=nyc_taxi
BATCH_SIZE=5000
```

### 4. Start MySQL

```bash
docker-compose up -d
```

Wait 20 seconds, then verify:

```bash
docker ps
```

### 5. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the pipeline

```bash
cd scripts
python data_pipeline.py --mode full --month 2024-01
```

This downloads the parquet file, cleans the data, loads 2.7M rows into MySQL, and builds all five views. Takes roughly 2 minutes.

### 7. Export CSVs for Tableau

```bash
python export_csv.py
```

Exports all views to `data/exports/`. These are gitignored since they are generated files.

---

## Pipeline Modes

```bash
# Full load: truncates and reloads
python data_pipeline.py --mode full --month 2024-01

# Incremental: appends new month
python data_pipeline.py --mode incremental --month 2024-02
```

---

## MySQL Views

Five aggregated views are created automatically at the end of the pipeline run. These are what Tableau connects to via the exported CSVs.

| View | Description |
|---|---|
| `daily_revenue` | Revenue, trips, avg fare, and tip rate per day |
| `hourly_patterns` | Trip volume and revenue by hour and day of week |
| `zone_summary` | Trip count, avg fare, avg distance, tip rate by pickup zone |
| `payment_split` | Trip count and revenue split by payment method |
| `anomalies` | Trips with z-score > 3 vs their pickup zone average |

### Anomaly detection logic

MySQL does not support `QUALIFY`, so anomaly detection uses a subquery join pattern:

```sql
SELECT t.*, 
    ROUND(ABS(t.total_amount - z.avg_fare) / NULLIF(z.stddev_fare, 0), 2) AS z_score
FROM trips t
JOIN (
    SELECT pickup_location_id,
           AVG(total_amount)    AS avg_fare,
           STDDEV(total_amount) AS stddev_fare
    FROM trips
    GROUP BY pickup_location_id
) z ON t.pickup_location_id = z.pickup_location_id
WHERE ABS(t.total_amount - z.avg_fare) / NULLIF(z.stddev_fare, 0) > 3
ORDER BY z_score DESC
LIMIT 1000;
```

---

## Dashboards

Built in Tableau Public 2026.2 using the exported CSVs as data sources.

Five sheets:

- **Daily Revenue** — line chart with trip volume overlay
- **Hourly Heatmap** — busiest hours by day of week
- **Zone Performance** — top pickup zones by trips and avg fare
- **Payment Split** — cash vs card vs app breakdown
- **Anomaly Table** — flagged suspicious trips sorted by z-score

---

## Key Learnings

- `DATEDIFF` is MySQL syntax. DuckDB uses `date_diff('minute', ...)`.
- `DATE_ADD(..., INTERVAL 1 MONTH)` is MySQL syntax. In DuckDB, compute the next month in Python and pass it as a plain string.
- MySQL has no `QUALIFY`. Window function filtering requires a subquery join.
- Tableau Public (free) does not support live database connections. Export to CSV first.
- The MySQL CLI with `sed` on Windows Git Bash produces malformed CSV headers. Use `pandas.read_sql` via Python instead.
- Schema changes require dropping the table first. Stale schemas with missing columns cause silent failures on insert.
- Docker Desktop must be running before any MySQL connection attempt. The daemon does not start automatically on Windows.

---

## Requirements

```
duckdb
pandas
mysql-connector-python
sqlalchemy
pymysql
python-dotenv
```

Install:

```bash
pip install -r requirements.txt
```

---

## Gitignore

```
data/
*.parquet
*.duckdb
data/exports/
.env
__pycache__/
pipeline.log
```

Raw data, exports, and credentials are never committed.

---

## License

MIT
