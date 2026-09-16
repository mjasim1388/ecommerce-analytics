SELECT
    p.product_category_name AS category,
    COUNT(DISTINCT oi.order_id) AS orders,
    SUM(oi.order_item_id) AS items_sold,
    ROUND(SUM(oi.price)::numeric, 2) AS revenue,
    ROUND(AVG(oi.price)::numeric, 2) AS avg_price
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
JOIN orders o ON o.order_id = oi.order_id
WHERE o.order_status NOT IN ('canceled', 'unavailable')
  AND p.product_category_name IS NOT NULL
GROUP BY category
ORDER BY revenue DESC
LIMIT 20;