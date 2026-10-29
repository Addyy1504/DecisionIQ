import re


def extract_discount_percentage(question: str):
    """
    Extract an explicit discount percentage from the question.

    Examples:
    "What happens at 25% discount?" -> 25.0
    "simulate a 20 percent discount" -> 20.0
    """

    if not question:
        return None

    patterns = [
        r"(\d+(?:\.\d+)?)\s*%",
        r"(\d+(?:\.\d+)?)\s*percent",
    ]

    q = question.lower()

    for pattern in patterns:
        match = re.search(pattern, q)

        if match:
            value = float(match.group(1))

            if 0 <= value <= 100:
                return value

    return None


def choose_analysis_routes(question: str):
    """
    Deterministic first-pass router for DecisionIQ.

    A question may return more than one route when it contains
    multiple analytical intents.
    """

    q = (question or "").lower().strip()

    routes = []


    # =====================================================
    # DATA SCIENCE — CUSTOMER SEGMENTATION
    # =====================================================

    segmentation_keywords = [
        "customer segment",
        "customer segments",
        "customer segmentation",
        "segmentation",
        "rfm",
        "k-means",
        "k means",
        "cluster",
        "clustering",
        "high-value customer",
        "high value customer",
        "high-value loyal",
        "high value loyal",
        "loyal customer",
        "loyal customers",
        "at risk customer",
        "at-risk customer",
        "regular customer",
        "regular customers",
    ]

    if any(
        keyword in q
        for keyword in segmentation_keywords
    ):
        routes.append(
            "customer_segmentation_analysis"
        )


    # =====================================================
    # DATA SCIENCE — RETURN RISK MODEL
    # =====================================================

    return_risk_keywords = [
        "return risk",
        "return-risk",
        "return probability",
        "predicted return",
        "predict return",
        "return prediction",
        "return model",
        "return-risk model",
        "high risk item",
        "high-risk item",
        "high risk order",
        "high-risk order",
        "highest risk item",
        "highest risk order",
        "risk of return",
        "roc auc",
        "roc-auc",
        "f1 score",
        "model precision",
        "model recall",
        "feature importance",
        "predictive feature",
        "predictive features",
    ]

    if any(
        keyword in q
        for keyword in return_risk_keywords
    ):
        routes.append(
            "return_risk_analysis"
        )


    # =====================================================
    # DEVICE / FUNNEL
    # =====================================================

    device_keywords = [
        "mobile",
        "desktop",
        "tablet",
        "device",
        "conversion",
        "funnel",
        "checkout",
        "cart",
        "add-to-cart",
        "add to cart",
        "dropoff",
        "drop-off",
    ]

    if any(
        keyword in q
        for keyword in device_keywords
    ):
        routes.append(
            "device_conversion_analysis"
        )


    # =====================================================
    # CATEGORY PROFITABILITY
    # =====================================================

    profitability_keywords = [
        "profitability",
        "gross profit",
        "gross margin",
        "margin",
        "refund pressure",
        "return pressure",
        "category performance",
        "category profit",
        "profit by category",
        "fashion performance",
        "electronics performance",
    ]

    diagnostic_words = [
        "why",
        "explain",
        "driver",
        "drivers",
        "pressure",
        "performance",
        "compare",
        "comparison",
    ]

    has_profitability_signal = any(
        keyword in q
        for keyword in profitability_keywords
    )

    has_diagnostic_signal = any(
        keyword in q
        for keyword in diagnostic_words
    )

    if (
        has_profitability_signal
        and has_diagnostic_signal
    ):
        routes.append(
            "category_profitability_analysis"
        )


    # =====================================================
    # DISCOUNT WHAT-IF
    # =====================================================

    discount_pct = extract_discount_percentage(
        question
    )

    discount_words = [
        "discount",
        "discounts",
        "markdown",
        "price cut",
    ]

    scenario_words = [
        "what if",
        "what happens",
        "simulate",
        "simulation",
        "scenario",
        "increase to",
        "decrease to",
        "set discount",
        "at ",
    ]

    has_discount_word = any(
        word in q
        for word in discount_words
    )

    has_scenario_word = any(
        word in q
        for word in scenario_words
    )

    if (
        discount_pct is not None
        and has_discount_word
        and has_scenario_word
    ):
        routes.append(
            "discount_what_if"
        )


    # =====================================================
    # HISTORICAL DISCOUNT / DEMAND EVIDENCE → SQL
    # =====================================================

    historical_discount_words = [
        "demand",
        "orders",
        "units",
        "volume",
        "sales volume",
        "increase demand",
        "higher demand",
        "caused demand",
        "cause demand",
        "did discounts",
        "historical discount",
        "discount band",
        "discount bands",
    ]

    if (
        has_discount_word
        and any(
            word in q
            for word in historical_discount_words
        )
        and "discount_what_if" not in routes
    ):
        routes.append("sql")


    # =====================================================
    # MONTHLY ANOMALIES
    # =====================================================

    anomaly_keywords = [
        "anomaly",
        "anomalies",
        "unusual",
        "spike",
        "spikes",
        "drop",
        "drops",
        "outlier",
        "outliers",
        "abnormal",
        "unexpected movement",
        "unusual movement",
    ]

    if any(
        keyword in q
        for keyword in anomaly_keywords
    ):
        routes.append(
            "monthly_anomaly_analysis"
        )


    # =====================================================
    # GENERAL SQL INTENTS
    # =====================================================

    sql_keywords = [
        "revenue",
        "sales",
        "customer",
        "customers",
        "marketing",
        "channel",
        "roas",
        "cpa",
        "campaign",
        "product",
        "subcategory",
        "city",
        "state",
        "acquisition",
        "rank",
        "ranking",
        "trend",
        "monthly",
        "yearly",
        "2023",
        "2024",
        "2025",
    ]

    # Only add SQL automatically for these general terms when no
    # specialized route already fully captures the question.
    specialized_routes = {
        "customer_segmentation_analysis",
        "return_risk_analysis",
        "device_conversion_analysis",
        "category_profitability_analysis",
        "discount_what_if",
        "monthly_anomaly_analysis",
    }

    if (
        not routes
        and any(
            keyword in q
            for keyword in sql_keywords
        )
    ):
        routes.append("sql")


    # =====================================================
    # FALLBACK
    # =====================================================

    if not routes:
        routes.append("sql")


    # Preserve order while removing duplicates.
    return list(
        dict.fromkeys(routes)
    )
