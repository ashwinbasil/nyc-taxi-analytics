import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # MySQL Configuration
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'root_password')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'nyc_taxi')
    
    # Connection String
    MYSQL_CONNECTION_STRING = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    
    # Data Pipeline Settings
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', 10000))
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 4))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    DATA_PATH = os.getenv('DATA_PATH', './data')
    
    # BigQuery Settings
    BIGQUERY_PROJECT = os.getenv('BIGQUERY_PROJECT', 'bigquery-public-data')
    BIGQUERY_DATASET = os.getenv('BIGQUERY_DATASET', 'new_york_taxi')
    BIGQUERY_TABLE = os.getenv('BIGQUERY_TABLE', 'tlc_yellow_trips_2019')
    
    # Date Range
    START_DATE = os.getenv('START_DATE', '2019-01-01')
    END_DATE = os.getenv('END_DATE', '2019-12-31')
    
    # Scheduler
    ENABLE_SCHEDULER = os.getenv('ENABLE_SCHEDULER', 'false').lower() == 'true'
    SCHEDULE_HOUR = int(os.getenv('SCHEDULE_HOUR', 2))
    SCHEDULE_MINUTE = int(os.getenv('SCHEDULE_MINUTE', 0))
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        required_fields = ['MYSQL_HOST', 'MYSQL_DATABASE']
        for field in required_fields:
            if not getattr(cls, field, None):
                raise ValueError(f"Missing required config: {field}")
        return True

if __name__ == '__main__':
    Config.validate()
    print("Configuration validated successfully")