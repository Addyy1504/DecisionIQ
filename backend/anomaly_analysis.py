import pandas as pd

from backend.db import engine


def monthly_anomaly_analysis():

    query = """
    SELECT
        DATE_FORMAT(order_date, '%Y-%m') AS month,
        SUM(net_revenue) AS net_revenue,
        SUM(gross_profit) AS gross_profit,
        SUM(refund_amount) AS refunds,
        SUM(is_returned) AS returned_items,
        COUNT(order_item_id) AS total_items
    FROM vw_order_item_metrics
    GROUP BY DATE_FORMAT(order_date, '%Y-%m')
    ORDER BY month;
    """

    df = pd.read_sql(query, engine)

    df["return_rate_pct"] = (
        df["returned_items"]
        / df["total_items"]
        * 100
    )

    # Detect unusual monthly changes instead of raw levels
    change_metrics = [
        "net_revenue",
        "gross_profit",
        "refunds"
    ]

    for metric in change_metrics:

        df[f"{metric}_growth_pct"] = (
            df[metric]
            .pct_change(fill_method=None)
            * 100
        )

        growth_col = f"{metric}_growth_pct"

        rolling_mean = (
            df[growth_col]
            .shift(1)
            .rolling(
                window=6,
                min_periods=4
            )
            .mean()
        )

        rolling_std = (
            df[growth_col]
            .shift(1)
            .rolling(
                window=6,
                min_periods=4
            )
            .std()
        )

        df[f"{metric}_zscore"] = (
            (df[growth_col] - rolling_mean)
            / rolling_std.replace(0, pd.NA)
        )

        df[f"{metric}_anomaly"] = (
            df[f"{metric}_zscore"].abs() >= 2.5
        )

    # Return rate is already a rate,
    # so compare its level against recent history
    return_mean = (
        df["return_rate_pct"]
        .shift(1)
        .rolling(
            window=6,
            min_periods=4
        )
        .mean()
    )

    return_std = (
        df["return_rate_pct"]
        .shift(1)
        .rolling(
            window=6,
            min_periods=4
        )
        .std()
    )

    df["return_rate_pct_zscore"] = (
        (df["return_rate_pct"] - return_mean)
        / return_std.replace(0, pd.NA)
    )

    df["return_rate_pct_anomaly"] = (
        df["return_rate_pct_zscore"].abs() >= 2.5
    )

    anomaly_columns = [
        "net_revenue_anomaly",
        "gross_profit_anomaly",
        "refunds_anomaly",
        "return_rate_pct_anomaly"
    ]

    df["is_anomaly"] = (
        df[anomaly_columns]
        .any(axis=1)
    )

    return df.to_dict(
        orient="records"
    )