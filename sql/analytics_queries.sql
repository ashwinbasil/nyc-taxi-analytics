-- Rolling 7-day revenue
SELECT
    day,
    revenue,
    ROUND(AVG(revenue) OVER (
        ORDER BY day
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2) AS revenue_7d_avg,
    trips
FROM daily_revenue
ORDER BY day;

-- Peak hour by day of week
SELECT
    day_name,
    hour,
    trips,
    revenue
FROM hourly_patterns
WHERE (day_name, trips) IN (
    SELECT day_name, MAX(trips)
    FROM hourly_patterns
    GROUP BY day_name
)
ORDER BY FIELD(day_name,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday');

-- Zone revenue per mile (efficiency metric)
SELECT
    zone_id,
    avg_fare,
    avg_distance_miles,
    ROUND(avg_fare / NULLIF(avg_distance_miles, 0), 2) AS revenue_per_mile,
    trips
FROM zone_summary
ORDER BY revenue_per_mile DESC
LIMIT 20;

-- Payment type revenue share
SELECT
    payment_label,
    trips,
    revenue,
    ROUND(revenue / SUM(revenue) OVER () * 100, 1) AS revenue_share_pct
FROM payment_split
ORDER BY revenue DESC;
