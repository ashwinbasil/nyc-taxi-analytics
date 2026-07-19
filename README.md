# NYC Taxi Analytics Pipeline

A production-style analytics pipeline built on 2.7 million real taxi trips from January 2024. The pipeline ingests raw parquet data, models it in MySQL, and delivers five operational dashboards in Tableau answering concrete business questions about revenue, demand, and fare anomalies.

---

## Business problem

NYC taxi operators collect data on every trip but rarely have visibility into three things that directly affect revenue:

1. **When and where to drive** — which hours and zones generate the most revenue per trip
2. **How payment method affects earnings** — whether card vs cash trips differ in fare and tip value
3. **Where fare anomalies exist** — trips with statistically unusual fares that warrant investigation

This pipeline answers all three using a month of real TLC data.

---

## Key findings

> These are derived from January 2024 yellow taxi data, ~2.7M trips after cleaning.

- **Peak revenue window is 6pm–10pm on weekdays**, accounting for the highest trip density and average fare combined
- **Airport zones (JFK: 132, LaGuardia: 138) generate the highest average fares** — roughly 2x the Manhattan average — but represent a smaller share of total volume
- **Credit card payments correlate with significantly higher tip rates** than cash, making card-heavy zones more valuable per trip than raw trip count suggests
- **847+ trips flagged as anomalies** with z-score > 3 vs their pickup zone average — concentrated in a small number of zones, suggesting either metering issues or systematic overcharging
- **Friday and Saturday nights are the highest revenue periods** — nearly double the revenue per hour compared to Monday and Tuesday mornings

---

## Architecture

```
NYC TLC S3 (parquet)
        │
        ▼
  DuckDB (extract + filter)
        │
        ▼
  Python (transform + batch load)
        │
        ▼
  MySQL 8.0 via Docker (storage)
        │
    5 SQL views
        │
        ▼
  export_csv.py (pandas export)
        │
        ▼
  Tableau Public (dashboards)
```

**Why this stack:**
- DuckDB reads 2.7M rows from a remote parquet file in under 10 seconds without downloading it first
- MySQL handles the aggregation layer via views so Tableau queries pre-computed results, not raw rows
- CSV export is required because Tableau Public does not support live database connections

---

## Stack

| Layer | Tool | Reason |
|---|---|---|
| Extraction | DuckDB | Reads parquet over HTTP, zero setup |
| Storage | MySQL 8.0 (Docker) | Reliable, widely understood, free |
| Transformation | SQL views | Logic lives in the database, not in Tableau |
| Export | Python + pandas | Reliable CSV output on Windows |
| Dashboards | Tableau Public 2026.2 | Free, publishable, shareable |
| Orchestration | Python CLI | `--mode full` and `--mode incremental` |

---

## Project structure

```
nyc-taxi-analytics/
├── scripts/
│   ├── data_pipeline.py      # Core ETL: extract, transform, load, build views
│   └── export_csv.py         # Export MySQL views to CSV for Tableau
├── sql/
│   ├── schema.sql            # trips table DDL
│   └── views.sql             # All 5 aggregated view definitions
├── data/
│   └── exports/              # Generated CSVs — gitignored
├── dashboards/               # Tableau .twbx workbook
├── docker-compose.yml        # MySQL 8.0 container
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Quickstart

### Prerequisites

- Python 3.9+
- Docker Desktop (must be open and running)
- Git Bash (Windows)

### Setup

```bash
git clone https://github.com/ashwinbasil/nyc-taxi-analytics.git
cd nyc-taxi-analytics

cp .env.example .env
# Edit .env with your MySQL credentials

docker-compose up -d
# Wait 20 seconds for MySQL to initialise

pip install -r requirements.txt
```

### Run the pipeline

```bash
cd scripts
python data_pipeline.py --mode full --month 2024-01
```

Downloads the parquet file, cleans data, loads 2.7M rows into MySQL, and builds all five views. Runs in roughly 2 minutes.

### Export to Tableau

```bash
python export_csv.py
```

Writes five clean CSVs to `data/exports/`. Open Tableau Public, connect via Text File, and load each one.

---

## Pipeline modes

```bash
# Full load: drop and reload everything
python data_pipeline.py --mode full --month 2024-01

# Incremental: append a new month without touching existing data
python data_pipeline.py --mode incremental --month 2024-02
```

---

## Data model

**Source table: `trips`**

~2.7M rows after filtering. Excludes zero-fare, zero-distance, zero-passenger, and duration outlier trips (under 1 min or over 300 min).

**Aggregated views:**

| View | Business question it answers |
|---|---|
| `daily_revenue` | How did revenue and trip volume trend across the month? |
| `hourly_patterns` | Which hours and days drive the most demand? |
| `zone_summary` | Which pickup zones are most valuable by volume and avg fare? |
| `payment_split` | How does payment method affect trip value and tip rate? |
| `anomalies` | Which trips have statistically unusual fares for their zone? |

---

## Anomaly detection

Trips are flagged if their fare deviates more than 3 standard deviations from the average fare in their pickup zone.

MySQL does not support `QUALIFY` for window function filtering, so the logic uses a subquery join:

```sql
SELECT t.*,
    ROUND(
        ABS(t.total_amount - z.avg_fare) / NULLIF(z.stddev_fare, 0)
    , 2) AS z_score
FROM trips t
JOIN (
    SELECT
        pickup_location_id,
        AVG(total_amount)    AS avg_fare,
        STDDEV(total_amount) AS stddev_fare
    FROM trips
    GROUP BY pickup_location_id
) z ON t.pickup_location_id = z.pickup_location_id
WHERE ABS(t.total_amount - z.avg_fare) / NULLIF(z.stddev_fare, 0) > 3
ORDER BY z_score DESC
LIMIT 1000;
```

This flags both overcharges (high z-score) and undercharges (large negative deviation), which can indicate metering errors, disputes, or data quality issues.

---

## Dashboards

Five sheets published to Tableau Public:

| Sheet | What it shows |
|---|---|
| Daily Revenue | Revenue and trip volume by day with trend line |
| Hourly Heatmap | Trip density by hour × day of week — shows rush hour and weekend patterns |
| Zone Performance | Top zones ranked by trips and avg fare, coloured by tip rate |
| Payment Split | Revenue and trip share by payment method |
| Anomaly Explorer | Flagged trips sorted by z-score with zone and fare details |

---

## Design decisions

**Why not PostgreSQL or Snowflake?**
MySQL was chosen deliberately to practise the most common database found in small-to-mid business environments. The SQL patterns (views, window functions, subquery joins) are portable to any RDBMS.

**Why CSV export instead of live connection?**
Tableau Public does not support live database connections. The export step is a deliberate part of the architecture, not a workaround — it also means the dashboard can be shared publicly without exposing database credentials.

**Why DuckDB for extraction and not direct MySQL load?**
DuckDB reads remote parquet files over HTTP in seconds without requiring a local download. It also handles type casting and filtering before the data touches MySQL, keeping the load step clean.

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

```bash
pip install -r requirements.txt
```

---

## What's next

- [ ] Load February and March 2024 data using `--mode incremental`
- [ ] Add a zone name lookup table (NYC TLC publishes a zone ID → name CSV)
- [ ] Schedule the pipeline with Windows Task Scheduler or cron
- [ ] Add data quality checks: row count validation, null rate alerts
- [ ] Publish Tableau dashboard to Tableau Public with public URL

---

## License

MIT
