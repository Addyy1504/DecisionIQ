USE decisioniq;

CREATE OR REPLACE VIEW vw_customer_metrics AS



SELECT
    c.customer_id,
    c.customer_name,
    c.age,
    c.gender,
    c.city,
    c.state,
    c.signup_date,
    c.acquisition_channel,

    COUNT(DISTINCT v.order_id) AS total_orders,

    ROUND(SUM(v.net_revenue), 2) AS net_revenue,

    ROUND(SUM(v.cogs), 2) AS cogs,

    ROUND(SUM(v.gross_profit), 2) AS gross_profit,

    COUNT(v.order_item_id) AS total_items,

    SUM(v.is_returned) AS returned_items,

    ROUND(
        SUM(v.is_returned)
        / NULLIF(COUNT(v.order_item_id), 0)
        * 100,
        2
    ) AS return_rate_pct,

    ROUND(
        SUM(v.net_revenue)
        / NULLIF(COUNT(DISTINCT v.order_id), 0),
        2
    ) AS avg_order_value

FROM customers c

LEFT JOIN vw_order_item_metrics v
    ON c.customer_id = v.customer_id

GROUP BY
    c.customer_id,
    c.customer_name,
    c.age,
    c.gender,
    c.city,
    c.state,
    c.signup_date,
    c.acquisition_channel;vw_order_item_metrics
    
    
SELECT *
FROM vw_customer_metrics
LIMIT 10;

SELECT
    ROUND(SUM(net_revenue), 2) AS net_revenue,
    ROUND(SUM(gross_profit), 2) AS gross_profit
FROM vw_customer_metrics;