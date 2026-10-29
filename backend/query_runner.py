from sqlalchemy import text
from backend.db import engine


ALLOWED_VIEWS = {
    "vw_order_item_metrics",
    "vw_customer_metrics",
    "vw_marketing_metrics",
    "vw_website_funnel"
}


def validate_query(query: str):

    cleaned_query = query.strip().lower()

    # Only SELECT queries allowed
    if not cleaned_query.startswith("select"):
        raise ValueError(
            "Only SELECT queries are allowed."
        )

    # Block dangerous SQL keywords
    blocked_keywords = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "create",
        "replace"
    ]

    for keyword in blocked_keywords:
        if keyword in cleaned_query:
            raise ValueError(
                f"Blocked SQL keyword detected: {keyword}"
            )

    # AI should mainly query semantic views
    if not any(
        view in cleaned_query
        for view in ALLOWED_VIEWS
    ):
        raise ValueError(
            "Query must use an approved analytical view."
        )

    return True


def run_query(query: str):

    validate_query(query)

    with engine.connect() as connection:

        result = connection.execute(
            text(query)
        )

        rows = result.fetchall()

        columns = list(
            result.keys()
        )

    data = [
        dict(zip(columns, row))
        for row in rows
    ]

    return data