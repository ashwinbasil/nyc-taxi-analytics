# NYC Taxi Analytics - Deployment Guide

## Production Deployment

### Prerequisites

- Docker & Docker Compose (latest)
- Python 3.9+
- MySQL 8.0+
- 50GB+ disk space (for data)
- 4GB+ RAM
- Outbound network access to BigQuery (for data sync)

---

## 1. Database Setup

### Option A: Local Development (Docker)

```bash
# Start MySQL + phpMyAdmin
docker-compose up -d

# Verify health
docker-compose ps
docker-compose logs mysql

# Access phpMyAdmin
# http://localhost:8080
# User: root, Password: root_password
```

### Option B: Cloud Database (AWS RDS, Google Cloud SQL)

```bash
# Update .env with your cloud database credentials
MYSQL_HOST=your-rds-endpoint.amazonaws.com
MYSQL_PORT=3306
MYSQL_USER=admin
MYSQL_PASSWORD=your_secure_password
MYSQL_DATABASE=nyc_taxi
```

---

## 2. Initialize Database Schema

```bash
# Run schema setup
mysql -h localhost -u root -proot_password < sql/schema.sql
mysql -h localhost -u root -proot_password < sql/materialized_views.sql

# Verify tables created
mysql -h localhost -u root -proot_password -e "USE nyc_taxi; SHOW TABLES;"
```

---

## 3. Data Pipeline Setup

### Install Python dependencies

```bash
pip install -r requirements.txt
```

### Copy environment template

```bash
cp .env.example .env
# Edit .env with your settings
```

### Initial full data load

```bash
# First time: full load
python scripts/data_pipeline.py --mode full
```

---

## 4. Automated Daily Runs

### Option A: Cron Job (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add daily incremental run at 2 AM
0 2 * * * cd /path/to/nyc-taxi-analytics && python scripts/data_pipeline.py --mode incremental >> logs/pipeline.log 2>&1
```

### Option B: Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: nyc-taxi-pipeline
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: pipeline
            image: nyc-taxi-pipeline:latest
            command: ["python", "scripts/data_pipeline.py", "--mode", "incremental"]
          restartPolicy: OnFailure
```

---

## Monitoring & Logging

### Query Pipeline History

```sql
-- Last 10 pipeline runs
SELECT * FROM pipeline_logs 
ORDER BY execution_date DESC 
LIMIT 10;

-- Failed runs
SELECT * FROM pipeline_logs 
WHERE status = 'FAILED' 
ORDER BY execution_date DESC;
```

---

## Backup & Recovery

### Daily MySQL Backup

```bash
mysqldump -h localhost -u root -proot_password nyc_taxi | \
  gzip > /backups/nyc_taxi_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Restore from Backup

```bash
gunzip < /backups/nyc_taxi_backup.sql.gz | \
  mysql -h localhost -u root -proot_password nyc_taxi
```
