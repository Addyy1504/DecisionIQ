import os
import json
import re

from openai import OpenAI

from backend.query_runner import run_query
from backend.analytics import device_conversion_analysis
from backend.profitability_analysis import (
    category_profitability_analysis,
)
from backend.discount_analysis import (
    simulate_discount_margin,
)
from backend.anomaly_analysis import (
    monthly_anomaly_analysis,
)
from backend.customer_segmentation import (
    run_customer_segmentation,
    get_segment_customers,
)
from backend.return_risk_model import (
    run_return_risk_model,
)

from backend.router import (
    choose_analysis_routes,
    extract_discount_percentage,
)


MODEL = "gpt-6-luna"
MAX_LLM_ROWS = 40

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


# =========================================================
# CONTEXT
# =========================================================

SCHEMA_CONTEXT = """
DecisionIQ may generate SQL ONLY against these MySQL 8 analytical views:

1. vw_order_item_metrics
order_item_id, order_id, customer_id, order_date, order_status,
product_id, product_name, category, subcategory, quantity,
unit_price, discount_pct, gross_sales, discounted_sales,
is_returned, refund_amount, net_revenue, cogs, gross_profit

2. vw_customer_metrics
customer_id, customer_name, age, gender, city, state,
signup_date, acquisition_channel, total_orders, net_revenue,
cogs, gross_profit, total_items, returned_items,
return_rate_pct, avg_order_value

3. vw_marketing_metrics
channel, campaigns, impressions, clicks, conversions,
ad_spend, attributed_revenue, ctr_pct,
click_conversion_rate_pct, cpa, roas

4. vw_website_funnel
device, traffic_source, total_sessions, add_to_cart_sessions,
converted_sessions, add_to_cart_rate_pct, conversion_rate_pct,
cart_to_conversion_pct, avg_pages_viewed,
avg_session_duration_seconds
"""


SQL_RULES = """
SQL RULES:

- Valid MySQL 8 only.
- SELECT only.
- Use only approved analytical views.
- Never INSERT, UPDATE, DELETE, DROP, ALTER, CREATE,
  REPLACE or TRUNCATE.
- Prefer aggregated business-level results.
- Avoid SELECT *.
- Use LIMIT for detailed row output.
- Use NULLIF for risky division.
- Use CTEs/window functions only when useful.
- Never invent columns.
- Product size does not exist.
- Return reasons are unavailable through approved views.
- acquisition_channel is customer acquisition source,
  not an order-level sales channel.
- Do not query raw database tables.

MYSQL NUMERIC SAFETY:
RANK(), DENSE_RANK() and ROW_NUMBER() may behave as unsigned.
Before subtracting ranking values, CAST both AS SIGNED.

Example:
ABS(
    CAST(profit_rank AS SIGNED)
    - CAST(margin_rank AS SIGNED)
)

Return only SQL.
"""


BUSINESS_CONTEXT = """
DecisionIQ business definitions:

- Gross Sales = quantity × unit_price for non-cancelled orders.
- Discounted Sales = quantity × unit_price × (1 - discount_pct).
- Net Revenue = Discounted Sales - Refunds.
- COGS = retained merchandise cost.
- Gross Profit = Net Revenue - COGS.
- Gross Margin % = Gross Profit / Net Revenue × 100.
- AOV = Discounted Sales / non-cancelled orders.
- Website Conversion = converted sessions / sessions.
- Return Rate = returned sold-item rows / sold-item rows.
- ROAS = attributed campaign revenue / ad spend.
- CPA = ad spend / campaign conversions. Do not call CPA CAC.

Important analytical caveats:

- Dataset is synthetic.
- Correlation does not establish causality.
- Do not claim discounts caused higher demand.
- Do not claim mobile checkout is confirmed broken.
- Mobile/Desktop add-to-cart rates are similar; the observed
  mobile gap appears later in the funnel.
- Return reasons must not be invented.
- Marketing ROAS is modeled/synthetic, not an industry benchmark.
- Later-period growth is partly affected by customer signup timing.
"""


