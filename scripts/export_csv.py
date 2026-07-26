# scripts/export_csv.py
import mysql.connector
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

conn = mysql.connector.connect(
    host="127.0.0.1",
    port=3306,
    user="root",
    password="root_password",
    database="nyc_taxi"
)

os.makedirs("../data/exports", exist_ok=True)

views = ["daily_revenue", "hourly_patterns", "zone_summary", "payment_split", "anomalies"]

for view in views:
    df = pd.read_sql(f"SELECT * FROM {view}", conn)
    path = f"../data/exports/{view}.csv"
    df.to_csv(path, index=False)
    print(f"{view}: {len(df)} rows -> {path}")

conn.close()