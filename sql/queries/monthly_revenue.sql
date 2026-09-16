SELECT
    DATE_TRUNC('month', o.order_purchase_timestamp) AS month,
    ROUND(SUM(oi.price + oi.freight_value)::numeric, 2) AS revenue,
    COUNT(DISTINCT o.order_id) AS orders,
    ROUND(AVG(oi.price + oi.freight_value)::numeric, 2) AS avg_item_value
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.order_status NOT IN ('canceled', 'unavailable')
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp < '2019-01-01'
GROUP BY month
ORDER BY month;