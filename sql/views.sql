CREATE OR REPLACE VIEW daily_revenue AS
SELECT
    DATE(pickup_datetime)                            AS day,
    COUNT(*)                                         AS trips,
    ROUND(SUM(total_amount), 2)                      AS revenue,
    ROUND(AVG(total_amount), 2)                      AS avg_fare,
    ROUND(AVG(tip_amount / NULLIF(fare_amount,0) * 100), 1) AS avg_tip_pct
FROM trips
GROUP BY DATE(pickup_datetime)
ORDER BY day;

CREATE OR REPLACE VIEW hourly_patterns AS
SELECT
    HOUR(pickup_datetime)                            AS hour,
    DAYNAME(pickup_datetime)                         AS day_name,
    COUNT(*)                                         AS trips,
    ROUND(SUM(total_amount), 2)                      AS revenue,
    ROUND(AVG(trip_duration_minutes), 1)             AS avg_duration_mins
FROM trips
GROUP BY HOUR(pickup_datetime), DAYNAME(pickup_datetime);

CREATE OR REPLACE VIEW zone_summary AS
SELECT
    pickup_location_id                               AS zone_id,
    COUNT(*)                                         AS trips,
    ROUND(AVG(total_amount), 2)                      AS avg_fare,
    ROUND(AVG(trip_distance), 2)                     AS avg_distance_miles,
    ROUND(AVG(tip_amount / NULLIF(fare_amount,0) * 100), 1) AS avg_tip_pct,
    ROUND(SUM(total_amount), 2)                      AS total_revenue
FROM trips
WHERE fare_amount > 0
GROUP BY pickup_location_id
ORDER BY trips DESC;

CREATE OR REPLACE VIEW payment_split AS
SELECT
    CASE payment_type
        WHEN 1 THEN 'Credit card'
        WHEN 2 THEN 'Cash'
        WHEN 3 THEN 'No charge'
        WHEN 4 THEN 'Dispute'
        WHEN 5 THEN 'App or digital'
        ELSE        'Other'
    END                                              AS payment_label,
    COUNT(*)                                         AS trips,
    ROUND(SUM(total_amount), 2)                      AS revenue,
    ROUND(AVG(tip_amount), 2)                        AS avg_tip
FROM trips
GROUP BY payment_type;

CREATE OR REPLACE VIEW anomalies AS
SELECT
    t.id,
    t.pickup_datetime,
    t.pickup_location_id                             AS zone_id,
    t.total_amount                                   AS fare,
    t.trip_distance,
    t.payment_type,
    ROUND(
        ABS(t.total_amount - z.avg_fare)
        / NULLIF(z.stddev_fare, 0)
    , 2)                                             AS z_score
FROM trips t
JOIN (
    SELECT
        pickup_location_id,
        AVG(total_amount)    AS avg_fare,
        STDDEV(total_amount) AS stddev_fare
    FROM trips
    GROUP BY pickup_location_id
) z ON t.pickup_location_id = z.pickup_location_id
WHERE ABS(t.total_amount - z.avg_fare)
    / NULLIF(z.stddev_fare, 0) > 3
ORDER BY z_score DESC
LIMIT 1000;