DATA_SCIENCE_CONTEXT = """
DecisionIQ has two data-science modules.

CUSTOMER SEGMENTATION:
- Uses RFM: Recency, Frequency and Monetary value.
- K-Means evaluates K=2 through K=6 using silhouette score.
- Current best K is 3.
- Business labels:
  At Risk
  Regular Customers
  High-Value Loyal
- These labels are business interpretations of clusters,
  not ground-truth customer classes.
- Customers with no qualifying non-cancelled purchase are not
  represented in the RFM clustering.

RETURN RISK:
- Experimental item-level return-risk classifier.
- Uses transaction/category features plus historical behavior.
- Temporal holdout is used rather than random train/test splitting.
- Current best model is Logistic Regression by ROC-AUC.
- Performance is moderate (ROC-AUC around 0.60).
- Predicted probabilities are prioritization signals,
  not certainties or production decision rules.
- Feature coefficients/importance indicate model association,
  not causal drivers.
- Accuracy alone is misleading because returns are imbalanced.
"""


REPORTING_RULES = """
REPORTING RULES:

- All money is INR.
- Use ₹M and ₹B for large monetary values.
- Never convert into lakh/crore.
- Preserve magnitude.
- Separate observation, interpretation, hypothesis
  and recommendation.
- Be concise and business-oriented.
- Clearly state unavailable evidence.
"""


VISUALIZATION_RULES = """
Do not generate Mermaid, ASCII charts, chart code, or chart markup.
DecisionIQ's frontend handles visualization separately.
"""


FULL_SQL_CONTEXT = (
    SCHEMA_CONTEXT
    + "\n"
    + SQL_RULES
    + "\n"
    + BUSINESS_CONTEXT
    + "\n"
    + REPORTING_RULES
)


ANALYST_CONTEXT = (
    BUSINESS_CONTEXT
    + "\n"
    + DATA_SCIENCE_CONTEXT
    + "\n"
    + REPORTING_RULES
    + "\n"
    + VISUALIZATION_RULES
)


# =========================================================
# GENERAL HELPERS
# =========================================================

def call_model(
    prompt: str,
    instructions: str = None,
    max_output_tokens: int = 1400,
):
    kwargs = {
        "model": MODEL,
        "input": prompt,
        "max_output_tokens": max_output_tokens,
    }

    if instructions:
        kwargs["instructions"] = instructions

    response = client.responses.create(
        **kwargs
    )

    return response.output_text.strip()


def clean_sql_output(sql: str):
    sql = sql.strip()

    if sql.startswith("```"):
        sql = sql.replace("```sql", "")
        sql = sql.replace("```SQL", "")
        sql = sql.replace("```", "")
        sql = sql.strip()

    return sql


def clean_json_output(text: str):
    text = text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```JSON", "")
        text = text.replace("```", "")
        text = text.strip()

    return text


def make_json_safe(value):
    """
    Convert pandas/numpy/date-like values into JSON-safe Python values.
    """

    if value is None:
        return None

    if isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    if isinstance(value, dict):
        return {
            str(k): make_json_safe(v)
            for k, v in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            make_json_safe(v)
            for v in value
        ]

    if hasattr(value, "item"):
        try:
            return make_json_safe(
                value.item()
            )
        except Exception:
            pass

    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass

    return str(value)


def dataframe_records(df):
    return make_json_safe(
        df.to_dict(
            orient="records"
        )
    )


def compact_data_for_llm(
    data,
    max_rows=MAX_LLM_ROWS,
):
    data = make_json_safe(data)

    if isinstance(data, list):
        if len(data) > max_rows:
            return {
                "rows_returned": len(data),
                "rows_included": max_rows,
                "data": data[:max_rows],
            }

        return data

    if isinstance(data, dict):
        compact = {}

        for key, value in data.items():
            if (
                isinstance(value, list)
                and len(value) > max_rows
            ):
                compact[key] = {
                    "rows_returned": len(value),
                    "rows_included": max_rows,
                    "data": value[:max_rows],
                }
            else:
                compact[key] = value

        return compact

    return data


