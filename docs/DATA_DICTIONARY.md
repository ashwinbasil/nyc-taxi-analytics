# NYC Taxi Analytics - Data Dictionary

## Main Tables

### trips
Raw NYC Taxi trip transactions with 100M+ row capacity

| Column | Type | Description |
|--------|------|-------------|
| trip_id | BIGINT | Unique trip identifier |
| vendor_id | INT | Vendor ID (1 or 2) |
| pickup_datetime | DATETIME | Trip start time |
| dropoff_datetime | DATETIME | Trip end time |
| passenger_count | INT | Number of passengers |
| trip_distance | DECIMAL(10,2) | Distance in miles |
| rate_code_id | INT | Rate code (1=Standard) |
| store_and_fwd_flag | CHAR(1) | Y/N |
| pickup_location_id | INT | Pickup zone code (1-263) |
| dropoff_location_id | INT | Dropoff zone code |
| payment_type | INT | Payment method ID (1-6) |
| fare_amount | DECIMAL(10,2) | Metered fare |
| extra | DECIMAL(10,2) | Surcharges |
| mta_tax | DECIMAL(10,2) | MTA tax (0.50) |
| tip_amount | DECIMAL(10,2) | Tip amount |
| tolls_amount | DECIMAL(10,2) | Tolls paid |
| total_amount | DECIMAL(10,2) | Total fare + surcharges + tip |
| congestion_surcharge | DECIMAL(10,2) | NYC congestion pricing |
| airport_fee | DECIMAL(10,2) | Airport fee |
| trip_duration_minutes | INT | **Calculated**: Trip duration |
| revenue_per_minute | DECIMAL(10,4) | **Calculated**: Fare/Duration |

**Indexes**: pickup_datetime, dropoff_datetime, payment_type, pickup_location_id, fare_amount

---

## Materialized Views (Pre-aggregated)

### daily_zone_metrics
Daily performance metrics aggregated by zone

| Column | Description |
|--------|-------------|
| trip_date | Date of trips |
| pickup_location_id | Zone ID |
| zone_name | Zone name |
| borough | NYC borough |
| total_trips | Count of trips |
| avg_distance | Average trip distance |
| avg_fare | Average fare amount |
| avg_tip | Average tip |
| total_revenue | Total revenue (sum) |
| credit_card_trips | Credit card transaction count |
| cash_trips | Cash transaction count |

### hourly_trends
Hourly time-series data for peak hours analysis

| Column | Description |
|--------|-------------|
| trip_date | Date |
| trip_hour | Hour of day (0-23) |
| day_name | Day name (Monday, etc) |
| trip_volume | Number of trips |
| avg_fare | Average fare |
| total_revenue | Hour revenue |
| avg_tip_percentage | Avg tip as % of fare |

### payment_analysis
Payment method trends and tipping behavior

| Column | Description |
|--------|-------------|
| trip_date | Date |
| payment_type_name | Payment method (Credit card, Cash, etc) |
| transaction_count | # transactions |
| avg_fare | Average fare |
| avg_tip | Average tip |
| tip_percentage | Tip % of fare |
| total_revenue | Total revenue |

### route_efficiency
Top pickup-dropoff combinations for route optimization

| Column | Description |
|--------|-------------|
| pickup_zone | Pickup zone name |
| dropoff_zone | Dropoff zone name |
| route_frequency | Times this route was used |
| avg_fare | Average fare for route |
| revenue_per_minute | Avg fare ÷ Duration |
| total_route_revenue | Total revenue from route |

### zone_heatmap
Geographic heatmap data for map visualization

| Column | Description |
|--------|-------------|
| location_id | Zone ID (1-263) |
| zone | Zone name |
| borough | Borough name |
| total_trips | Total trips from zone |
| total_revenue | Total revenue |
| avg_fare | Average fare |

### monthly_metrics
Month-over-month trend analysis

| Column | Description |
|--------|-------------|
| year_month | YYYY-MM format |
| trip_volume | Total trips |
| total_revenue | Total revenue |
| avg_fare | Average fare |
| avg_tip | Average tip |

---

## Reference Tables

### zones
NYC geographic zones

| Column | Description |
|--------|-------------|
| location_id | Zone ID (1-263) |
| borough | NYC borough |
| zone | Zone name |

### payment_types
Payment method codes

| payment_type_id | payment_type_name |
|-----------------|-------------------|
| 1 | Credit card |
| 2 | Cash |
| 3 | No charge |
| 4 | Dispute |
| 5 | Unknown |
| 6 | Voided trip |

---

## Key Business Metrics

- **Total Revenue**: SUM(total_amount)
- **Average Fare**: AVG(fare_amount)
- **Tip Percentage**: AVG(tip_amount) / AVG(fare_amount) × 100
- **Revenue Per Minute**: AVG(fare_amount) / AVG(trip_duration_minutes)
- **Average Trip Duration**: AVG(trip_duration_minutes)

---

## Monitoring Tables

### pipeline_logs
Data pipeline execution history

| Column | Description |
|--------|-------------|
| execution_date | When pipeline ran |
| pipeline_mode | 'full' or 'incremental' |
| records_loaded | Number of records |
| execution_time_seconds | Pipeline duration |
| status | 'SUCCESS' or 'FAILED' |
| error_message | Error details if failed |
