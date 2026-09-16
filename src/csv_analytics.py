import pandas as pd
import numpy as np


REQUIRED_COLUMNS = ["order_id", "order_date", "customer_id", "category", "state", "revenue"]


class CsvAnalytics:
    """
    Same interface as the analytics module (top_kpis, monthly_revenue, ...)
    but works on an uploaded pandas DataFrame instead of PostgreSQL.
    """

    def __init__(self, df: pd.DataFrame):
        df = df.copy()
        df.columns = [str(c).strip().lower() for c in df.columns]

        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(
                f"CSV is missing required columns: {missing}. "
                f"Required: {REQUIRED_COLUMNS}"
            )

        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
        df = df.dropna(subset=["order_date"])
        df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce").fillna(0.0)
        df["month"] = df["order_date"].dt.to_period("M").dt.to_timestamp()

        self.df = df

    # ---------- KPIs ----------
    def top_kpis(self):
        df = self.df
        total_orders = int(df["order_id"].nunique())
        total_customers = int(df["customer_id"].nunique())
        total_revenue = float(df["revenue"].sum())
        aov = total_revenue / total_orders if total_orders else 0.0
        return pd.DataFrame([{
            "total_orders": total_orders,
            "total_customers": total_customers,
            "total_revenue": round(total_revenue, 2),
            "aov": round(aov, 2),
        }])

    # ---------- Revenue over time ----------
    def monthly_revenue(self):
        df = self.df
        out = df.groupby("month").agg(
            revenue=("revenue", "sum"),
            orders=("order_id", "nunique"),
        ).reset_index()
        out["revenue"] = out["revenue"].round(2)
        return out.sort_values("month")

    def aov_trend(self):
        m = self.monthly_revenue()
        m["aov"] = (m["revenue"] / m["orders"]).round(2)
        return m[["month", "aov"]]

    # ---------- Top products ----------
    def top_products(self, limit=20):
        df = self.df
        out = df.groupby("category").agg(
            orders=("order_id", "nunique"),
            revenue=("revenue", "sum"),
            avg_price=("revenue", "mean"),
        ).reset_index()
        out["revenue"] = out["revenue"].round(2)
        out["avg_price"] = out["avg_price"].round(2)
        return out.sort_values("revenue", ascending=False).head(limit)

    # ---------- Revenue by state ----------
    def revenue_by_state(self):
        df = self.df
        out = df.groupby("state").agg(
            orders=("order_id", "nunique"),
            revenue=("revenue", "sum"),
        ).reset_index()
        out["revenue"] = out["revenue"].round(2)
        return out.sort_values("revenue", ascending=False)

    # ---------- Cohort retention ----------
    def retention(self):
        df = self.df

        first = df.groupby("customer_id")["order_date"].min().reset_index()
        first.columns = ["customer_id", "first_order"]
        first["cohort"] = first["first_order"].dt.to_period("M").dt.to_timestamp()

        merged = df.merge(first, on="customer_id", how="left")
        merged["order_month"] = merged["order_date"].dt.to_period("M").dt.to_timestamp()

        merged["month_number"] = (
            (merged["order_month"].dt.year - merged["cohort"].dt.year) * 12
            + (merged["order_month"].dt.month - merged["cohort"].dt.month)
        )

        rows = []
        for cohort, group in merged.groupby("cohort"):
            row = {"cohort": cohort.strftime("%Y-%m")}
            for i in range(6):
                row[f"month_{i}"] = int(
                    group.loc[group["month_number"] == i, "customer_id"].nunique()
                )
            rows.append(row)

        return pd.DataFrame(rows).sort_values("cohort").reset_index(drop=True)

    # ---------- RFM segments ----------
    def rfm_segments(self):
        df = self.df
        snapshot = df["order_date"].max() + pd.Timedelta(days=1)

        rfm = df.groupby("customer_id").agg(
            last_order=("order_date", "max"),
            frequency=("order_id", "nunique"),
            monetary=("revenue", "sum"),
        ).reset_index()

        rfm["recency_days"] = (snapshot - rfm["last_order"]).dt.days

        rfm["r_score"] = pd.qcut(
            rfm["recency_days"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]
        ).astype(int)
        rfm["f_score"] = pd.qcut(
            rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
        ).astype(int)
        rfm["m_score"] = pd.qcut(
            rfm["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
        ).astype(int)

        def seg(row):
            r, f, m = row["r_score"], row["f_score"], row["m_score"]
            if r >= 4 and f >= 4 and m >= 4:
                return "Champions"
            if r >= 3 and f >= 3 and m >= 3:
                return "Loyal"
            if r >= 4 and f <= 2:
                return "New Customers"
            if r <= 2 and f >= 3:
                return "At Risk"
            if r <= 2 and f <= 2:
                return "Lost"
            return "Others"

        rfm["segment"] = rfm.apply(seg, axis=1)

        out = rfm.groupby("segment").agg(
            customers=("customer_id", "count"),
            avg_recency_days=("recency_days", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
            total_revenue=("monetary", "sum"),
        ).reset_index()

        for c in ["avg_recency_days", "avg_frequency", "avg_monetary", "total_revenue"]:
            out[c] = out[c].round(2)

        return out.sort_values("total_revenue", ascending=False)


# ---------- Sample CSV for users to download ----------
def sample_csv_bytes() -> bytes:
    sample = pd.DataFrame([
        {"order_id": "1001", "order_date": "2023-01-05", "customer_id": "C001", "category": "Electronics", "state": "SP", "revenue": 150.00},
        {"order_id": "1002", "order_date": "2023-01-12", "customer_id": "C002", "category": "Books",       "state": "RJ", "revenue": 45.50},
        {"order_id": "1003", "order_date": "2023-01-20", "customer_id": "C003", "category": "Electronics", "state": "MG", "revenue": 220.00},
        {"order_id": "1004", "order_date": "2023-02-02", "customer_id": "C001", "category": "Home",        "state": "SP", "revenue": 89.90},
        {"order_id": "1005", "order_date": "2023-02-11", "customer_id": "C004", "category": "Books",       "state": "SP", "revenue": 32.00},
        {"order_id": "1006", "order_date": "2023-02-25", "customer_id": "C002", "category": "Electronics", "state": "RJ", "revenue": 410.00},
        {"order_id": "1007", "order_date": "2023-03-04", "customer_id": "C005", "category": "Home",        "state": "RS", "revenue": 120.75},
        {"order_id": "1008", "order_date": "2023-03-15", "customer_id": "C001", "category": "Books",       "state": "SP", "revenue": 27.50},
        {"order_id": "1009", "order_date": "2023-03-22", "customer_id": "C003", "category": "Electronics", "state": "MG", "revenue": 199.99},
        {"order_id": "1010", "order_date": "2023-04-01", "customer_id": "C004", "category": "Home",        "state": "SP", "revenue": 75.00},
    ])
    return sample.to_csv(index=False).encode("utf-8")