def looks_like_compound_question(
    question: str,
):
    q = question.lower()

    signals = [
        " and ",
        " also ",
        " as well as ",
        " along with ",
        " additionally ",
        " plus ",
        " while ",
        " but also ",
        "whether",
    ]

    return (
        any(signal in q for signal in signals)
        or question.count("?") > 1
    )


def focused_question_for_route(
    route: str,
    question: str,
):
    """
    Avoid an extra planner call when deterministic routing already
    identifies multiple routes.
    """

    prefixes = {
        "sql":
            "Using historical SQL evidence only, answer the parts of this "
            "question not covered by specialized analytics: ",
        "device_conversion_analysis":
            "Answer only the device/funnel portion of: ",
        "category_profitability_analysis":
            "Answer only the category profitability portion of: ",
        "discount_what_if":
            "Answer only the explicit discount scenario portion of: ",
        "monthly_anomaly_analysis":
            "Answer only the anomaly/time-movement portion of: ",
        "customer_segmentation_analysis":
            "Answer only the customer segmentation/RFM portion of: ",
        "return_risk_analysis":
            "Answer only the predictive return-risk/model portion of: ",
    }

    return (
        prefixes.get(route, "")
        + question
    )


# =========================================================
# SQL
# =========================================================

def generate_sql(question: str):
    sql = call_model(
        prompt=question,
        instructions=FULL_SQL_CONTEXT,
        max_output_tokens=1200,
    )

    return clean_sql_output(sql)


def repair_sql(
    question: str,
    broken_sql: str,
    error: str,
):
    prompt = f"""
Business question:
{question}

Broken SQL:
{broken_sql}

MySQL error:
{error}

Repair the SQL while preserving the analytical intent.

Important:
- MySQL 8.
- SELECT only.
- Approved views only.
- Do not repeat the same failing query.
- If ranking arithmetic is involved, cast ranking values AS SIGNED.
- Check GROUP BY grain, aliases, window functions,
  unavailable columns and division by zero.

Return only repaired SQL.
"""

    sql = call_model(
        prompt=prompt,
        instructions=FULL_SQL_CONTEXT,
        max_output_tokens=1200,
    )

    return clean_sql_output(sql)


def execute_sql_question(question: str):
    sql = generate_sql(question)

    try:
        data = run_query(sql)

    except Exception as first_error:
        repaired_sql = repair_sql(
            question=question,
            broken_sql=sql,
            error=str(first_error),
        )

        try:
            data = run_query(
                repaired_sql
            )
            sql = repaired_sql

        except Exception as second_error:
            raise RuntimeError(
                "DecisionIQ could not execute SQL after one "
                "automatic repair attempt.\n\n"
                f"Original error: {first_error}\n\n"
                f"Repair error: {second_error}"
            )

    return {
        "route": "sql",
        "question": question,
        "sql": sql,
        "data": make_json_safe(data),
    }


# =========================================================
# DATA SCIENCE EXECUTION
# =========================================================

def execute_customer_segmentation(
    question: str,
):
    result = run_customer_segmentation()

    cluster_profile = dataframe_records(
        result["cluster_profile"]
    )

    segment_value = dataframe_records(
        result["segment_value"]
    )

    q = question.lower()

    requested_segment = None

    segment_phrases = {
        "high-value loyal":
            "High-Value Loyal",
        "high value loyal":
            "High-Value Loyal",
        "high-value":
            "High-Value Loyal",
        "high value":
            "High-Value Loyal",
        "at risk":
            "At Risk",
        "at-risk":
            "At Risk",
        "regular":
            "Regular Customers",
    }

    for phrase, segment in (
        segment_phrases.items()
    ):
        if phrase in q:
            requested_segment = segment
            break

    wants_customer_list = any(
        phrase in q
        for phrase in [
            "show",
            "list",
            "which customer",
            "which customers",
            "customer ids",
            "target",
            "targeting",
        ]
    )

    customers = None

    if (
        requested_segment
        and wants_customer_list
    ):
        customers = dataframe_records(
            get_segment_customers(
                requested_segment,
                limit=25,
            )
        )

    data = {
        "best_k": int(
            result["best_k"]
        ),
        "silhouette_scores":
            make_json_safe(
                result[
                    "silhouette_scores"
                ]
            ),
        "cluster_profile":
            cluster_profile,
        "segment_value":
            segment_value,
        "requested_segment":
            requested_segment,
        "customers":
            customers,
    }

    return {
        "route":
            "customer_segmentation_analysis",
        "question": question,
        "sql": None,
        "data": data,
    }


