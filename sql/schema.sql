-- NYC Taxi Analytics Schema
-- Create base tables for NYC Taxi Yellow Trips data

USE nyc_taxi;

-- Main trips table
CREATE TABLE IF NOT EXISTS trips (
    trip_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    vendor_id INT NOT NULL,
    pickup_datetime DATETIME NOT NULL,
    dropoff_datetime DATETIME NOT NULL,
    passenger_count INT NOT NULL,
    trip_distance DECIMAL(10, 2),
    rate_code_id INT,
    store_and_fwd_flag CHAR(1),
    pickup_location_id INT,
    dropoff_location_id INT,
    payment_type INT NOT NULL,
    fare_amount DECIMAL(10, 2) NOT NULL,
    extra DECIMAL(10, 2),
    mta_tax DECIMAL(10, 2),
    tip_amount DECIMAL(10, 2),
    tolls_amount DECIMAL(10, 2),
    total_amount DECIMAL(10, 2) NOT NULL,
    congestion_surcharge DECIMAL(10, 2),
    airport_fee DECIMAL(10, 2),
    
    -- Calculated fields
    trip_duration_minutes INT,
    revenue_per_minute DECIMAL(10, 4),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    INDEX idx_pickup_datetime (pickup_datetime),
    INDEX idx_dropoff_datetime (dropoff_datetime),
    INDEX idx_payment_type (payment_type),
    INDEX idx_pickup_location (pickup_location_id),
    INDEX idx_dropoff_location (dropoff_location_id),
    INDEX idx_vendor_id (vendor_id),
    INDEX idx_trip_distance (trip_distance),
    INDEX idx_fare_amount (fare_amount),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Zone lookup table
CREATE TABLE IF NOT EXISTS zones (
    location_id INT PRIMARY KEY,
    borough VARCHAR(50),
    zone VARCHAR(100),
    service_zone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Payment type lookup
CREATE TABLE IF NOT EXISTS payment_types (
    payment_type_id INT PRIMARY KEY,
    payment_type_name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert payment type reference data
INSERT IGNORE INTO payment_types (payment_type_id, payment_type_name) VALUES
(1, 'Credit card'),
(2, 'Cash'),
(3, 'No charge'),
(4, 'Dispute'),
(5, 'Unknown'),
(6, 'Voided trip');

-- Data quality monitoring table
CREATE TABLE IF NOT EXISTS data_quality_logs (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    check_date DATE NOT NULL,
    table_name VARCHAR(100),
    total_records BIGINT,
    invalid_fares INT,
    invalid_tips INT,
    invalid_duration INT,
    null_zones INT,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_check_date (check_date),
    INDEX idx_table_name (table_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Pipeline execution log
CREATE TABLE IF NOT EXISTS pipeline_logs (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    execution_date DATETIME NOT NULL,
    pipeline_mode VARCHAR(50),
    records_loaded BIGINT,
    execution_time_seconds INT,
    status VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_execution_date (execution_date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;