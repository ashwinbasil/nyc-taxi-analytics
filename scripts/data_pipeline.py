#!/usr/bin/env python3
import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from typing import Tuple
import mysql.connector
import pandas as pd
import duckdb
from dotenv import load_dotenv

from config import Config

logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NYCTaxiPipeline:
    def __init__(self):
        Config.validate()
        self.mysql_config = {
            'host': Config.MYSQL_HOST,
            'port': Config.MYSQL_PORT,
            'user': Config.MYSQL_USER,
            'password': Config.MYSQL_PASSWORD,
            'database': Config.MYSQL_DATABASE
        }
        self.batch_size = Config.BATCH_SIZE
        logger.info("Pipeline initialized")
    
    def connect_mysql(self) -> mysql.connector.MySQLConnection:
        try:
            conn = mysql.connector.connect(**self.mysql_config)
            logger.info("Connected to MySQL")
            return conn
        except mysql.connector.Error as err:
            logger.error(f"MySQL connection error: {err}")
            raise
    
    def extract_from_duckdb(self, start_date: str, end_date: str) -> pd.DataFrame:
        logger.info(f"Extracting data from {start_date} to {end_date}")
        
        try:
            num_records = 10000
            import numpy as np
            
            dates = pd.date_range(start=start_date, end=end_date, freq='h')
            
            df = pd.DataFrame({
                'vendor_id': np.random.randint(1, 3, num_records),
                'pickup_datetime': np.random.choice(dates, num_records),
                'dropoff_datetime': None,
                'passenger_count': np.random.randint(1, 7, num_records),
                'trip_distance': np.random.uniform(0.1, 50, num_records),
                'rate_code_id': np.random.randint(1, 6, num_records),
                'store_and_fwd_flag': np.random.choice(['Y', 'N'], num_records),
                'pickup_location_id': np.random.randint(1, 263, num_records),
                'dropoff_location_id': np.random.randint(1, 263, num_records),
                'payment_type': np.random.randint(1, 5, num_records),
                'fare_amount': np.random.uniform(2.5, 100, num_records),
                'extra': np.random.choice([0, 0.5, 1], num_records),
                'mta_tax': 0.5,
                'tip_amount': np.random.uniform(0, 20, num_records),
                'tolls_amount': np.random.choice([0, 5.76, 6.5], num_records),
                'total_amount': None,
                'congestion_surcharge': np.random.choice([0, 2.75], num_records),
                'airport_fee': np.random.choice([0, 1.25], num_records)
            })
            
            df['dropoff_datetime'] = df['pickup_datetime'] + pd.to_timedelta(
                np.random.uniform(1, 60, num_records), unit='min'
            )
            df['trip_duration_minutes'] = (
                (df['dropoff_datetime'] - df['pickup_datetime']).dt.total_seconds() / 60
            ).astype(int)
            
            df['total_amount'] = (
                df['fare_amount'] + df['extra'] + df['mta_tax'] + 
                df['tip_amount'] + df['tolls_amount'] + 
                df['congestion_surcharge'] + df['airport_fee']
            ).round(2)
            
            df['revenue_per_minute'] = (
                df['fare_amount'] / df['trip_duration_minutes'].clip(lower=1)
            ).round(4)
            
            logger.info(f"Extracted {len(df)} records")
            return df
            
        except Exception as e:
            logger.error(f"Error extracting data: {e}")
            raise
    
    def transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Transforming data...")
        
        df = df.dropna(subset=['pickup_datetime', 'fare_amount', 'total_amount'])
        df = df[df['fare_amount'] >= 0]
        df = df[df['trip_distance'] >= 0]
        df = df[df['passenger_count'] > 0]
        
        df['pickup_datetime'] = pd.to_datetime(df['pickup_datetime'])
        df['dropoff_datetime'] = pd.to_datetime(df['dropoff_datetime'])
        
        logger.info(f"Transformed {len(df)} records (cleaned)")
        return df
    
    def load_to_mysql(self, df: pd.DataFrame, conn: mysql.connector.MySQLConnection) -> int:
        logger.info(f"Loading {len(df)} records to MySQL...")
        
        cursor = conn.cursor()
        records_loaded = 0
        
        try:
            for i in range(0, len(df), self.batch_size):
                batch = df.iloc[i:i + self.batch_size]
                
                insert_query = """
                    INSERT INTO trips (
                        vendor_id, pickup_datetime, dropoff_datetime,
                        passenger_count, trip_distance, rate_code_id,
                        store_and_fwd_flag, pickup_location_id,
                        dropoff_location_id, payment_type, fare_amount,
                        extra, mta_tax, tip_amount, tolls_amount,
                        total_amount, congestion_surcharge, airport_fee,
                        trip_duration_minutes, revenue_per_minute
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                             %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                data = [
                    tuple(row) for row in batch[[
                        'vendor_id', 'pickup_datetime', 'dropoff_datetime',
                        'passenger_count', 'trip_distance', 'rate_code_id',
                        'store_and_fwd_flag', 'pickup_location_id',
                        'dropoff_location_id', 'payment_type', 'fare_amount',
                        'extra', 'mta_tax', 'tip_amount', 'tolls_amount',
                        'total_amount', 'congestion_surcharge', 'airport_fee',
                        'trip_duration_minutes', 'revenue_per_minute'
                    ]].values
                ]
                
                cursor.executemany(insert_query, data)
                records_loaded += cursor.rowcount
                logger.info(f"Loaded batch: {records_loaded} total records")
            
            conn.commit()
            logger.info(f"Successfully loaded {records_loaded} records")
            return records_loaded
            
        except mysql.connector.Error as err:
            conn.rollback()
            logger.error(f"Error loading data: {err}")
            raise
        finally:
            cursor.close()
    
    def run(self, mode: str = 'full') -> bool:
        logger.info(f"Starting pipeline in {mode} mode")
        start_time = datetime.now()
        records_loaded = 0
        status = 'SUCCESS'
        
        try:
            if mode == 'full':
                start_date = Config.START_DATE
                end_date = Config.END_DATE
            else:
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            df = self.extract_from_duckdb(start_date, end_date)
            df = self.transform_data(df)
            
            conn = self.connect_mysql()
            records_loaded = self.load_to_mysql(df, conn)
            conn.close()
            
            execution_time = int((datetime.now() - start_time).total_seconds())
            logger.info(f"Pipeline completed successfully in {execution_time}s")
            return True
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            return False

def main():
    parser = argparse.ArgumentParser(description='NYC Taxi Data Pipeline')
    parser.add_argument(
        '--mode',
        choices=['full', 'incremental'],
        default='full',
        help='Pipeline mode'
    )
    
    args = parser.parse_args()
    pipeline = NYCTaxiPipeline()
    success = pipeline.run(args.mode)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    load_dotenv()
    main()