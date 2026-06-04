# NYC Taxi Analytics - Data Dictionary

## Main Tables

### trips
Raw NYC Taxi trip transactions

| Column | Type | Description |
|--------|------|-------------|
| trip_id | BIGINT | Unique trip identifier |
| vendor_id | INT | Vendor ID |
| pickup_datetime | DATETIME | Trip start time |
| dropoff_datetime | DATETIME | Trip end time |
| passenger_count | INT | Number of passengers |
| trip_distance | DECIMAL(10,2) | Distance in miles |
| pickup_location_id | INT | Pickup zone code |
| dropoff_location_id | INT | Dropoff zone code |
| payment_type | INT | Payment method ID |
| fare_amount | DECIMAL(10,2) | Metered fare |
| extra | DECIMAL(10,2) | Surcharges |
| tip_amount | DECIMAL(10,2) | Tip amount |
| total_amount | DECIMAL(10,2) | Total fare |
| trip_duration_minutes | INT | Calculated trip duration |
| revenue_per_minute | DECIMAL(10,4) | Calculated revenue/min |

---

## Materialized Views

### daily_zone_metrics
Daily performance metrics by zone

| Column | Description |
|--------|-------------|
| trip_date | Date of trips |
| pickup_location_id | Zone ID |
| zone_name | Zone name |
| total_trips | Count of trips |
| avg_distance | Average distance |
| avg_fare | Average fare |
| avg_tip | Average tip |
| total_revenue | Total revenue |

### hourly_trends
Hourly time-series data

| Column | Description |
|--------|-------------|
| trip_date | Date |
| trip_hour | Hour (0-23) |
| trip_volume | Trips in hour |
| avg_fare | Average fare |
| avg_tip | Average tip |
| total_revenue | Hour revenue |

### payment_analysis
Payment method analysis

| Column | Description |
|--------|-------------|
| trip_date | Date |
| payment_type_name | Payment method |
| transaction_count | # transactions |
| avg_tip | Average tip |
| tip_percentage | Tip % of fare |
| total_revenue | Total revenue |

### route_efficiency
Top pickup-dropoff routes

| Column | Description |
|--------|-------------|
| pickup_zone | Pickup zone |
| dropoff_zone | Dropoff zone |
| route_frequency | Times used |
| avg_fare | Average fare |
| revenue_per_minute | Revenue/min |
| total_route_revenue | Total revenue |

---

## Key Metrics

### Business KPIs
- **Total Revenue**: SUM(total_amount)
- **Average Fare**: AVG(fare_amount)
- **Tip Percentage**: AVG(tip_amount) / AVG(fare_amount) × 100
- **Revenue Per Minute**: AVG(fare_amount) / AVG(trip_duration_minutes)

### Data Quality
- **Data Freshness**: MAX(pickup_datetime)
- **Load Success Rate**: % of successful pipeline runs
