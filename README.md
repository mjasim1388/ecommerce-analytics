# E-commerce Sales Analytics Dashboard

An end-to-end data analytics project analyzing 100K+ orders from the Brazilian Olist e-commerce dataset.

## Overview

This project builds a complete analytics pipeline — from raw CSV data to an interactive dashboard — using PostgreSQL, Python, and Streamlit.

## Features

- **Data pipeline**: Loads ~450,000 rows from 5 CSV files into PostgreSQL
- **SQL analytics**: 6 production-style queries including cohort retention and RFM segmentation
- **Python layer**: Reusable analytics module returning pandas DataFrames
- **Interactive dashboard**: Streamlit + Plotly with KPI cards, charts, and drill-downs

## Key Metrics

- Total revenue, total orders, total customers
- Average Order Value (AOV) trend over time
- Top 20 product categories by revenue
- Revenue by Brazilian state
- Cohort retention (month 0 to month 5)
- RFM customer segmentation (Champions, Loyal, At Risk, Lost, etc.)

## Tech Stack

| Layer | Tool |
|---|---|
| Database | PostgreSQL (Supabase) |
| Data processing | pandas, SQLAlchemy |
| Analytics | SQL (CTEs, window functions, joins) |
| Visualization | Plotly |
| Dashboard | Streamlit |
| Deployment | Streamlit Community Cloud |

## Project Structure



## Setup

1. Clone the repo
2. Create a virtual environment: `python -m venv venv`
3. Activate: `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Create `.env` with `DATABASE_URL=your_postgres_connection_string`
6. Load data: `python src/load_data.py`
7. Run dashboard: `streamlit run app/streamlit_app.py`

## Live Demo

🔗 [View the live dashboard](https://ecommerce-analytics-mjasim.streamlit.app/)

## Dataset

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) — 100K orders from 2016–2018.