def execute_return_risk(
    question: str,
):
    result = run_return_risk_model()

    q = question.lower()

    data = {
        "dataset_summary":
            make_json_safe(
                result[
                    "dataset_summary"
                ]
            ),
        "best_model_name":
            result[
                "best_model_name"
            ],
        "best_metrics":
            make_json_safe(
                result[
                    "best_metrics"
                ]
            ),
        "model_metrics":
            make_json_safe(
                result[
                    "model_metrics"
                ]
            ),
    }

    wants_features = any(
        phrase in q
        for phrase in [
            "feature",
            "driver",
            "drivers",
            "driving",
            "factor",
            "factors",
            "importance",
            "why",
        ]
    )

    wants_high_risk = any(
        phrase in q
        for phrase in [
            "high risk",
            "high-risk",
            "highest risk",
            "risky",
            "which item",
            "which items",
            "which order",
            "which orders",
            "show",
            "list",
        ]
    )

    if wants_features:
        data[
            "feature_importance"
        ] = dataframe_records(
            result[
                "feature_importance"
            ].head(10)
        )

    if wants_high_risk:
        data[
            "high_risk_items"
        ] = dataframe_records(
            result[
                "high_risk_items"
            ].head(20)
        )

    return {
        "route":
            "return_risk_analysis",
        "question": question,
        "sql": None,
        "data": data,
    }


# =========================================================
# PLANNER
# =========================================================

def build_analysis_plan(
    question: str,
):
    deterministic_routes = (
        choose_analysis_routes(
            question
        )
    )

    # Token optimization:
    # if routing already found multiple distinct intents,
    # do not spend another LLM call on planning.
    if len(deterministic_routes) > 1:
        return [
            {
                "route": route,
                "question":
                    focused_question_for_route(
                        route,
                        question,
                    ),
            }
            for route
            in deterministic_routes[:4]
        ]

    allowed_routes = {
        "sql",
        "device_conversion_analysis",
        "category_profitability_analysis",
        "discount_what_if",
        "monthly_anomaly_analysis",
        "customer_segmentation_analysis",
        "return_risk_analysis",
    }

    prompt = f"""
User question:
{question}

Deterministic route:
{json.dumps(deterministic_routes)}

Available routes:
- sql
- device_conversion_analysis
- category_profitability_analysis
- discount_what_if
- monthly_anomaly_analysis
- customer_segmentation_analysis
- return_risk_analysis

Break the question into the minimum number of independent
analytical tasks.

Rules:
- Usually 1-3 tasks; maximum 4.
- discount_what_if requires an explicit numeric percentage.
- Historical discount-vs-demand questions use sql.
- Customer RFM/segments use customer_segmentation_analysis.
- Return probabilities/model metrics/features/high-risk items
  use return_risk_analysis.
- Do not invent routes.
- Do not claim causality.

Return only JSON:
{{
  "tasks": [
    {{
      "route": "sql",
      "question": "focused analytical subquestion"
    }}
  ]
}}
"""

    raw = clean_json_output(
        call_model(
            prompt=prompt,
            max_output_tokens=500,
        )
    )

    try:
        plan = json.loads(raw)
        tasks = plan.get(
            "tasks",
            [],
        )

        cleaned = []
        seen = set()

        for task in tasks[:4]:
            route = task.get(
                "route"
            )
            subquestion = task.get(
                "question"
            )

            if (
                route not in allowed_routes
                or not subquestion
            ):
                continue

            key = (
                route,
                subquestion
                .strip()
                .lower(),
            )

            if key in seen:
                continue

            seen.add(key)

            cleaned.append({
                "route": route,
                "question":
                    subquestion.strip(),
            })

        if cleaned:
            return cleaned

    except Exception:
        pass

    return [
        {
            "route": route,
            "question": question,
        }
        for route
        in deterministic_routes
    ]


