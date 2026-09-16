import pandas as pd
from db import engine


def _query(sql):
    return pd.read_sql(sql, engine)


def get_date_range():
    sql = """
    SELECT
        MIN(order_purchase_timestamp)::date AS min_date,
        MAX(order_purchase_timestamp)::date AS max_date
    FROM orders
    WHERE order_status NOT IN ('canceled', 'unavailable');
    """
    row = _query(sql).iloc[0]
    return row["min_date"], row["max_date"]


BRAZIL_STATES = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AP": "Amapá",
    "AM": "Amazonas",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",
    "PA": "Pará",
    "PB": "Paraíba",
    "PR": "Paraná",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul",
    "RO": "Rondônia",
    "RR": "Roraima",
    "SC": "Santa Catarina",
    "SP": "São Paulo",
    "SE": "Sergipe",
    "TO": "Tocantins",
}


def get_states():
    """
    Returns list of (display_name, code) tuples, sorted by display name.
    Example: ("São Paulo", "SP")
    """
    sql = """
    SELECT DISTINCT customer_state AS state
    FROM customers
    WHERE customer_state IS NOT NULL
    ORDER BY customer_state;
    """
    codes = _query(sql)["state"].tolist()
    return [(f"{BRAZIL_STATES.get(code, code)} ({code})", code) for code in codes]

def _filters(start_date=None, end_date=None, states=None):
    clauses = ["o.order_status NOT IN ('canceled', 'unavailable')"]

    if start_date is not None:
        clauses.append(f"o.order_purchase_timestamp >= '{start_date.isoformat()}'")

    if end_date is not None:
        clauses.append(
            f"o.order_purchase_timestamp < '{end_date.isoformat()}'::date + INTERVAL '1 day'"
        )

    if states:
        quoted = ", ".join(f"'{s}'" for s in states)
        clauses.append(f"c.customer_state IN ({quoted})")

    return " AND ".join(clauses)


def top_kpis(start_date=None, end_date=None, states=None):
    where = _filters(start_date, end_date, states)
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
    WHERE {where};
    """
    return _query(sql)


def monthly_revenue(start_date=None, end_date=None, states=None):
    where = _filters(start_date, end_date, states)
    sql = f"""
    SELECT
        DATE_TRUNC('month', o.order_purchase_timestamp)::date AS month,
        ROUND(SUM(oi.price + oi.freight_value)::numeric, 2) AS revenue,
        COUNT(DISTINCT o.order_id) AS orders
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE {where}
    GROUP BY month
    ORDER BY month;
    """
    return _query(sql)


def aov_trend(start_date=None, end_date=None, states=None):
    where = _filters(start_date, end_date, states)
    sql = f"""
    SELECT
        DATE_TRUNC('month', o.order_purchase_timestamp)::date AS month,
        ROUND(
            (SUM(oi.price + oi.freight_value) / COUNT(DISTINCT o.order_id))::numeric,
            2
        ) AS aov
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE {where}
    GROUP BY month
    ORDER BY month;
    """
    return _query(sql)


def top_products(limit=20, start_date=None, end_date=None, states=None):
    where = _filters(start_date, end_date, states)
    sql = f"""
    SELECT
        p.product_category_name AS category,
        COUNT(DISTINCT oi.order_id) AS orders,
        ROUND(SUM(oi.price)::numeric, 2) AS revenue,
        ROUND(AVG(oi.price)::numeric, 2) AS avg_price
    FROM order_items oi
    JOIN products p ON p.product_id = oi.product_id
    JOIN orders o ON o.order_id = oi.order_id
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE {where}
      AND p.product_category_name IS NOT NULL
    GROUP BY category
    ORDER BY revenue DESC
    LIMIT {limit};
    """
    return _query(sql)


def revenue_by_state(start_date=None, end_date=None, states=None):
    where = _filters(start_date, end_date, states)
    sql = f"""
    SELECT
        c.customer_state AS state,
        COUNT(DISTINCT o.order_id) AS orders,
        ROUND(SUM(oi.price + oi.freight_value)::numeric, 2) AS revenue
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE {where}
    GROUP BY state
    ORDER BY revenue DESC;
    """
    return _query(sql)


def _date_only_filter(start_date=None, end_date=None):
    clauses = ["o.order_status NOT IN ('canceled', 'unavailable')"]
    if start_date is not None:
        clauses.append(f"o.order_purchase_timestamp >= '{start_date.isoformat()}'")
    if end_date is not None:
        clauses.append(
            f"o.order_purchase_timestamp < '{end_date.isoformat()}'::date + INTERVAL '1 day'"
        )
    return " AND ".join(clauses)


def retention(start_date=None, end_date=None, states=None):
    where = _date_only_filter(start_date, end_date)
    sql = f"""
    WITH customer_first_order AS (
        SELECT
            c.customer_unique_id,
            MIN(DATE_TRUNC('month', o.order_purchase_timestamp)) AS cohort_month
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        WHERE {where}
        GROUP BY c.customer_unique_id
    ),
    customer_orders AS (
        SELECT DISTINCT
            c.customer_unique_id,
            DATE_TRUNC('month', o.order_purchase_timestamp) AS order_month
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        WHERE {where}
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


def rfm_segments(start_date=None, end_date=None, states=None):
    where = _date_only_filter(start_date, end_date)
    sql = f"""
    WITH customer_metrics AS (
        SELECT
            c.customer_unique_id,
            MAX(o.order_purchase_timestamp)::date AS last_order_date,
            COUNT(DISTINCT o.order_id) AS frequency,
            SUM(oi.price + oi.freight_value)::numeric AS monetary
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE {where}
        GROUP BY c.customer_unique_id
    ),
    snapshot AS (
        SELECT MAX(last_order_date) + INTERVAL '1 day' AS snap FROM customer_metrics
    ),
    scored AS (
        SELECT
            customer_unique_id,
            ((SELECT snap FROM snapshot)::date - last_order_date) AS recency_days,
            frequency,
            monetary,
            NTILE(5) OVER (ORDER BY ((SELECT snap FROM snapshot)::date - last_order_date) DESC) AS r_score,
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