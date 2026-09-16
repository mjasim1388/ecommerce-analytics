import sys
from pathlib import Path

# Allow imports from src/
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import streamlit as st
import plotly.express as px
import analytics as a

st.set_page_config(page_title="E-commerce Analytics", layout="wide")

st.title("E-commerce Sales Analytics")
st.caption("Brazilian Olist dataset — 2017 to 2018")

# ---------- KPI CARDS ----------
kpi = a.top_kpis().iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"R$ {kpi['total_revenue']:,.0f}")
col2.metric("Total Orders", f"{kpi['total_orders']:,}")
col3.metric("Total Customers", f"{kpi['total_customers']:,}")
col4.metric("Avg Order Value", f"R$ {kpi['aov']:,.2f}")

st.divider()

# ---------- REVENUE OVER TIME ----------
st.subheader("Revenue Over Time")

rev = a.monthly_revenue()
fig_rev = px.line(
    rev,
    x="month",
    y="revenue",
    markers=True,
    labels={"month": "Month", "revenue": "Revenue (R$)"},
)
st.plotly_chart(fig_rev, use_container_width=True)

# ---------- AOV TREND ----------
st.subheader("Average Order Value Trend")

aov = a.aov_trend()
fig_aov = px.line(
    aov,
    x="month",
    y="aov",
    markers=True,
    labels={"month": "Month", "aov": "AOV (R$)"},
)
st.plotly_chart(fig_aov, use_container_width=True)

st.divider()

# ---------- TOP PRODUCTS ----------
colA, colB = st.columns(2)

with colA:
    st.subheader("Top 15 Product Categories")
    top = a.top_products(15)
    fig_top = px.bar(
        top.sort_values("revenue"),
        x="revenue",
        y="category",
        orientation="h",
        labels={"revenue": "Revenue (R$)", "category": ""},
    )
    st.plotly_chart(fig_top, use_container_width=True)

with colB:
    st.subheader("Revenue by State")
    states = a.revenue_by_state()
    fig_state = px.bar(
        states.sort_values("revenue"),
        x="revenue",
        y="state",
        orientation="h",
        labels={"revenue": "Revenue (R$)", "state": ""},
    )
    st.plotly_chart(fig_state, use_container_width=True)

st.divider()

# ---------- RETENTION ----------
st.subheader("Cohort Retention (month 0–5)")
ret = a.retention()
st.dataframe(ret, use_container_width=True)

st.divider()

# ---------- RFM ----------
st.subheader("Customer Segments (RFM)")
rfm = a.rfm_segments()

colC, colD = st.columns(2)
with colC:
    fig_rfm = px.pie(
        rfm,
        names="segment",
        values="customers",
        title="Customers by Segment",
    )
    st.plotly_chart(fig_rfm, use_container_width=True)

with colD:
    fig_rfm_rev = px.bar(
        rfm,
        x="segment",
        y="total_revenue",
        title="Revenue by Segment",
        labels={"total_revenue": "Revenue (R$)", "segment": ""},
    )
    st.plotly_chart(fig_rfm_rev, use_container_width=True)

st.dataframe(rfm, use_container_width=True)