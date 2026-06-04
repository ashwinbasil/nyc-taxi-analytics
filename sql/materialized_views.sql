-- Materialized Views for Analytics & Dashboards
-- Pre-aggregated tables for optimal Tableau performance

USE nyc_taxi;

-- Daily zone metrics (for daily operations dashboard)
CREATE TABLE IF NOT EXISTS daily_zone_metrics (
    trip_date DATE,
    pickup_location_id INT,
    zone_name VARCHAR(100),
    borough VARCHAR(50),
    total_trips BIGINT,
    days_active INT,
    avg_distance DECIMAL(10, 2),
    avg_duration_minutes DECIMAL(10, 2),
    avg_fare DECIMAL(10, 2),
    avg_tip DECIMAL(10, 2),
    total_revenue DECIMAL(15, 2),
    revenue_per_trip DECIMAL(10, 2),
    avg_passengers DECIMAL(10, 2),
    max_fare DECIMAL(10, 2),
    min_fare DECIMAL(10, 2),
    credit_card_trips BIGINT,
    cash_trips BIGINT,
    last_updated TIMESTAMP,
    PRIMARY KEY (trip_date, pickup_location_id),
    INDEX idx_date (trip_date),
    INDEX idx_zone (pickup_location_id),
    INDEX idx_borough (borough)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Hourly trends (for time-series analysis)
CREATE TABLE IF NOT EXISTS hourly_trends (
    trip_date DATE,
    trip_hour INT,
    day_name VARCHAR(20),
    day_of_week INT,
    trip_volume BIGINT,
    avg_distance DECIMAL(10, 2),
    avg_duration_minutes DECIMAL(10, 2),
    avg_fare DECIMAL(10, 2),
    avg_tip DECIMAL(10, 2),
    total_revenue DECIMAL(15, 2),
    avg_passengers DECIMAL(10, 2),
    unique_zones INT,
    avg_tip_percentage DECIMAL(10, 2),
    last_updated TIMESTAMP,
    PRIMARY KEY (trip_date, trip_hour),
    INDEX idx_date (trip_date),
    INDEX idx_hour (trip_hour),
    INDEX idx_dow (day_of_week)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Payment type analysis
CREATE TABLE IF NOT EXISTS payment_analysis (
    trip_date DATE,
    payment_type_name VARCHAR(50),
    transaction_count BIGINT,
    avg_fare DECIMAL(10, 2),
    avg_tip DECIMAL(10, 2),
    tip_percentage DECIMAL(10, 2),
    total_revenue DECIMAL(15, 2),
    avg_total_amount DECIMAL(10, 2),
    max_tip DECIMAL(10, 2),
    min_tip DECIMAL(10, 2),
    last_updated TIMESTAMP,
    PRIMARY KEY (trip_date, payment_type_name),
    INDEX idx_date (trip_date),
    INDEX idx_payment_type (payment_type_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Route efficiency (top pickup-dropoff combinations)
CREATE TABLE IF NOT EXISTS route_efficiency (
    pickup_zone VARCHAR(100),
    dropoff_zone VARCHAR(100),
    pickup_borough VARCHAR(50),
    dropoff_borough VARCHAR(50),
    route_frequency BIGINT,
    avg_distance DECIMAL(10, 2),
    avg_duration_minutes DECIMAL(10, 2),
    avg_fare DECIMAL(10, 2),
    avg_tip DECIMAL(10, 2),
    revenue_per_minute DECIMAL(10, 4),
    total_route_revenue DECIMAL(15, 2),
    days_active INT,
    last_updated TIMESTAMP,
    PRIMARY KEY (pickup_zone, dropoff_zone),
    INDEX idx_pickup (pickup_zone),
    INDEX idx_dropoff (dropoff_zone),
    INDEX idx_frequency (route_frequency)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Zone heatmap data (for geographic visualization)
CREATE TABLE IF NOT EXISTS zone_heatmap (
    location_id INT PRIMARY KEY,
    zone VARCHAR(100),
    borough VARCHAR(50),
    total_trips BIGINT,
    avg_fare DECIMAL(10, 2),
    total_revenue DECIMAL(15, 2),
    avg_tip DECIMAL(10, 2),
    days_active INT,
    max_fare DECIMAL(10, 2),
    min_fare DECIMAL(10, 2),
    last_updated TIMESTAMP,
    INDEX idx_zone (zone),
    INDEX idx_borough (borough),
    INDEX idx_revenue (total_revenue)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Monthly comparison (for trend analysis)
CREATE TABLE IF NOT EXISTS monthly_metrics (
    year INT,
    month INT,
    year_month VARCHAR(7),
    trip_volume BIGINT,
    days_in_month INT,
    avg_distance DECIMAL(10, 2),
    avg_duration DECIMAL(10, 2),
    total_revenue DECIMAL(15, 2),
    avg_fare DECIMAL(10, 2),
    avg_tip DECIMAL(10, 2),
    avg_passengers DECIMAL(10, 2),
    credit_card_pct BIGINT,
    cash_pct BIGINT,
    last_updated TIMESTAMP,
    PRIMARY KEY (year, month),
    INDEX idx_year_month (year_month),
    INDEX idx_revenue (total_revenue)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;