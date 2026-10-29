import pandas as pd

from backend.db import engine


def discount_profitability_analysis():

    query = """
    SELECT
        discount_pct,
        SUM(gross_sales) AS gross_sales,
        SUM(discounted_sales) AS discounted_sales,
        SUM(refund_amount) AS refunds,
        SUM(net_revenue) AS net_revenue,
        SUM(cogs) AS cogs,
        SUM(gross_profit) AS gross_profit,
        SUM(is_returned) AS returned_items,
        COUNT(order_item_id) AS total_items
    FROM vw_order_item_metrics
    GROUP BY discount_pct
    ORDER BY discount_pct;
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

    df["discount_pct"] = (
        df["discount_pct"] * 100
    )

    return df.to_dict(
        orient="records"
    )



def simulate_discount_margin(discount_pct: float):

    query = """
    SELECT
        SUM(gross_sales) AS gross_sales,
        SUM(cogs) AS cogs,
        SUM(refund_amount) AS refunds
    FROM vw_order_item_metrics;
    """

    df = pd.read_sql(query, engine)

    gross_sales = float(df.loc[0, "gross_sales"])
    cogs = float(df.loc[0, "cogs"])
    refunds = float(df.loc[0, "refunds"])

    discount_decimal = discount_pct / 100

    # Baseline: 0% discount
    baseline_discounted_sales = gross_sales
    baseline_net_revenue = gross_sales - refunds
    baseline_gross_profit = baseline_net_revenue - cogs

    baseline_margin_pct = (
        baseline_gross_profit
        / baseline_net_revenue
        * 100
    )

    # Simulated scenario
    simulated_discounted_sales = (
        gross_sales
        * (1 - discount_decimal)
    )

    simulated_net_revenue = (
        simulated_discounted_sales
        - refunds
    )

    simulated_gross_profit = (
        simulated_net_revenue
        - cogs
    )

    simulated_margin_pct = (
        simulated_gross_profit
        / simulated_net_revenue
        * 100
    )

    profit_change = (
        simulated_gross_profit
        - baseline_gross_profit
    )

    profit_change_pct = (
        profit_change
        / baseline_gross_profit
        * 100
    )

    margin_change_pp = (
        simulated_margin_pct
        - baseline_margin_pct
    )

    return {
        "discount_pct": discount_pct,

        "baseline_gross_profit": baseline_gross_profit,
        "baseline_margin_pct": baseline_margin_pct,

        "simulated_discounted_sales": simulated_discounted_sales,
        "simulated_net_revenue": simulated_net_revenue,
        "simulated_gross_profit": simulated_gross_profit,
        "simulated_margin_pct": simulated_margin_pct,

        "profit_change": profit_change,
        "profit_change_pct": profit_change_pct,
        "margin_change_pp": margin_change_pp
    }