SELECT
    c.customer_state AS state,
    COUNT(DISTINCT o.order_id) AS orders,
    COUNT(DISTINCT c.customer_unique_id) AS customers,
    ROUND(SUM(oi.price + oi.freight_value)::numeric, 2) AS revenue,
    ROUND(
        (SUM(oi.price + oi.freight_value) / COUNT(DISTINCT o.order_id))::numeric,
        2
    ) AS aov
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY state
ORDER BY revenue DESC;