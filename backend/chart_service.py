from decimal import Decimal


def is_number(value):
    return isinstance(
        value,
        (int, float, Decimal)
    ) and not isinstance(value, bool)


def get_columns(data):
    if not isinstance(data, list) or not data:
        return [], []

    row = data[0]

    text_columns = []
    numeric_columns = []

    for key, value in row.items():
        if isinstance(value, str):
            text_columns.append(key)

        elif is_number(value):
            numeric_columns.append(key)

    return text_columns, numeric_columns


def detect_time_column(columns):
    preferred = [
        "month",
        "date",
        "year",
        "order_date",
        "month_start",
        "order_month"
    ]

    for column in preferred:
        if column in columns:
            return column

    return None


def recommend_sql_chart(
    data,
    question=""
):
    if not isinstance(data, list) or not data:
        return None

    text_columns, numeric_columns = get_columns(data)

    if not numeric_columns:
        return None

    all_columns = text_columns + numeric_columns

    time_column = detect_time_column(all_columns)

    q = question.lower()

    # ----------------------------------
    # TIME SERIES → LINE
    # ----------------------------------

    if time_column:
        preferred_metrics = [
            "net_revenue",
            "total_net_revenue",
            "gross_profit",
            "total_gross_profit",
            "revenue",
            "refunds",
            "orders",
            "conversions"
        ]

        y_columns = [
            col
            for col in preferred_metrics
            if col in numeric_columns
        ]

        if not y_columns:
            y_columns = [
                col
                for col in numeric_columns
                if col != time_column
            ][:2]

        if not y_columns:
            return None

        return {
            "type": "line",
            "title": "Trend Analysis",
            "x": time_column,
            "series": [
                {
                    "key": col,
                    "label": col.replace("_", " ").title()
                }
                for col in y_columns[:3]
            ],
            "format": "currency"
        }

    # ----------------------------------
    # RANKING → HORIZONTAL BAR
    # ----------------------------------

    ranking_words = [
        "rank",
        "highest",
        "lowest",
        "top",
        "best",
        "worst"
    ]

    if (
        text_columns
        and any(word in q for word in ranking_words)
    ):
        preferred = [
            "gross_profit",
            "total_gross_profit",
            "net_revenue",
            "total_net_revenue",
            "roas",
            "cpa",
            "conversion_rate_pct",
            "return_rate_pct"
        ]

        y = next(
            (
                col
                for col in preferred
                if col in numeric_columns
            ),
            numeric_columns[0]
        )

        return {
            "type": "horizontal_bar",
            "title": y.replace("_", " ").title(),
            "x": text_columns[0],
            "y": y,
            "y_label": y.replace("_", " ").title()
        }

    # ----------------------------------
    # MULTI-METRIC COMPARISON
    # ----------------------------------

    if text_columns and len(numeric_columns) >= 2:
        percentage_metrics = [
            col
            for col in numeric_columns
            if (
                "pct" in col.lower()
                or "rate" in col.lower()
                or "margin" in col.lower()
            )
        ]

        comparable_metrics = [
            col
            for col in numeric_columns
            if col not in percentage_metrics
        ]

        if len(comparable_metrics) >= 2:
            return {
                "type": "grouped_bar",
                "title": "Business Metric Comparison",
                "x": text_columns[0],
                "series": [
                    {
                        "key": comparable_metrics[0],
                        "label": comparable_metrics[0]
                        .replace("_", " ")
                        .title()
                    },
                    {
                        "key": comparable_metrics[1],
                        "label": comparable_metrics[1]
                        .replace("_", " ")
                        .title()
                    }
                ]
            }

    # ----------------------------------
    # DEFAULT BAR
    # ----------------------------------

    if text_columns:
        return {
            "type": "bar",
            "title": "Query Result",
            "x": text_columns[0],
            "y": numeric_columns[0],
            "y_label": numeric_columns[0]
            .replace("_", " ")
            .title()
        }

    return None


def recommend_single_route_charts(
    route,
    data,
    question=""
):
    charts = []

    # ----------------------------------
    # DEVICE FUNNEL
    # ----------------------------------

    if route == "device_conversion_analysis":
        charts.append({
            "type": "grouped_bar",
            "title": "Device Funnel Performance",
            "x": "device",
            "series": [
                {
                    "key": "conversion_rate_pct",
                    "label": "Conversion Rate"
                },
                {
                    "key": "add_to_cart_rate_pct",
                    "label": "Add-to-Cart Rate"
                },
                {
                    "key": "cart_to_conversion_pct",
                    "label": "Cart-to-Conversion"
                }
            ],
            "format": "percent"
        })

        return charts

    # ----------------------------------
    # CATEGORY PROFITABILITY
    # ----------------------------------

    if route == "category_profitability_analysis":
        charts.append({
            "type": "bar",
            "title": "Gross Profit by Category",
            "x": "category",
            "y": "gross_profit",
            "y_label": "Gross Profit",
            "format": "currency"
        })

        charts.append({
            "type": "grouped_bar",
            "title": "Return vs Refund Pressure",
            "x": "category",
            "series": [
                {
                    "key": "return_rate_pct",
                    "label": "Return Rate"
                },
                {
                    "key": "refund_rate_pct",
                    "label": "Refund Rate"
                }
            ],
            "format": "percent"
        })

        return charts

    # ----------------------------------
    # DISCOUNT WHAT-IF
    # ----------------------------------

    if route == "discount_what_if":
        charts.append({
            "type": "kpi",
            "title": "Discount Scenario",
            "metrics": [
                "simulated_gross_profit",
                "simulated_margin_pct",
                "profit_change_pct",
                "margin_change_pp"
            ]
        })

        return charts

    # ----------------------------------
    # ANOMALIES
    # ----------------------------------

    if route == "monthly_anomaly_analysis":
        charts.append({
            "type": "grouped_bar",
            "title": "Detected Monthly Anomalies",
            "x": "month",
            "series": [
                {
                    "key": "net_revenue_growth_pct",
                    "label": "Revenue Growth"
                },
                {
                    "key": "gross_profit_growth_pct",
                    "label": "Profit Growth"
                },
                {
                    "key": "refunds_growth_pct",
                    "label": "Refund Growth"
                }
            ],
            "format": "percent"
        })

        return charts

    # ----------------------------------
    # SQL
    # ----------------------------------

    if route == "sql":
        chart = recommend_sql_chart(
            data,
            question
        )

        if chart:
            charts.append(chart)

        return charts

    return charts


def recommend_charts(
    route,
    data,
    question=""
):
    # ==================================
    # MULTI-ANALYSIS
    # ==================================

    if route == "multi_analysis":
        charts = []

        if not isinstance(data, dict):
            return charts

        analyses = data.get(
            "analyses",
            []
        )

        for analysis in analyses:
            subroute = analysis.get(
                "route"
            )

            subquestion = analysis.get(
                "question",
                question
            )

            subdata = analysis.get(
                "data"
            )

            subcharts = recommend_single_route_charts(
                subroute,
                subdata,
                subquestion
            )

            for chart in subcharts[:1]:
                chart["source_route"] = subroute

                charts.append({
                    **chart,
                    "data": subdata
                })

        return charts[:4]

    # ==================================
    # SINGLE ANALYSIS
    # ==================================

    charts = recommend_single_route_charts(
        route,
        data,
        question
    )

    return [
        {
            **chart,
            "data": data
        }
        for chart in charts
    ]