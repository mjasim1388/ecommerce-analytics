import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import streamlit as st
import pandas as pd
import plotly.express as px

import analytics as db_analytics
from csv_analytics import CsvAnalytics, sample_csv_bytes

st.set_page_config(page_title="E-commerce Analytics", layout="wide")

# ---------------- SIDEBAR ----------------
st.sidebar.title("Data Source")

source = st.sidebar.radio(
    "Choose data source",
    ["Sample data (Olist)", "Upload my CSV"],
    index=0,
)

analytics = None  # this will be either db_analytics module or CsvAnalytics instance

if source == "Sample data (Olist)":
    analytics = db_analytics
    st.sidebar.success("Using 100K+ orders from the Olist dataset.")
else:
    st.sidebar.markdown(
        "**Required CSV columns:**\n"
        "- `order_id`\n"
        "- `order_date` (YYYY-MM-DD)\n"
        "- `customer_id`\n"
        "- `category`\n"
        "- `state`\n"
        "- `revenue`\n"
    )
    st.sidebar.download_button(
        label="Download sample CSV",
        data=sample_csv_bytes(),
        file_name="sample_sales.csv",
        mime="text/csv",
    )

    uploaded = st.sidebar.file_uploader("Upload your CSV", type=["csv"])

    if uploaded is None:
        st.title("Upload your CSV to get started")
        st.info(
            "Use the sidebar to upload a CSV. "
            "The app will compute the same KPIs, charts, retention, and RFM analysis on your data."
        )
        st.markdown("### Expected CSV format")
        st.code(
            "order_id,order_date,customer_id,category,state,revenue\n"
            "1001,2023-01-05,C001,Electronics,SP,150.00\n"
            "1002,2023-01-12,C002,Books,RJ,45.50",
            language="csv",
        )
        st.stop()

    try:
        df = pd.read_csv(uploaded)
        analytics = CsvAnalytics(df)
        st.sidebar.success(f"Loaded {len(df):,} rows from your CSV.")
    except Exception as e:
        st.error(f"Could not read CSV: {e}")
        st.stop()

# ---------------- HEADER ----------------
st.title("E-commerce Sales Analytics")
if source == "Sample data (Olist)":
    st.caption("Brazilian Olist dataset — 2017 to 2018")
else:
    st.caption("Uploaded CSV — custom dataset")

# ---------------- KPIs ----------------
kpi = analytics.top_kpis().iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"R$ {kpi['total_revenue']:,.0f}")
col2.metric("Total Orders", f"{int(kpi['total_orders']):,}")
col3.metric("Total Customers", f"{int(kpi['total_customers']):,}")
col4.metric("Avg Order Value", f"R$ {kpi['aov']:,.2f}")

st.divider()

# ---------------- REVENUE ----------------
st.subheader("Revenue Over Time")
rev = analytics.monthly_revenue()
fig_rev = px.line(
    rev, x="month", y="revenue", markers=True,
    labels={"month": "Month", "revenue": "Revenue (R$)"},
)
st.plotly_chart(fig_rev, use_container_width=True)

# ---------------- AOV ----------------
st.subheader("Average Order Value Trend")
aov = analytics.aov_trend()
fig_aov = px.line(
    aov, x="month", y="aov", markers=True,
    labels={"month": "Month", "aov": "AOV (R$)"},
)
st.plotly_chart(fig_aov, use_container_width=True)

st.divider()

# ---------------- TOP PRODUCTS & STATES ----------------
colA, colB = st.columns(2)

with colA:
    st.subheader("Top Product Categories")
    top = analytics.top_products(15)
    fig_top = px.bar(
        top.sort_values("revenue"),
        x="revenue", y="category", orientation="h",
        labels={"revenue": "Revenue (R$)", "category": ""},
    )
    st.plotly_chart(fig_top, use_container_width=True)

with colB:
    st.subheader("Revenue by State")
    states = analytics.revenue_by_state()
    fig_state = px.bar(
        states.sort_values("revenue"),
        x="revenue", y="state", orientation="h",
        labels={"revenue": "Revenue (R$)", "state": ""},
    )
    st.plotly_chart(fig_state, use_container_width=True)

st.divider()

# ---------------- RETENTION ----------------
st.subheader("Cohort Retention (month 0–5)")
ret = analytics.retention()
st.dataframe(ret, use_container_width=True)

st.divider()

# ---------------- RFM ----------------
st.subheader("Customer Segments (RFM)")
rfm = analytics.rfm_segments()

colC, colD = st.columns(2)
with colC:
    fig_rfm = px.pie(rfm, names="segment", values="customers", title="Customers by Segment")
    st.plotly_chart(fig_rfm, use_container_width=True)

with colD:
    fig_rfm_rev = px.bar(
        rfm, x="segment", y="total_revenue",
        title="Revenue by Segment",
        labels={"total_revenue": "Revenue (R$)", "segment": ""},
    )
    st.plotly_chart(fig_rfm_rev, use_container_width=True)

st.dataframe(rfm, use_container_width=True)