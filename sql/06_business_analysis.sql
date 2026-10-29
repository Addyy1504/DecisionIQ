USE decisioniq;

-- 1. Category Profitability Analysis

SELECT
    p.category,

    COUNT(DISTINCT o.order_id) AS total_orders,

    ROUND(
        SUM(
            oi.quantity
            * oi.unit_price
            * (1 - oi.discount_pct)
        ),
        2
    ) AS discounted_sales,

    ROUND(
        COALESCE(SUM(r.refund_amount), 0),
        2
    ) AS refunds,

    ROUND(
        SUM(
            oi.quantity
            * oi.unit_price
            * (1 - oi.discount_pct)
        )
        -
        COALESCE(SUM(r.refund_amount), 0),
        2
    ) AS net_revenue,

    ROUND(
        SUM(
            CASE
                WHEN r.return_id IS NULL
                THEN oi.quantity * p.cost_price
                ELSE 0
            END
        ),
        2
    ) AS cogs,

    ROUND(
        (
            SUM(
                oi.quantity
                * oi.unit_price
                * (1 - oi.discount_pct)
            )
            -
            COALESCE(SUM(r.refund_amount), 0)
        )
        -
        SUM(
            CASE
                WHEN r.return_id IS NULL
                THEN oi.quantity * p.cost_price
                ELSE 0
            END
        ),
        2
    ) AS gross_profit,

    ROUND(
        COUNT(r.return_id)
        / COUNT(oi.order_item_id)
        * 100,
        2
    ) AS return_rate_pct

FROM order_items oi
JOIN orders o
    ON oi.order_id = o.order_id
JOIN products p
    ON oi.product_id = p.product_id
LEFT JOIN returns r
    ON oi.order_item_id = r.order_item_id

WHERE o.order_status <> 'Cancelled'

GROUP BY p.category

ORDER BY gross_profit DESC;








-- 2. Discount Impact on Profitability

SELECT
    ROUND(oi.discount_pct * 100, 0) AS discount_pct,

    COUNT(DISTINCT o.order_id) AS total_orders,

    ROUND(
        SUM(
            oi.quantity
            * oi.unit_price
        ),
        2
    ) AS gross_sales,

    ROUND(
        SUM(
            oi.quantity
            * oi.unit_price
            * (1 - oi.discount_pct)
        ),
        2
    ) AS discounted_sales,

    ROUND(
        COALESCE(
            SUM(r.refund_amount),
            0
        ),
        2
    ) AS refunds,

    ROUND(
        SUM(
            oi.quantity
            * oi.unit_price
            * (1 - oi.discount_pct)
        )
        -
        COALESCE(
            SUM(r.refund_amount),
            0
        ),
        2
    ) AS net_revenue,

    ROUND(
        (
            (
                SUM(
                    oi.quantity
                    * oi.unit_price
                    * (1 - oi.discount_pct)
                )
                -
                COALESCE(
                    SUM(r.refund_amount),
                    0
                )
            )
            -
            SUM(
                CASE
                    WHEN r.return_id IS NULL
                    THEN oi.quantity * p.cost_price
                    ELSE 0
                END
            )
        ),
        2
    ) AS gross_profit,

    ROUND(
        COUNT(r.return_id)
        / COUNT(oi.order_item_id)
        * 100,
        2
    ) AS return_rate_pct

FROM order_items oi

JOIN orders o
    ON oi.order_id = o.order_id

JOIN products p
    ON oi.product_id = p.product_id

LEFT JOIN returns r
    ON oi.order_item_id = r.order_item_id

WHERE o.order_status <> 'Cancelled'

GROUP BY oi.discount_pct

ORDER BY discount_pct;








-- 3. Gross Margin by Discount Band

SELECT
    ROUND(oi.discount_pct * 100, 0) AS discount_pct,

    ROUND(
        (
            (
                SUM(
                    oi.quantity
                    * oi.unit_price
                    * (1 - oi.discount_pct)
                )
                -
                COALESCE(
                    SUM(r.refund_amount),
                    0
                )
            )
            -
            SUM(
                CASE
                    WHEN r.return_id IS NULL
                    THEN oi.quantity * p.cost_price
                    ELSE 0
                END
            )
        )
        /
        NULLIF(
            (
                SUM(
                    oi.quantity
                    * oi.unit_price
                    * (1 - oi.discount_pct)
                )
                -
                COALESCE(
                    SUM(r.refund_amount),
                    0
                )
            ),
            0
        )
        * 100,
        2
    ) AS gross_margin_pct

