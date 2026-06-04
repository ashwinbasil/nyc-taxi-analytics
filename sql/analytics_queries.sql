-- Pre-built Analytics Queries for Business Insights
-- Use these queries in Tableau or for ad-hoc analysis

USE nyc_taxi;

-- Query 1: Revenue by Zone & Time
SELECT 
    z.zone,
    DATE(t.pickup_datetime) as trip_date,
    HOUR(t.pickup_datetime) as trip_hour,
    COUNT(*) as trips,
    ROUND(AVG(t.fare_amount), 2) as avg_fare,
    ROUND(SUM(t.total_amount), 2) as total_revenue
FROM trips t
LEFT JOIN zones z ON t.pickup_location_id = z.location_id
WHERE DATE(t.pickup_datetime) >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY z.zone, DATE(t.pickup_datetime), HOUR(t.pickup_datetime)
ORDER BY total_revenue DESC;

-- Query 2: Tip Analysis by Payment Type
SELECT 
    pt.payment_type_name,
    COUNT(*) as transactions,
    ROUND(AVG(t.tip_amount), 2) as avg_tip,
    ROUND(AVG(t.tip_amount) / AVG(t.fare_amount) * 100, 2) as tip_percentage,
    ROUND(MAX(t.tip_amount), 2) as max_tip,
    ROUND(MIN(t.tip_amount), 2) as min_tip
FROM trips t
LEFT JOIN payment_types pt ON t.payment_type = pt.payment_type_id
GROUP BY pt.payment_type_name
ORDER BY avg_tip DESC;

-- Query 3: Peak Hours & Volume Trends
SELECT 
    HOUR(t.pickup_datetime) as hour,
    DAYNAME(t.pickup_datetime) as day_name,
    COUNT(*) as trip_volume,
    ROUND(AVG(t.trip_duration_minutes), 2) as avg_duration,
    ROUND(AVG(t.fare_amount), 2) as avg_fare,
    ROUND(AVG(t.tip_amount), 2) as avg_tip,
    ROUND(SUM(t.total_amount), 2) as total_revenue
FROM trips t
WHERE t.pickup_datetime >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY HOUR(t.pickup_datetime), DAYNAME(t.pickup_datetime)
ORDER BY trip_volume DESC;

-- Query 4: Driver Efficiency (Route Analysis)
SELECT 
    z_pickup.zone as pickup_zone,
    z_dropoff.zone as dropoff_zone,
    COUNT(*) as route_frequency,
    ROUND(AVG(t.trip_duration_minutes), 2) as avg_duration_minutes,
    ROUND(AVG(t.fare_amount), 2) as avg_fare,
    ROUND(AVG(t.fare_amount) / NULLIF(AVG(t.trip_duration_minutes), 0), 2) as revenue_per_minute,
    ROUND(SUM(t.total_amount), 2) as total_route_revenue
FROM trips t
LEFT JOIN zones z_pickup ON t.pickup_location_id = z_pickup.location_id
LEFT JOIN zones z_dropoff ON t.dropoff_location_id = z_dropoff.location_id
WHERE t.trip_duration_minutes BETWEEN 5 AND 120
GROUP BY z_pickup.zone, z_dropoff.zone
HAVING COUNT(*) > 50
ORDER BY revenue_per_minute DESC
LIMIT 20;

-- Query 5: Data Quality Monitoring
SELECT 
    DATE(t.pickup_datetime) as check_date,
    COUNT(*) as total_records,
    COUNT(DISTINCT t.pickup_location_id) as unique_zones,
    SUM(CASE WHEN t.fare_amount < 0 THEN 1 ELSE 0 END) as invalid_fares,
    SUM(CASE WHEN t.tip_amount < 0 THEN 1 ELSE 0 END) as invalid_tips,
    SUM(CASE WHEN t.trip_duration_minutes <= 0 THEN 1 ELSE 0 END) as invalid_duration,
    SUM(CASE WHEN t.pickup_location_id IS NULL THEN 1 ELSE 0 END) as null_pickup_zones
FROM trips t
GROUP BY DATE(t.pickup_datetime)
ORDER BY check_date DESC
LIMIT 90;

-- Query 6: Borough Comparison
SELECT 
    z.borough,
    DATE(t.pickup_datetime) as trip_date,
    COUNT(*) as trip_count,
    ROUND(AVG(t.fare_amount), 2) as avg_fare,
    ROUND(AVG(t.tip_amount), 2) as avg_tip,
    ROUND(SUM(t.total_amount), 2) as total_revenue,
    ROUND(AVG(t.trip_duration_minutes), 2) as avg_duration,
    ROUND(AVG(t.passenger_count), 2) as avg_passengers
FROM trips t
LEFT JOIN zones z ON t.pickup_location_id = z.location_id
WHERE DATE(t.pickup_datetime) >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY z.borough, DATE(t.pickup_datetime)
ORDER BY total_revenue DESC;

-- Query 7: Distance vs Revenue Analysis
SELECT 
    ROUND(t.trip_distance, 1) as distance_bucket,
    COUNT(*) as trip_count,
    ROUND(AVG(t.fare_amount), 2) as avg_fare,
    ROUND(AVG(t.tip_amount), 2) as avg_tip,
    ROUND(AVG(t.trip_duration_minutes), 2) as avg_duration,
    ROUND(SUM(t.total_amount), 2) as total_revenue,
    ROUND(AVG(t.passenger_count), 2) as avg_passengers
FROM trips t
WHERE t.trip_distance > 0
GROUP BY ROUND(t.trip_distance, 1)
ORDER BY distance_bucket;

-- Query 8: Monthly Trend Analysis
SELECT 
    DATE_FORMAT(t.pickup_datetime, '%Y-%m') as year_month,
    COUNT(*) as trip_volume,
    ROUND(SUM(t.total_amount), 2) as monthly_revenue,
    ROUND(AVG(t.fare_amount), 2) as avg_fare,
    ROUND(AVG(t.tip_amount), 2) as avg_tip,
    ROUND(AVG(t.passenger_count), 2) as avg_passengers,
    ROUND(AVG(t.trip_distance), 2) as avg_distance
FROM trips t
GROUP BY DATE_FORMAT(t.pickup_datetime, '%Y-%m')
ORDER BY year_month DESC;