# =========================================================
# ROUTE EXECUTION
# =========================================================

def execute_analysis_task(
    route: str,
    question: str,
    original_question: str,
):
    if route == "sql":
        return execute_sql_question(
            question
        )

    if (
        route
        == "device_conversion_analysis"
    ):
        return {
            "route": route,
            "question": question,
            "sql": None,
            "data": make_json_safe(
                device_conversion_analysis()
            ),
        }

    if (
        route
        == "category_profitability_analysis"
    ):
        return {
            "route": route,
            "question": question,
            "sql": None,
            "data": make_json_safe(
                category_profitability_analysis()
            ),
        }

    if route == "discount_what_if":
        discount_pct = (
            extract_discount_percentage(
                question
            )
        )

        if discount_pct is None:
            discount_pct = (
                extract_discount_percentage(
                    original_question
                )
            )

        if discount_pct is None:
            return execute_sql_question(
                question
            )

        return {
            "route": route,
            "question": question,
            "sql": None,
            "data": make_json_safe(
                simulate_discount_margin(
                    discount_pct
                )
            ),
        }

    if (
        route
        == "monthly_anomaly_analysis"
    ):
        raw_data = (
            monthly_anomaly_analysis()
        )

        anomalies = [
            row
            for row in raw_data
            if row["is_anomaly"]
        ]

        return {
            "route": route,
            "question": question,
            "sql": None,
            "data": make_json_safe(
                anomalies
            ),
        }

    if (
        route
        == "customer_segmentation_analysis"
    ):
        return execute_customer_segmentation(
            question
        )

    if (
        route
        == "return_risk_analysis"
    ):
        return execute_return_risk(
            question
        )

    raise ValueError(
        f"Unknown analysis route: {route}"
    )


# =========================================================
# EXPLANATIONS
# =========================================================

def explain_sql_result(
    question: str,
    sql: str,
    data,
):
    prompt = f"""
Question:
{question}

SQL result:
{json.dumps(
    compact_data_for_llm(data),
    default=str
)}

Explain the result directly.

Requirements:
- Mention the key numbers.
- Distinguish amounts from percentages.
- Do not invent causes.
- State limitations when relevant.
- Suggest one practical action only when useful.
"""

    return call_model(
        prompt=prompt,
        instructions=ANALYST_CONTEXT,
        max_output_tokens=1000,
    )


def explain_specialized_result(
    route: str,
    question: str,
    data,
):
    route_rules = {
        "device_conversion_analysis":
            """
Focus on conversion, add-to-cart and cart-to-conversion.
Do not claim checkout UX is definitely the cause.
""",

        "category_profitability_analysis":
            """
Focus on net revenue, gross profit, margin,
return rate and refund rate.
Do not invent return reasons.
""",

        "discount_what_if":
            """
This is a scenario, not a forecast.
Volume, mix, COGS and refunds are held constant.
Mention profit/margin impact and whether profit turns negative.
""",

        "monthly_anomaly_analysis":
            """
Explain unusual months, triggering metrics, direction
and magnitude. Anomaly does not establish cause.
""",

        "customer_segmentation_analysis":
            """
Explain the RFM/K-Means customer segments.
Use the business segment labels but clarify that they are
interpretations of clusters.
If a customer list is present, summarize it rather than
printing every row.
""",

        "return_risk_analysis":
            """
Explain the experimental return-risk model honestly.
ROC-AUC is around 0.60, so performance is moderate.
Do not call it production-grade.
Predicted risk is a prioritization signal, not certainty.
Feature importance/coefficient is association, not causality.
For imbalanced returns, do not rely on accuracy alone.
""",
    }

    prompt = f"""
Question:
{question}

Analysis route:
{route}

Analysis data:
{json.dumps(
    compact_data_for_llm(data),
    default=str
)}

Route-specific instructions:
{route_rules.get(route, "")}

Answer directly and concisely.
"""

    return call_model(
        prompt=prompt,
        instructions=ANALYST_CONTEXT,
        max_output_tokens=1000,
    )


