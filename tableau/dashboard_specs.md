# NYC Taxi Analytics - Dashboard Specifications

## Dashboard Overview

This document outlines the Tableau dashboards for the NYC Taxi Analytics system. Each dashboard targets specific operational insights.

---

## Dashboard 1: Daily Operations Center

**Purpose**: Executive overview of daily taxi operations

**KPI Cards**:
- Total Trips (last 24 hours)
- Total Revenue (last 24 hours)
- Average Fare
- Average Tip %
- Active Zones
- Average Trip Duration

**Visualizations**:
1. **Line Chart**: Daily trip volume (last 30 days)
   - X-axis: Date
   - Y-axis: Number of trips
   - Breakdown: By payment type

2. **Bar Chart**: Revenue by zone (today)
   - Top 10 zones
   - Color: Revenue amount
   - Sort: Descending

3. **Scatter Plot**: Fare vs. Trip Distance
   - X-axis: Trip distance
   - Y-axis: Fare amount
   - Color: Payment type

4. **Gauge Charts**: (3 tiles)
   - Average tip percentage (target: 15%)
   - On-time completion rate
   - Revenue per trip vs. target

**Filters**:
- Date range picker
- Payment type
- Borough
