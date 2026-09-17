import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import streamlit as st
import pandas as pd
import plotly.express as px

import analytics as db_analytics
from csv_analytics import (
    CsvAnalytics,
    sample_csv_bytes,
    auto_detect_mapping,
    REQUIRED_COLUMNS,
)

st.set_page_config(page_title="E-commerce Analytics", layout="wide")

# ============================================================
# SIDEBAR — DATA SOURCE
# ============================================================
st.sidebar.title("Data Source")

source = st.sidebar.radio(
    "Choose data source",
    ["Sample data (Olist)", "Upload my CSV"],
    index=0,
    label_visibility="collapsed",
)

analytics = None
is_csv = (source == "Upload my CSV")
mapping_ui_needed = False
df_raw = None

if not is_csv:
    analytics = db_analytics
    st.sidebar.success("Using 100K+ orders from Olist dataset.")
else:
    st.sidebar.markdown(
        "**Required columns:** `order_id`, `order_date`, `customer_id`, "
        "`category`, `state`, `revenue`  \n"
        "*Your CSV can use different names — you'll map them after upload.*"
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
        st.info("Use the sidebar to upload a CSV. Analytics will be computed on your data.")
        st.markdown("### Expected data")
        st.markdown("Your CSV needs columns for: **order, date, customer, category, region, amount**.")
        st.markdown("Column names can be anything — you'll map them in the next step.")
        st.markdown("### Sample format")
        st.code(
            "order_id,order_date,customer_id,category,state,revenue\n"
            "1001,2023-01-05,C001,Electronics,SP,150.00\n"
            "1002,2023-01-12,C002,Books,RJ,45.50",
            language="csv",
        )
        st.stop()

    # ---- Read CSV ----
    try:
        df_raw = pd.read_csv(uploaded)
        df_raw.columns = [str(c).strip().lower() for c in df_raw.columns]
    except Exception as e:
        st.error(f"Could not read CSV: {e}")
        st.stop()

    # ---- Check if mapping is needed ----
    missing = [c for c in REQUIRED_COLUMNS if c not in df_raw.columns]

    if missing:
        mapping_ui_needed = True

        st.sidebar.divider()
        st.sidebar.subheader("Map your columns")
        st.sidebar.caption(
            "Your CSV doesn't have all the columns we need with the exact names. "
            "Tell us which of your columns matches each requirement."
        )

        auto = auto_detect_mapping(df_raw.columns.tolist())
        user_cols = ["(skip)"] + df_raw.columns.tolist()
        mapping = {}

        for req in REQUIRED_COLUMNS:
            is_mapped = req not in missing
            default = auto.get(req, "(skip)")
            idx = user_cols.index(default) if default in user_cols else 0

            label = f"✓ {req}" if is_mapped else f"→ {req}"
            sel = st.sidebar.selectbox(
                label,
                user_cols,
                index=idx,
                key=f"map_{req}",
                disabled=is_mapped,
            )
            if is_mapped:
                mapping[req] = req
            elif sel != "(skip)":
                mapping[req] = sel
    else:
        mapping = {req: req for req in REQUIRED_COLUMNS}

# ============================================================
# MAIN AREA — mapping preview if needed
# ============================================================
if mapping_ui_needed:
    st.title("Map your CSV columns")

    st.info(
        "Your CSV column names don't match our expected schema. "
        "Use the sidebar on the left to map your columns, then the dashboard will load."
    )

    st.markdown("#### Your CSV preview")
    st.dataframe(df_raw.head(10), use_container_width=True)

    still_missing = [r for r in REQUIRED_COLUMNS if r not in mapping]
    if still_missing:
        st.warning(f"Still need to map: **{', '.join(still_missing)}**")
        st.stop()
    else:
        try:
            analytics = CsvAnalytics(df_raw, mapping=mapping)
            st.sidebar.success(f"Mapped and loaded {len(df_raw):,} rows.")
        except Exception as e:
            st.error(f"Could not apply mapping: {e}")
            st.stop()

if not is_csv:
    pass  # using db_analytics
elif not mapping_ui_needed:
    try:
        analytics = CsvAnalytics(df_raw)
        st.sidebar.success(f"Loaded {len(df_raw):,} rows.")
    except Exception as e:
        st.error(f"Could not load CSV: {e}")
        st.stop()

# ============================================================
# SIDEBAR — FILTERS
# ============================================================
st.sidebar.divider()

if st.sidebar.button("Reset filters", use_container_width=True):
    for key in ["quick_range", "date_range", "states_pick", "start_date", "end_date"]:
        st.session_state.pop(key, None)
    st.rerun()

st.sidebar.subheader("Filters")

try:
    min_date, max_date = analytics.get_date_range()
    min_date = pd.Timestamp(min_date).date()
    max_date = pd.Timestamp(max_date).date()
    all_states = analytics.get_states()

    st.sidebar.caption("Quick range")
    quick = st.sidebar.radio(
        "Quick range",
        ["All time", "Last 12 months", "Last 6 months", "Last 3 months", "Custom"],
        index=0,
        label_visibility="collapsed",
        key="quick_range",
    )

    if quick == "All time":
        start_date, end_date = min_date, max_date
    elif quick == "Last 12 months":
        end_date = max_date
        start_date = (pd.Timestamp(max_date) - pd.DateOffset(months=12)).date()
        start_date = max(start_date, min_date)
    elif quick == "Last 6 months":
        end_date = max_date
        start_date = (pd.Timestamp(max_date) - pd.DateOffset(months=6)).date()
        start_date = max(start_date, min_date)
    elif quick == "Last 3 months":
        end_date = max_date
        start_date = (pd.Timestamp(max_date) - pd.DateOffset(months=3)).date()
        start_date = max(start_date, min_date)
    else:  # Custom
        st.sidebar.caption("From")
        start_date = st.sidebar.date_input(
            "Start date", value=min_date, min_value=min_date, max_value=max_date,
            label_visibility="collapsed", key="start_date",
        )
        st.sidebar.caption("To")
        end_date = st.sidebar.date_input(
            "End date", value=max_date, min_value=min_date, max_value=max_date,
            label_visibility="collapsed", key="end_date",
        )
        if start_date > end_date:
            st.sidebar.warning("Start date is after end date — swapping.")
            start_date, end_date = end_date, start_date

    st.sidebar.divider()

    display_names = [name for name, code in all_states]
    code_lookup = {name: code for name, code in all_states}

    btn_col1, btn_col2 = st.sidebar.columns(2)
    if btn_col1.button("Select all", use_container_width=True):
        st.session_state["states_pick"] = display_names
    if btn_col2.button("Clear all", use_container_width=True):
        st.session_state["states_pick"] = []

    if "states_pick" not in st.session_state:
        st.session_state["states_pick"] = display_names

    selected_display = st.sidebar.multiselect(
        f"States ({len(st.session_state['states_pick'])} of {len(display_names)})",
        display_names,
        key="states_pick",
        placeholder="Choose one or more states",
    )

    selected_states = [code_lookup[name] for name in selected_display]
    if not selected_states:
        selected_states = [code for _, code in all_states]
        st.sidebar.caption("No states selected — showing all.")

except Exception as e:
    st.sidebar.error(f"Filter load failed: {e}")
    start_date, end_date, selected_states = None, None, None

filters = dict(start_date=start_date, end_date=end_date, states=selected_states)

# ============================================================
# HEADER
# ============================================================
st.title("E-commerce Sales Analytics")
if is_csv:
    st.caption("Uploaded CSV")
else:
    st.caption("Brazilian Olist dataset — 2017 to 2018")

is_filtered = (
    (start_date is not None and start_date != min_date) or
    (end_date is not None and end_date != max_date) or
    (selected_states is not None and len(selected_states) != len(all_states))
)

if is_filtered:
    parts = []
    if start_date and end_date:
        parts.append(f"**Date:** {start_date} → {end_date}")
    if selected_states and len(selected_states) != len(all_states):
        parts.append(f"**States:** {len(selected_states)} of {len(all_states)} selected")
    st.info(" · ".join(parts))
else:
    st.caption("Showing all data. Use the sidebar to filter.")

# ============================================================
# KPIs
# ============================================================
kpi = analytics.top_kpis(**filters).iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"R$ {kpi['total_revenue']:,.0f}")
col2.metric("Total Orders", f"{int(kpi['total_orders']):,}")
col3.metric("Total Customers", f"{int(kpi['total_customers']):,}")
col4.metric("Avg Order Value", f"R$ {kpi['aov']:,.2f}")

