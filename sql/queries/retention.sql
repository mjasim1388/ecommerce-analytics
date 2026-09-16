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