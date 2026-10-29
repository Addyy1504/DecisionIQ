import pandas as pd

from backend.db import engine


def category_profitability_analysis():

    query = """
    SELECT
        category,
        COUNT(DISTINCT order_id) AS orders,
        SUM(discounted_sales) AS discounted_sales,
        SUM(refund_amount) AS refunds,
        SUM(net_revenue) AS net_revenue,
        SUM(cogs) AS cogs,
        SUM(gross_profit) AS gross_profit,
        SUM(is_returned) AS returned_items,
        COUNT(order_item_id) AS total_items
    FROM vw_order_item_metrics
    GROUP BY category;
    """

    df = pd.read_sql(query, engine)

    df["gross_margin_pct"] = (
        df["gross_profit"]
        / df["net_revenue"]
        * 100
    )

    df["return_rate_pct"] = (
        df["returned_items"]
        / df["total_items"]
        * 100
    )

    df["refund_rate_pct"] = (
        df["refunds"]
        / df["discounted_sales"]
        * 100
    )

    df = df.sort_values(
        "gross_profit",
        ascending=False
    )

    return df.to_dict(
        orient="records"
    )