st.divider()

# ============================================================
# CHARTS
# ============================================================
st.subheader("Revenue Over Time")
rev = analytics.monthly_revenue(**filters)
if rev.empty:
    st.warning("No data in selected range.")
else:
    fig_rev = px.line(
        rev, x="month", y="revenue", markers=True,
        labels={"month": "Month", "revenue": "Revenue (R$)"},
    )
    st.plotly_chart(fig_rev, use_container_width=True)

st.subheader("Average Order Value Trend")
aov = analytics.aov_trend(**filters)
if aov.empty:
    st.warning("No data in selected range.")
else:
    fig_aov = px.line(
        aov, x="month", y="aov", markers=True,
        labels={"month": "Month", "aov": "AOV (R$)"},
    )
    st.plotly_chart(fig_aov, use_container_width=True)

st.divider()

colA, colB = st.columns(2)

with colA:
    st.subheader("Top Product Categories")
    top = analytics.top_products(15, **filters)
    if top.empty:
        st.warning("No data.")
    else:
        fig_top = px.bar(
            top.sort_values("revenue"),
            x="revenue", y="category", orientation="h",
            labels={"revenue": "Revenue (R$)", "category": ""},
        )
        st.plotly_chart(fig_top, use_container_width=True)

with colB:
    st.subheader("Revenue by State")
    states_df = analytics.revenue_by_state(**filters)
    if states_df.empty:
        st.warning("No data.")
    else:
        fig_state = px.bar(
            states_df.sort_values("revenue"),
            x="revenue", y="state", orientation="h",
            labels={"revenue": "Revenue (R$)", "state": ""},
        )
        st.plotly_chart(fig_state, use_container_width=True)

st.divider()

st.subheader("Cohort Retention (month 0–5)")
ret = analytics.retention(**filters)
if ret.empty:
    st.warning("No data.")
else:
    st.dataframe(ret, use_container_width=True)

st.divider()

st.subheader("Customer Segments (RFM)")
rfm = analytics.rfm_segments(**filters)

if rfm.empty:
    st.warning("No data.")
else:
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