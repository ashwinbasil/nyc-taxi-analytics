# NYC Taxi Analytics System

End-to-end SQL + Dashboard system with real NYC Taxi dataset (100M+ rows). Demonstrates operational analytics, automated data pipelines, and business insights through Tableau dashboards.

## 📊 System Architecture

```
DuckDB/CSV (NYC Taxi Data)
          ↓
     Data Pipeline (Python)
          ↓
    MySQL Database
          ↓
   Materialized Views
   (Aggregated Tables)
          ↓
   Tableau Dashboard
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.9+
- MySQL 8.0+
- Tableau Desktop/Server or Tableau Public (free)
- DuckDB (auto-installed via pip)

### 1. Spin up MySQL

```bash
docker-compose up -d mysql
```

Verify connection:
```bash
mysql -h 127.0.0.1 -u root -proot_password
```

### 2. Load NYC Taxi Data

```bash
# Install dependencies
pip install -r requirements.txt

# Download & ingest data (first run: ~5-10 mins)
python scripts/data_pipeline.py --mode full

# Subsequent incremental runs
python scripts/data_pipeline.py --mode incremental
```

### 3. Create Analytics Views

```bash
mysql -h 127.0.0.1 -u root -proot_password < sql/schema.sql
mysql -h 127.0.0.1 -u root -proot_password < sql/materialized_views.sql
```

### 4. Connect Tableau

- **Data Source**: MySQL (localhost:3306)
- **Database**: `nyc_taxi`
- **Suggested Tables**: 
  - `daily_zone_metrics` (pre-aggregated)
  - `hourly_trends` (time-series)
  - `trips` (raw data for drill-down)

---

## 📁 Project Structure

```
.
├── README.md
├── docker-compose.yml           # MySQL + phpmyadmin setup
├── requirements.txt             # Python dependencies
├── sql/
│   ├── schema.sql               # Base tables
│   ├── materialized_views.sql   # Aggregated tables for dashboards
│   └── analytics_queries.sql    # Business queries (examples)
├── scripts/
│   ├── data_pipeline.py         # Main ETL script
│   ├── config.py                # Database config
│   └── scheduler.sh             # Cron automation setup
├── tableau/
│   ├── dashboard_specs.md       # Dashboard design specs
│   └── sample_queries.sql       # Pre-built queries for Tableau
├── .env.example                 # Environment variables template
└── docs/
    ├── DEPLOYMENT.md            # Production deployment guide
    ├── TROUBLESHOOTING.md       # Common issues & fixes
    └── DATA_DICTIONARY.md       # Schema documentation
```

---

## 💡 Business Insights (Sample Queries)

### 1. Revenue by Zone & Time
```sql
SELECT 
    zone,
    DATE(pickup_datetime) as date,
    HOUR(pickup_datetime) as hour,
    COUNT(*) as trips,
    AVG(fare_amount) as avg_fare,
    SUM(total_amount) as total_revenue
FROM trips
WHERE DATE(pickup_datetime) >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY zone, DATE(pickup_datetime), HOUR(pickup_datetime)
ORDER BY total_revenue DESC;
```

### 2. Tip Analysis by Payment Type
```sql
SELECT 
    payment_type,
    COUNT(*) as transactions,
    AVG(tip_amount) as avg_tip,
    ROUND(AVG(tip_amount) / AVG(fare_amount) * 100, 2) as tip_percentage,
    MAX(tip_amount) as max_tip
FROM trips
GROUP BY payment_type
ORDER BY avg_tip DESC;
```

### 3. Peak Hours & Volume Trends
```sql
SELECT 
    HOUR(pickup_datetime) as hour,
    COUNT(*) as trip_volume,
    AVG(trip_duration_minutes) as avg_duration,
    AVG(fare_amount) as avg_fare,
    AVG(tip_amount) as avg_tip
FROM trips
GROUP BY HOUR(pickup_datetime)
ORDER BY hour;
```

### 4. Driver Efficiency (Trip Duration Analysis)
```sql
SELECT 
    pickup_zone,
    dropoff_zone,
    COUNT(*) as route_frequency,
    AVG(trip_duration_minutes) as avg_duration,
    AVG(fare_amount) as avg_fare,
    ROUND(AVG(fare_amount) / AVG(trip_duration_minutes), 2) as revenue_per_minute
