#!/usr/bin/env python3
import os
import sys
import logging
import argparse
from datetime import datetime

import duckdb
import pandas as pd
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

class Config:
    MYSQL_HOST     = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT     = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER     = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root_password")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "nyc_taxi")
    BATCH_SIZE     = int(os.getenv("BATCH_SIZE", 5000))
    LOG_LEVEL      = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls):
        missing = [
            k for k in ["MYSQL_HOST", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE"]
            if not getattr(cls, k)
        ]
        if missing:
            raise ValueError(f"Missing required config: {', '.join(missing)}")

logging.basicConfig(
    level=Config.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline.log"),
    ],
)
log = logging.getLogger(__name__)


class NYCTaxiPipeline:

    def __init__(self):
        Config.validate()
        self.mysql_config = {
            "host":     Config.MYSQL_HOST,
            "port":     Config.MYSQL_PORT,
            "user":     Config.MYSQL_USER,
            "password": Config.MYSQL_PASSWORD,
            "database": Config.MYSQL_DATABASE,
        }
        self.batch_size = Config.BATCH_SIZE
        log.info("Pipeline initialised.")

    def connect(self):
        try:
            conn = mysql.connector.connect(**self.mysql_config)
            log.info("Connected to MySQL.")
            return conn
        except mysql.connector.Error as e:
            log.error(f"MySQL connection failed: {e}")
            raise

    def create_schema(self, conn):
        log.info("Creating schema...")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                id                    BIGINT AUTO_INCREMENT PRIMARY KEY,
                vendor_id             TINYINT,
                pickup_datetime       DATETIME,
                dropoff_datetime      DATETIME,
                passenger_count       TINYINT,
                trip_distance         FLOAT,
                pickup_location_id    SMALLINT,
                dropoff_location_id   SMALLINT,
                payment_type          TINYINT,
                fare_amount           DECIMAL(8,2),
                extra                 DECIMAL(6,2),
                mta_tax               DECIMAL(6,2),
                tip_amount            DECIMAL(8,2),
                tolls_amount          DECIMAL(8,2),
                congestion_surcharge  DECIMAL(6,2),
                airport_fee           DECIMAL(6,2),
                total_amount          DECIMAL(8,2),
                trip_duration_minutes FLOAT,
                revenue_per_minute    DECIMAL(8,4),
                INDEX idx_pickup  (pickup_datetime),
                INDEX idx_pu_zone (pickup_location_id),
                INDEX idx_payment (payment_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        conn.commit()
        cursor.close()
        log.info("Schema ready.")

    def extract(self, month: str) -> pd.DataFrame:
        url = (
            "https://d37ci6vzurychx.cloudfront.net/trip-data/"
            f"yellow_tripdata_{month}.parquet"
        )
        log.info(f"Downloading: {url}")

        year, mon = map(int, month.split("-"))
        if mon == 12:
            next_month = f"{year + 1}-01-01"
        else:
            next_month = f"{year}-{mon + 1:02d}-01"

        con = duckdb.connect()
        con.execute("INSTALL httpfs; LOAD httpfs;")

        df = con.execute(f"""
            SELECT
                VendorID                                    AS vendor_id,
                tpep_pickup_datetime                        AS pickup_datetime,
                tpep_dropoff_datetime                       AS dropoff_datetime,
                CAST(passenger_count AS INTEGER)            AS passenger_count,
                ROUND(trip_distance, 2)                     AS trip_distance,
                PULocationID                                AS pickup_location_id,
                DOLocationID                                AS dropoff_location_id,
                payment_type,
                ROUND(fare_amount, 2)                       AS fare_amount,
                ROUND(COALESCE(extra, 0), 2)                AS extra,
                ROUND(COALESCE(mta_tax, 0), 2)              AS mta_tax,
                ROUND(COALESCE(tip_amount, 0), 2)           AS tip_amount,
                ROUND(COALESCE(tolls_amount, 0), 2)         AS tolls_amount,
                ROUND(COALESCE(congestion_surcharge, 0), 2) AS congestion_surcharge,
                ROUND(COALESCE(airport_fee, 0), 2)          AS airport_fee,
                ROUND(total_amount, 2)                      AS total_amount,
                date_diff('minute',
                    tpep_pickup_datetime,
                    tpep_dropoff_datetime)                  AS trip_duration_minutes,
                ROUND(
                    fare_amount / NULLIF(date_diff('minute',
                        tpep_pickup_datetime,
                        tpep_dropoff_datetime), 0)
                , 4)                                        AS revenue_per_minute
            FROM read_parquet('{url}')
            WHERE total_amount    > 0
              AND fare_amount     > 0
              AND trip_distance   > 0
              AND passenger_count > 0
              AND tpep_pickup_datetime >= '{month}-01'
              AND tpep_pickup_datetime <  '{next_month}'
              AND date_diff('minute',
                    tpep_pickup_datetime,
                    tpep_dropoff_datetime) BETWEEN 1 AND 300
        """).df()

        con.close()
        log.info(f"Extracted {len(df):,} rows.")
        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        log.info("Transforming...")
        before = len(df)
        df = df.dropna(subset=["pickup_datetime", "fare_amount", "total_amount"])
        df["pickup_datetime"]  = pd.to_datetime(df["pickup_datetime"])
        df["dropoff_datetime"] = pd.to_datetime(df["dropoff_datetime"])
        df["fare_amount"]  = df["fare_amount"].clip(upper=500)
        df["total_amount"] = df["total_amount"].clip(upper=500)
        df["tip_amount"]   = df["tip_amount"].clip(lower=0, upper=200)
        log.info(f"Transform done. {before:,} in, {len(df):,} out.")
        return df

    def load(self, df: pd.DataFrame, conn, mode: str) -> int:
        cursor = conn.cursor()
        records_loaded = 0

        if mode == "full":
            log.info("Full mode: truncating trips table...")
            cursor.execute("TRUNCATE TABLE trips;")
            conn.commit()

        log.info(f"Loading {len(df):,} rows in batches of {self.batch_size}...")

        insert_sql = """
            INSERT INTO trips (
                vendor_id, pickup_datetime, dropoff_datetime,
                passenger_count, trip_distance,
                pickup_location_id, dropoff_location_id,
                payment_type, fare_amount, extra, mta_tax,
                tip_amount, tolls_amount, congestion_surcharge,
                airport_fee, total_amount,
                trip_duration_minutes, revenue_per_minute
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s
            )
        """

        cols = [
            "vendor_id", "pickup_datetime", "dropoff_datetime",
            "passenger_count", "trip_distance",
            "pickup_location_id", "dropoff_location_id",
            "payment_type", "fare_amount", "extra", "mta_tax",
            "tip_amount", "tolls_amount", "congestion_surcharge",
            "airport_fee", "total_amount",
            "trip_duration_minutes", "revenue_per_minute",
        ]

        try:
            for i in range(0, len(df), self.batch_size):
                batch = df.iloc[i : i + self.batch_size][cols]
                rows = [tuple(r) for r in batch.itertuples(index=False)]
                cursor.executemany(insert_sql, rows)
                records_loaded += cursor.rowcount
                conn.commit()
                log.info(f"  {records_loaded:,} rows loaded so far...")

            log.info(f"Load complete. {records_loaded:,} total rows.")
            return records_loaded

        except mysql.connector.Error as e:
            conn.rollback()
            log.error(f"Load failed: {e}")
            raise
        finally:
            cursor.close()

    def create_views(self, conn):
        log.info("Building Tableau views...")
        cursor = conn.cursor()

        views = {
            "daily_revenue": """
                SELECT
                    DATE(pickup_datetime)                       AS day,
                    COUNT(*)                                    AS trips,
                    ROUND(SUM(total_amount), 2)                 AS revenue,
                    ROUND(AVG(total_amount), 2)                 AS avg_fare,
                    ROUND(AVG(tip_amount / NULLIF(fare_amount, 0) * 100), 1) AS avg_tip_pct
                FROM trips
                GROUP BY DATE(pickup_datetime)
                ORDER BY day
            """,
            "hourly_patterns": """
                SELECT
                    HOUR(pickup_datetime)                       AS hour,
                    DAYNAME(pickup_datetime)                    AS day_name,
                    COUNT(*)                                    AS trips,
                    ROUND(SUM(total_amount), 2)                 AS revenue,
                    ROUND(AVG(trip_duration_minutes), 1)        AS avg_duration_mins
                FROM trips
                GROUP BY HOUR(pickup_datetime), DAYNAME(pickup_datetime)
            """,
            "zone_summary": """
                SELECT
                    pickup_location_id                          AS zone_id,
                    COUNT(*)                                    AS trips,
                    ROUND(AVG(total_amount), 2)                 AS avg_fare,
                    ROUND(AVG(trip_distance), 2)                AS avg_distance_miles,
                    ROUND(AVG(tip_amount / NULLIF(fare_amount, 0) * 100), 1) AS avg_tip_pct,
                    ROUND(SUM(total_amount), 2)                 AS total_revenue
                FROM trips
                WHERE fare_amount > 0
                GROUP BY pickup_location_id
                ORDER BY trips DESC
            """,
            "payment_split": """
                SELECT
                    CASE payment_type
                        WHEN 1 THEN 'Credit card'
                        WHEN 2 THEN 'Cash'
                        WHEN 3 THEN 'No charge'
                        WHEN 4 THEN 'Dispute'
                        WHEN 5 THEN 'App or digital'
                        ELSE        'Other'
                    END                                         AS payment_label,
                    COUNT(*)                                    AS trips,
                    ROUND(SUM(total_amount), 2)                 AS revenue,
                    ROUND(AVG(tip_amount), 2)                   AS avg_tip
                FROM trips
                GROUP BY payment_type
            """,
            "anomalies": """
                SELECT
                    t.id,
                    t.pickup_datetime,
                    t.pickup_location_id                        AS zone_id,
                    t.total_amount                              AS fare,
                    t.trip_distance,
                    t.payment_type,
                    ROUND(
                        ABS(t.total_amount - z.avg_fare)
                        / NULLIF(z.stddev_fare, 0)
                    , 2)                                        AS z_score
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
                LIMIT 1000
            """,
        }

        for name, query in views.items():
            cursor.execute(f"CREATE OR REPLACE VIEW {name} AS {query}")
            log.info(f"  View ready: {name}")

        conn.commit()
        cursor.close()
        log.info("All views created.")

    def run(self, mode: str, month: str) -> bool:
        log.info(f"Starting pipeline. mode={mode}, month={month}")
        start = datetime.now()
        try:
            df   = self.extract(month)
            df   = self.transform(df)
            conn = self.connect()
            self.create_schema(conn)
            self.load(df, conn, mode)
            self.create_views(conn)
            conn.close()
            elapsed = round((datetime.now() - start).total_seconds(), 1)
            log.info(f"Pipeline finished in {elapsed}s. MySQL is ready for Tableau.")
            return True
        except Exception as e:
            log.error(f"Pipeline failed: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="NYC Taxi Data Pipeline")
    parser.add_argument("--mode", choices=["full", "incremental"], default="full")
    parser.add_argument("--month", default="2024-01")
    args = parser.parse_args()
    pipeline = NYCTaxiPipeline()
    success = pipeline.run(args.mode, args.month)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