# =========================================================
# SYNTHESIS
# =========================================================

def synthesize_analyses(
    original_question: str,
    analyses: list,
):
    compact_analyses = [
        {
            "route":
                analysis["route"],
            "subquestion":
                analysis["question"],
            # Intentionally do not resend SQL text.
            "data":
                compact_data_for_llm(
                    analysis.get(
                        "data"
                    )
                ),
        }
        for analysis in analyses
    ]

    prompt = f"""
Original question:
{original_question}

Independent analyses:
{json.dumps(
    compact_analyses,
    default=str
)}

Create one coherent answer.

Rules:
- Answer every part.
- Keep evidence from different routes logically separate.
- Connect findings only when evidence supports the connection.
- Never turn association into causality.
- Do not mention internal routing.
- Use Markdown when helpful.
"""

    return call_model(
        prompt=prompt,
        instructions=ANALYST_CONTEXT,
        max_output_tokens=1300,
    )


# =========================================================
# MAIN AGENT
# =========================================================

def ask_decisioniq(question: str):
    deterministic_routes = (
        choose_analysis_routes(
            question
        )
    )

    is_multi = (
        len(deterministic_routes) > 1
        or looks_like_compound_question(
            question
        )
    )

    # -----------------------------------------------------
    # MULTI-INTENT
    # -----------------------------------------------------

    if is_multi:
        plan = build_analysis_plan(
            question
        )

        analyses = [
            execute_analysis_task(
                route=task["route"],
                question=task["question"],
                original_question=question,
            )
            for task in plan
        ]

        # If planning resolves to one task, avoid an
        # unnecessary synthesis call.
        if len(analyses) == 1:
            analysis = analyses[0]

            if analysis["route"] == "sql":
                answer = explain_sql_result(
                    question=question,
                    sql=analysis["sql"],
                    data=analysis["data"],
                )
            else:
                answer = explain_specialized_result(
                    route=analysis["route"],
                    question=question,
                    data=analysis["data"],
                )

            return {
                "question": question,
                "route":
                    analysis["route"],
                "sql":
                    analysis.get("sql"),
                "data":
                    analysis["data"],
                "answer":
                    answer,
            }

        answer = synthesize_analyses(
            original_question=question,
            analyses=analyses,
        )

        sql_queries = [
            (
                f"-- {analysis['question']}\n"
                f"{analysis['sql']}"
            )
            for analysis in analyses
            if analysis.get("sql")
        ]

        combined_sql = (
            "\n\n".join(
                sql_queries
            )
            if sql_queries
            else None
        )

        return {
            "question": question,
            "route": "multi_analysis",
            "analysis_routes": [
                analysis["route"]
                for analysis in analyses
            ],
            "sql": combined_sql,
            "data": {
                "analyses": [
                    {
                        "route":
                            analysis["route"],
                        "question":
                            analysis["question"],
                        "data":
                            analysis["data"],
                    }
                    for analysis
                    in analyses
                ]
            },
            "answer": answer,
        }

    # -----------------------------------------------------
    # SINGLE ROUTE
    # -----------------------------------------------------

    route = deterministic_routes[0]

    analysis = execute_analysis_task(
        route=route,
        question=question,
        original_question=question,
    )

    if route == "sql":
        answer = explain_sql_result(
            question=question,
            sql=analysis["sql"],
            data=analysis["data"],
        )
    else:
        answer = explain_specialized_result(
            route=route,
            question=question,
            data=analysis["data"],
        )

    return {
        "question": question,
        "route": route,
        "sql": analysis.get("sql"),
        "data": analysis["data"],
        "answer": answer,
    }
