import pandas as pd

from backend.db import engine


def device_conversion_analysis():

    query = """
    SELECT
        device,
        traffic_source,
        total_sessions,
        add_to_cart_sessions,
        converted_sessions,
        avg_pages_viewed,
        avg_session_duration_seconds
    FROM vw_website_funnel;
    """

    df = pd.read_sql(query, engine)

    df["weighted_pages"] = (
        df["avg_pages_viewed"]
        * df["total_sessions"]
    )

    df["weighted_duration"] = (
        df["avg_session_duration_seconds"]
        * df["total_sessions"]
    )

    summary = (
        df.groupby("device")
        .agg(
            total_sessions=("total_sessions", "sum"),
            add_to_cart_sessions=("add_to_cart_sessions", "sum"),
            converted_sessions=("converted_sessions", "sum"),
            weighted_pages=("weighted_pages", "sum"),
            weighted_duration=("weighted_duration", "sum")
        )
        .reset_index()
    )

    summary["add_to_cart_rate_pct"] = (
        summary["add_to_cart_sessions"]
        / summary["total_sessions"]
        * 100
    )

    summary["conversion_rate_pct"] = (
        summary["converted_sessions"]
        / summary["total_sessions"]
        * 100
    )

    summary["cart_to_conversion_pct"] = (
        summary["converted_sessions"]
        / summary["add_to_cart_sessions"]
        * 100
    )

    summary["avg_pages_viewed"] = (
        summary["weighted_pages"]
        / summary["total_sessions"]
    )

    summary["avg_session_duration_seconds"] = (
        summary["weighted_duration"]
        / summary["total_sessions"]
    )

    summary = summary[
        [
            "device",
            "total_sessions",
            "add_to_cart_sessions",
            "converted_sessions",
            "add_to_cart_rate_pct",
            "conversion_rate_pct",
            "cart_to_conversion_pct",
            "avg_pages_viewed",
            "avg_session_duration_seconds"
        ]
    ]

    return summary.to_dict(
        orient="records"
    )