FROM order_items oi

JOIN orders o
    ON oi.order_id = o.order_id

JOIN products p
    ON oi.product_id = p.product_id

LEFT JOIN returns r
    ON oi.order_item_id = r.order_item_id

WHERE o.order_status <> 'Cancelled'

GROUP BY oi.discount_pct

ORDER BY discount_pct;





-- 4. High-Discount Profitability by Category

SELECT
    p.category,

    ROUND(
        oi.discount_pct * 100,
        0
    ) AS discount_pct,

    COUNT(oi.order_item_id) AS total_items,

    ROUND(
        SUM(
            oi.quantity
            * oi.unit_price
            * (1 - oi.discount_pct)
        ),
        2
    ) AS discounted_sales,

    ROUND(
        COALESCE(
            SUM(r.refund_amount),
            0
        ),
        2
    ) AS refunds,

    ROUND(
        SUM(
            oi.quantity
            * oi.unit_price
            * (1 - oi.discount_pct)
        )
        -
        COALESCE(
            SUM(r.refund_amount),
            0
        ),
        2
    ) AS net_revenue,

    ROUND(
        SUM(
            CASE
                WHEN r.return_id IS NULL
                THEN oi.quantity * p.cost_price
                ELSE 0
            END
        ),
        2
    ) AS cogs,

    ROUND(
        (
            SUM(
                oi.quantity
                * oi.unit_price
                * (1 - oi.discount_pct)
            )
            -
            COALESCE(
                SUM(r.refund_amount),
                0
            )
        )
        -
        SUM(
            CASE
                WHEN r.return_id IS NULL
                THEN oi.quantity * p.cost_price
                ELSE 0
            END
        ),
        2
    ) AS gross_profit,

    ROUND(
        (
            (
                SUM(
                    oi.quantity
                    * oi.unit_price
                    * (1 - oi.discount_pct)
                )
                -
                COALESCE(
                    SUM(r.refund_amount),
                    0
                )
            )
            -
            SUM(
                CASE
                    WHEN r.return_id IS NULL
                    THEN oi.quantity * p.cost_price
                    ELSE 0
                END
            )
        )
        /
        NULLIF(
            SUM(
                oi.quantity
                * oi.unit_price
                * (1 - oi.discount_pct)
            )
            -
            COALESCE(
                SUM(r.refund_amount),
                0
            ),
            0
        ) * 100,
        2
    ) AS gross_margin_pct

FROM order_items oi

JOIN orders o
    ON oi.order_id = o.order_id

JOIN products p
    ON oi.product_id = p.product_id

LEFT JOIN returns r
    ON oi.order_item_id = r.order_item_id

WHERE o.order_status <> 'Cancelled'
  AND oi.discount_pct >= 0.25

GROUP BY
    p.category,
    oi.discount_pct

ORDER BY
    discount_pct DESC,
    gross_profit ASC;
    
    
    
    
    
    
    
    
-- 5. Customer Value by Acquisition Channel

WITH customer_metrics AS (

    SELECT
        c.customer_id,
        c.acquisition_channel,

        COUNT(
            DISTINCT o.order_id
        ) AS completed_orders,

        COALESCE(
            SUM(
                oi.quantity
                * oi.unit_price
                * (1 - oi.discount_pct)
            ),
            0
        )
        -
        COALESCE(
            SUM(r.refund_amount),
            0
        ) AS net_revenue,

        COALESCE(
            SUM(
                CASE
                    WHEN r.return_id IS NULL
                    THEN oi.quantity * p.cost_price
                    ELSE 0
                END
            ),
            0
        ) AS cogs

    FROM customers c

    LEFT JOIN orders o
        ON c.customer_id = o.customer_id
        AND o.order_status <> 'Cancelled'

    LEFT JOIN order_items oi
        ON o.order_id = oi.order_id

    LEFT JOIN products p
        ON oi.product_id = p.product_id

    LEFT JOIN returns r
        ON oi.order_item_id = r.order_item_id

    GROUP BY
        c.customer_id,
        c.acquisition_channel
)

