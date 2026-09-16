import pandas as pd
from db import engine

START = "2017-01-01"
END = "2019-01-01"


def _query(sql):
    return pd.read_sql(sql, engine)


def monthly_revenue():
    sql = f"""
    SELECT
        DATE_TRUNC('month', o.order_purchase_timestamp)::date AS month,
        ROUND(SUM(oi.price + oi.freight_value)::numeric, 2) AS revenue,
        COUNT(DISTINCT o.order_id) AS orders
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
      AND o.order_purchase_timestamp >= '{START}'
      AND o.order_purchase_timestamp < '{END}'
    GROUP BY month
    ORDER BY month;
    """
    return _query(sql)


def aov_trend():
    sql = f"""
    SELECT
        DATE_TRUNC('month', o.order_purchase_timestamp)::date AS month,
        ROUND(
            (SUM(oi.price + oi.freight_value) / COUNT(DISTINCT o.order_id))::numeric,
            2
        ) AS aov
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
      AND o.order_purchase_timestamp >= '{START}'
      AND o.order_purchase_timestamp < '{END}'
    GROUP BY month
    ORDER BY month;
    """
    return _query(sql)


def top_products(limit=20):
    sql = f"""
    SELECT
        p.product_category_name AS category,
        COUNT(DISTINCT oi.order_id) AS orders,
        ROUND(SUM(oi.price)::numeric, 2) AS revenue,
        ROUND(AVG(oi.price)::numeric, 2) AS avg_price
    FROM order_items oi
    JOIN products p ON p.product_id = oi.product_id
    JOIN orders o ON o.order_id = oi.order_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
      AND p.product_category_name IS NOT NULL
    GROUP BY category
    ORDER BY revenue DESC
    LIMIT {limit};
    """
    return _query(sql)


def revenue_by_state():
    sql = """
    SELECT
        c.customer_state AS state,
        COUNT(DISTINCT o.order_id) AS orders,
        ROUND(SUM(oi.price + oi.freight_value)::numeric, 2) AS revenue
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY state
    ORDER BY revenue DESC;
    """
    return _query(sql)


def retention():
    sql = """
    WITH customer_first_order AS (
        SELECT
            c.customer_unique_id,
            MIN(DATE_TRUNC('month', o.order_purchase_timestamp)) AS cohort_month
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        WHERE o.order_status NOT IN ('canceled', 'unavailable')
        GROUP BY c.customer_unique_id
    ),
    customer_orders AS (
        SELECT DISTINCT
            c.customer_unique_id,
            DATE_TRUNC('month', o.order_purchase_timestamp) AS order_month
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        WHERE o.order_status NOT IN ('canceled', 'unavailable')
    ),
    cohort_data AS (
        SELECT
            f.cohort_month,
            o.order_month,
            EXTRACT(MONTH FROM AGE(o.order_month, f.cohort_month))::int AS month_number,
            f.customer_unique_id
        FROM customer_first_order f
        JOIN customer_orders o ON o.customer_unique_id = f.customer_unique_id
    )
    SELECT
        TO_CHAR(cohort_month, 'YYYY-MM') AS cohort,
        COUNT(DISTINCT CASE WHEN month_number = 0 THEN customer_unique_id END) AS month_0,
        COUNT(DISTINCT CASE WHEN month_number = 1 THEN customer_unique_id END) AS month_1,
        COUNT(DISTINCT CASE WHEN month_number = 2 THEN customer_unique_id END) AS month_2,
        COUNT(DISTINCT CASE WHEN month_number = 3 THEN customer_unique_id END) AS month_3,
        COUNT(DISTINCT CASE WHEN month_number = 4 THEN customer_unique_id END) AS month_4,
        COUNT(DISTINCT CASE WHEN month_number = 5 THEN customer_unique_id END) AS month_5
    FROM cohort_data
    GROUP BY cohort_month
    ORDER BY cohort_month;
    """
    return _query(sql)


def rfm_segments():
    sql = """
    WITH customer_metrics AS (
        SELECT
            c.customer_unique_id,
            MAX(o.order_purchase_timestamp)::date AS last_order_date,
            COUNT(DISTINCT o.order_id) AS frequency,
            SUM(oi.price + oi.freight_value)::numeric AS monetary
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.order_status NOT IN ('canceled', 'unavailable')
        GROUP BY c.customer_unique_id
    ),
    scored AS (
        SELECT
            customer_unique_id,
            (CURRENT_DATE - last_order_date) AS recency_days,
            frequency,
            monetary,
            NTILE(5) OVER (ORDER BY (CURRENT_DATE - last_order_date) DESC) AS r_score,
            NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
            NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
        FROM customer_metrics
    )
    SELECT
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
            WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Loyal'
            WHEN r_score >= 4 AND f_score <= 2 THEN 'New Customers'
            WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
            WHEN r_score <= 2 AND f_score <= 2 THEN 'Lost'
            ELSE 'Others'
        END AS segment,
        COUNT(*) AS customers,
        ROUND(AVG(recency_days)::numeric, 0) AS avg_recency_days,
        ROUND(AVG(frequency)::numeric, 2) AS avg_frequency,
        ROUND(AVG(monetary)::numeric, 2) AS avg_monetary,
        ROUND(SUM(monetary)::numeric, 2) AS total_revenue
    FROM scored
    GROUP BY segment
    ORDER BY total_revenue DESC;
    """
    return _query(sql)


def top_kpis():
    sql = f"""
    SELECT
        COUNT(DISTINCT o.order_id) AS total_orders,
        COUNT(DISTINCT c.customer_unique_id) AS total_customers,
        ROUND(SUM(oi.price + oi.freight_value)::numeric, 2) AS total_revenue,
        ROUND(
            (SUM(oi.price + oi.freight_value) / COUNT(DISTINCT o.order_id))::numeric,
            2
        ) AS aov
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
      AND o.order_purchase_timestamp >= '{START}'
      AND o.order_purchase_timestamp < '{END}';
    """
    return _query(sql)