FROM trips
WHERE trip_duration_minutes BETWEEN 5 AND 120
GROUP BY pickup_zone, dropoff_zone
HAVING COUNT(*) > 100
ORDER BY revenue_per_minute DESC
LIMIT 20;
```

### 5. Data Quality Monitoring
```sql
SELECT 
    DATE(pickup_datetime) as date,
    COUNT(*) as total_records,
    COUNT(DISTINCT pickup_zone) as unique_zones,
    SUM(CASE WHEN fare_amount < 0 THEN 1 ELSE 0 END) as invalid_fares,
    SUM(CASE WHEN tip_amount < 0 THEN 1 ELSE 0 END) as invalid_tips,
    SUM(CASE WHEN trip_duration_minutes <= 0 THEN 1 ELSE 0 END) as invalid_duration
FROM trips
GROUP BY DATE(pickup_datetime)
ORDER BY date DESC;
```

---

## 📊 Dashboard Specs (Tableau)

### Dashboard 1: Daily Operations
- **KPIs**: Total trips, Revenue, Avg Fare, Avg Tip %
- **Charts**: 
  - Line chart: Daily trip volume (last 30 days)
  - Bar chart: Revenue by zone
  - Scatter: Fare vs. Trip Duration

### Dashboard 2: Zone Performance
- **Map**: Trip count heatmap by pickup zone
- **Table**: Top 10 zones by revenue
- **Filter**: Date range, Zone, Payment type

### Dashboard 3: Peak Hours Analysis
- **Heatmap**: Trip volume by hour × day of week
- **Line**: Revenue trend (hourly)
- **Bar**: Avg fare & tip by hour

### Dashboard 4: Payment Trends
- **Pie**: Payment type distribution
- **Bar**: Tip % by payment type
- **Trend**: Monthly payment method shifts

---

## 🔄 Automation & Scheduling

### Local Development (Manual Refresh)
```bash
# One-time full load
python scripts/data_pipeline.py --mode full

# Daily incremental run
python scripts/data_pipeline.py --mode incremental
```

### Production (Automated Cron)
```bash
# Edit crontab
crontab -e

# Add scheduled job (daily at 2 AM)
0 2 * * * cd /path/to/nyc-taxi-analytics && python scripts/data_pipeline.py --mode incremental >> logs/pipeline.log 2>&1
```

### Docker Compose Full Stack
```bash
docker-compose up -d
```

---

## 🗄️ Data Pipeline Details

### Source Data
- **NYC Taxi Dataset** (BigQuery public dataset)
- **Format**: Parquet files from DuckDB
- **Frequency**: Daily updates (production)
- **Volume**: 100M+ historical rows, ~50K new rows/day

### ETL Steps
1. **Extract**: Query BigQuery or download from DuckDB
2. **Transform**: 
   - Parse timestamps
   - Calculate trip duration
   - Validate data ranges
   - Handle nulls & outliers
3. **Load**: Batch insert into MySQL
4. **Aggregate**: Refresh materialized views

### Performance Optimizations
- ✅ Indexes on `pickup_datetime`, `zone`, `payment_type`
- ✅ Partitioning by date (for large tables)
- ✅ Pre-aggregated tables for dashboard queries
- ✅ Connection pooling (MySQL)

---

## 🔧 Configuration

Edit `.env` to customize:
```bash
# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root_password
MYSQL_DATABASE=nyc_taxi

# Data Pipeline
BATCH_SIZE=10000
MAX_WORKERS=4
LOG_LEVEL=INFO

# NYC Taxi Data (BigQuery)
BIGQUERY_PROJECT=bigquery-public-data
BIGQUERY_DATASET=new_york_taxi
```

---

## 📈 Expected Outcomes

After setup, you'll have:

✅ **100M+ rows** of NYC Taxi data in MySQL  
✅ **5 Tableau dashboards** with interactive drill-downs  
✅ **Automated daily pipeline** refreshing data  
✅ **Pre-built SQL queries** for common business questions  
✅ **Production-ready setup** with logging & monitoring  

---

## 🐛 Troubleshooting

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for:
- MySQL connection issues
- Data pipeline failures
- Tableau connection problems
- Performance optimization

---

## 📚 Additional Resources

- [NYC Taxi Dataset Docs](https://cloud.google.com/bigquery/public-data/nyc-tlc-trips)
- [MySQL Best Practices](docs/DEPLOYMENT.md)
- [Tableau Connection Guide](tableau/dashboard_specs.md)
- [Data Dictionary](docs/DATA_DICTIONARY.md)

---

## 📝 License

MIT License - Use for learning & demonstration purposes.

**Last Updated**: June 2026  
**Author**: ashwinbasil