SELECT
    acquisition_channel,

    COUNT(*) AS total_customers,

    SUM(
        completed_orders > 0
    ) AS purchasing_customers,

    SUM(completed_orders) AS total_orders,

    ROUND(
        AVG(completed_orders),
        2
    ) AS avg_orders_per_customer,

    ROUND(
        SUM(net_revenue),
        2
    ) AS net_revenue,

    ROUND(
        SUM(net_revenue - cogs),
        2
    ) AS gross_profit,

    ROUND(
        AVG(net_revenue),
        2
    ) AS avg_revenue_per_customer

FROM customer_metrics

GROUP BY acquisition_channel

ORDER BY gross_profit DESC;







-- 6. Normalized Customer Quality by Acquisition Channel

WITH customer_metrics AS (

    SELECT
        c.customer_id,
        c.acquisition_channel,

        COUNT(DISTINCT o.order_id) AS completed_orders,

        COALESCE(
            SUM(
                oi.quantity
                * oi.unit_price
                * (1 - oi.discount_pct)
            ),
            0
        )
        -
        COALESCE(
            SUM(r.refund_amount),
            0
        ) AS net_revenue,

        COALESCE(
            SUM(
                CASE
                    WHEN r.return_id IS NULL
                    THEN oi.quantity * p.cost_price
                    ELSE 0
                END
            ),
            0
        ) AS cogs

    FROM customers c

    LEFT JOIN orders o
        ON c.customer_id = o.customer_id
        AND o.order_status <> 'Cancelled'

    LEFT JOIN order_items oi
        ON o.order_id = oi.order_id

    LEFT JOIN products p
        ON oi.product_id = p.product_id

    LEFT JOIN returns r
        ON oi.order_item_id = r.order_item_id

    GROUP BY
        c.customer_id,
        c.acquisition_channel
)

SELECT
    acquisition_channel,

    COUNT(*) AS total_customers,

    SUM(completed_orders > 0) AS purchasing_customers,

    ROUND(
        SUM(completed_orders > 0)
        / COUNT(*) * 100,
        2
    ) AS purchase_rate_pct,

    ROUND(
        SUM(completed_orders)
        /
        NULLIF(
            SUM(completed_orders > 0),
            0
        ),
        2
    ) AS avg_orders_per_purchasing_customer,

    ROUND(
        SUM(net_revenue)
        / COUNT(*),
        2
    ) AS avg_revenue_per_customer,

    ROUND(
        SUM(net_revenue - cogs)
        / COUNT(*),
        2
    ) AS avg_profit_per_customer

FROM customer_metrics

GROUP BY acquisition_channel

ORDER BY avg_profit_per_customer DESC;


-- 7. State-Level Profitability Analysis

SELECT
    c.state,

    COUNT(DISTINCT c.customer_id) AS customers,

    COUNT(DISTINCT o.order_id) AS orders,

    ROUND(
        SUM(
            oi.quantity
            * oi.unit_price
            * (1 - oi.discount_pct)
        ),
        2
    ) AS discounted_sales,

    ROUND(
        COALESCE(
            SUM(r.refund_amount),
            0
        ),
        2
    ) AS refunds,

    ROUND(
        SUM(
            oi.quantity
            * oi.unit_price
            * (1 - oi.discount_pct)
        )
        -
        COALESCE(
            SUM(r.refund_amount),
            0
        ),
        2
    ) AS net_revenue,

    ROUND(
        SUM(
            CASE
                WHEN r.return_id IS NULL
                THEN oi.quantity * p.cost_price
                ELSE 0
            END
        ),
        2
    ) AS cogs,

    ROUND(
        (
            SUM(
                oi.quantity
                * oi.unit_price
                * (1 - oi.discount_pct)
            )
            -
            COALESCE(
                SUM(r.refund_amount),
                0
            )
        )
        -
        SUM(
            CASE
                WHEN r.return_id IS NULL
                THEN oi.quantity * p.cost_price
                ELSE 0
            END
        ),
        2
    ) AS gross_profit,

    ROUND(
        (
            (
                SUM(
                    oi.quantity
                    * oi.unit_price
                    * (1 - oi.discount_pct)
                )
                -
                COALESCE(
                    SUM(r.refund_amount),
                    0
                )
            )
            -
            SUM(
                CASE
                    WHEN r.return_id IS NULL
                    THEN oi.quantity * p.cost_price
                    ELSE 0
                END
            )
        )
        /
        NULLIF(
            SUM(
                oi.quantity
                * oi.unit_price
                * (1 - oi.discount_pct)
            )
            -
            COALESCE(
                SUM(r.refund_amount),
                0
            ),
            0
        ) * 100,
        2
    ) AS gross_margin_pct,

    ROUND(
        COUNT(r.return_id)
        / COUNT(oi.order_item_id)
        * 100,
        2
    ) AS return_rate_pct

FROM customers c

JOIN orders o
    ON c.customer_id = o.customer_id

JOIN order_items oi
    ON o.order_id = oi.order_id

JOIN products p
    ON oi.product_id = p.product_id

LEFT JOIN returns r
    ON oi.order_item_id = r.order_item_id

WHERE o.order_status <> 'Cancelled'

GROUP BY c.state

ORDER BY gross_profit DESC;


-- 8. Website Funnel Performance by Device

SELECT
    device,

    COUNT(*) AS total_sessions,

    SUM(added_to_cart) AS add_to_cart_sessions,

    SUM(converted) AS converted_sessions,

    ROUND(
        SUM(added_to_cart)
        / COUNT(*) * 100,
        2
    ) AS add_to_cart_rate_pct,

    ROUND(
        SUM(converted)
        / COUNT(*) * 100,
        2
    ) AS conversion_rate_pct,

    ROUND(
        SUM(
            CASE
                WHEN added_to_cart = 1
                AND converted = 1
                THEN 1
                ELSE 0
            END
        )
        /
        NULLIF(
            SUM(added_to_cart),
            0
        ) * 100,
        2
    ) AS cart_to_conversion_pct,

    ROUND(
        AVG(pages_viewed),
        2
    ) AS avg_pages_viewed,

    ROUND(
        AVG(session_duration_seconds),
        2
    ) AS avg_session_duration_sec

FROM website_sessions

GROUP BY device

ORDER BY conversion_rate_pct DESC;








-- 9. Conversion Rate by Device and Traffic Source

SELECT
    device,
    traffic_source,

    COUNT(*) AS total_sessions,

    SUM(added_to_cart) AS add_to_cart_sessions,

    SUM(converted) AS converted_sessions,

    ROUND(
        SUM(added_to_cart)
        / COUNT(*) * 100,
        2
    ) AS add_to_cart_rate_pct,

    ROUND(
        SUM(converted)
        / COUNT(*) * 100,
        2
    ) AS conversion_rate_pct,

    ROUND(
        SUM(
            CASE
                WHEN added_to_cart = 1
                 AND converted = 1
                THEN 1
                ELSE 0
            END
        )
        /
        NULLIF(SUM(added_to_cart), 0)
        * 100,
        2
    ) AS cart_to_conversion_pct

FROM website_sessions

GROUP BY
    device,
    traffic_source

ORDER BY
    traffic_source,
    conversion_rate_pct DESC;
    
    
    
    
    
-- 10. Mobile Conversion Opportunity vs Desktop Benchmark

WITH device_source_metrics AS (

    SELECT
        traffic_source,
        device,

        COUNT(*) AS sessions,

        SUM(converted) AS conversions,

        SUM(converted)
        / COUNT(*) AS conversion_rate

    FROM website_sessions

    GROUP BY
        traffic_source,
        device
),

desktop_rates AS (

    SELECT
        traffic_source,
        conversion_rate
            AS desktop_conversion_rate

    FROM device_source_metrics

    WHERE device = 'Desktop'
),

mobile_metrics AS (

    SELECT
        traffic_source,
        sessions,
        conversions,
        conversion_rate
            AS mobile_conversion_rate

    FROM device_source_metrics

    WHERE device = 'Mobile'
)

SELECT
    m.traffic_source,

    m.sessions AS mobile_sessions,

    ROUND(
        m.mobile_conversion_rate * 100,
        2
    ) AS mobile_conversion_rate_pct,

    ROUND(
        d.desktop_conversion_rate * 100,
        2
    ) AS desktop_conversion_rate_pct,

    ROUND(
        (
            d.desktop_conversion_rate
            - m.mobile_conversion_rate
        ) * 100,
        2
    ) AS conversion_gap_pct_points,

    ROUND(
        m.sessions
        *
        (
            d.desktop_conversion_rate
            - m.mobile_conversion_rate
        ),
        0
    ) AS potential_additional_conversions

FROM mobile_metrics m

JOIN desktop_rates d
    ON m.traffic_source = d.traffic_source

ORDER BY
    potential_additional_conversions DESC;
    
    
    
    
-- 11. Marketing Channel Performance

SELECT
    mc.channel,

    COUNT(
        DISTINCT mc.campaign_id
    ) AS campaigns,

    SUM(cp.impressions) AS impressions,

    SUM(cp.clicks) AS clicks,

    SUM(cp.conversions) AS conversions,

    ROUND(
        SUM(cp.ad_spend),
        2
    ) AS ad_spend,

    ROUND(
        SUM(cp.revenue_generated),
        2
    ) AS attributed_revenue,

    -- Click Through Rate
    ROUND(
        SUM(cp.clicks)
        / NULLIF(
            SUM(cp.impressions),
            0
        ) * 100,
        2
    ) AS ctr_pct,

    -- Conversion Rate after click
    ROUND(
        SUM(cp.conversions)
        / NULLIF(
            SUM(cp.clicks),
            0
        ) * 100,
        2
    ) AS click_conversion_rate_pct,

    -- Cost per conversion
    ROUND(
        SUM(cp.ad_spend)
        / NULLIF(
            SUM(cp.conversions),
            0
        ),
        2
    ) AS cpa,

    -- Return on Ad Spend
    ROUND(
        SUM(cp.revenue_generated)
        / NULLIF(
            SUM(cp.ad_spend),
            0
        ),
        2
    ) AS roas

FROM marketing_campaigns mc

JOIN campaign_performance cp
    ON mc.campaign_id = cp.campaign_id

GROUP BY mc.channel

ORDER BY roas DESC;




-- 12. Marketing Spend vs Revenue Share

WITH channel_metrics AS (

    SELECT
        mc.channel,

        SUM(cp.ad_spend) AS ad_spend,

        SUM(cp.revenue_generated) AS revenue,

        SUM(cp.conversions) AS conversions

    FROM marketing_campaigns mc

    JOIN campaign_performance cp
        ON mc.campaign_id = cp.campaign_id

    GROUP BY mc.channel
)

SELECT
    channel,

    ROUND(ad_spend, 2) AS ad_spend,

    ROUND(
        ad_spend
        / SUM(ad_spend) OVER ()
        * 100,
        2
    ) AS spend_share_pct,

    ROUND(revenue, 2) AS attributed_revenue,

    ROUND(
        revenue
        / SUM(revenue) OVER ()
        * 100,
        2
    ) AS revenue_share_pct,

    ROUND(
        revenue
        / NULLIF(ad_spend, 0),
        2
    ) AS roas,

    ROUND(
        ad_spend
        / NULLIF(conversions, 0),
        2
    ) AS cpa

FROM channel_metrics

ORDER BY roas DESC;




-- 13. Monthly Revenue and Profit Trend

SELECT
    DATE_FORMAT(o.order_date, '%Y-%m') AS month,

    COUNT(DISTINCT o.order_id) AS orders,

    ROUND(
        SUM(
            oi.quantity
            * oi.unit_price
            * (1 - oi.discount_pct)
        )
        -
        COALESCE(
            SUM(r.refund_amount),
            0
        ),
        2
    ) AS net_revenue,

    ROUND(
        (
            SUM(
                oi.quantity
                * oi.unit_price
                * (1 - oi.discount_pct)
            )
            -
            COALESCE(
                SUM(r.refund_amount),
                0
            )
        )
        -
        SUM(
            CASE
                WHEN r.return_id IS NULL
                THEN oi.quantity * p.cost_price
                ELSE 0
            END
        ),
        2
    ) AS gross_profit,

    ROUND(
        COUNT(r.return_id)
        / COUNT(oi.order_item_id)
        * 100,
        2
    ) AS return_rate_pct

FROM orders o

JOIN order_items oi
    ON o.order_id = oi.order_id

JOIN products p
    ON oi.product_id = p.product_id

LEFT JOIN returns r
    ON oi.order_item_id = r.order_item_id

WHERE o.order_status <> 'Cancelled'

GROUP BY
    DATE_FORMAT(o.order_date, '%Y-%m')

ORDER BY month;