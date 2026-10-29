from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.query_runner import run_query
from backend.ai_service import ask_decisioniq
from backend.analytics import device_conversion_analysis
from backend.chart_service import recommend_charts
from backend.customer_segmentation import (
    run_customer_segmentation,
    get_segment_customers,
)

from backend.return_risk_model import run_return_risk_model

app = FastAPI(
    title="DecisionIQ API",
    version="1.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    sql: str


class AskRequest(BaseModel):
    question: str


@app.get("/")
def root():

    return {
        "message": "DecisionIQ backend is running"
    }


@app.get("/health")
def health():

    return {
        "status": "ok"
    }


@app.post("/query")
def query_database(
    request: QueryRequest
):

    try:

        data = run_query(
            request.sql
        )

        return {
            "success": True,
            "rows": len(data),
            "data": data
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


@app.get("/analytics/device-conversion")
def device_conversion():

    try:

        data = device_conversion_analysis()

        return {
            "success": True,
            "analysis": "device_conversion",
            "data": data
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


@app.post("/ask")
def ask_ai(
    request: AskRequest
):

    try:

        result = ask_decisioniq(
            request.question
        )

        charts = recommend_charts(
            route=result["route"],
            data=result["data"],
            question=request.question
        )

        return {
            "success": True,
            **result,
            "charts": charts
        }

    except Exception as e:

        error_text = str(e)

        # -----------------------------------
        # OPENAI RATE LIMIT
        # -----------------------------------

        if (
            "rate_limit_exceeded" in error_text.lower()
            or "error code: 429" in error_text.lower()
            or "tokens per min" in error_text.lower()
        ):

            return {
                "success": False,
                "error_type": "rate_limit",
                "error": (
                    "DecisionIQ has temporarily reached its AI usage limit. "
                    "The analytics engine is working correctly, but the AI "
                    "model cannot process another request right now."
                )
            }

        # -----------------------------------
        # SQL GENERATION / REPAIR FAILURE
        # -----------------------------------

        if (
            "could not execute sql" in error_text.lower()
            or "mysql" in error_text.lower()
            or "sqlalchemy" in error_text.lower()
        ):

            return {
                "success": False,
                "error_type": "analysis_error",
                "error": (
                    "DecisionIQ could not complete this analysis because "
                    "the generated database query failed. Please try "
                    "rephrasing the question or simplifying the request."
                )
            }

        # -----------------------------------
        # FALLBACK ERROR
        # -----------------------------------

        return {
            "success": False,
            "error_type": "unknown",
            "error": (
                "DecisionIQ could not complete the analysis. "
                "Please try again."
            )
        }




@app.get("/analytics/customer-segmentation")
def customer_segmentation():
    try:
        result = run_customer_segmentation()

        return {
            "success": True,
            "best_k": result["best_k"],
            "silhouette_scores": result["silhouette_scores"],
            "cluster_profile": result[
                "cluster_profile"
            ].to_dict(
                orient="records"
            ),
            "segment_value": result[
                "segment_value"
            ].to_dict(
                orient="records"
            ),
        }

    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
        }


@app.get("/analytics/customer-segmentation/customers")
def customer_segment_list(
    segment: str,
    limit: int = 100,
):
    try:
        customers = get_segment_customers(
            segment,
            limit,
        )

        return {
            "success": True,
            "segment": segment,
            "count": len(customers),
            "customers": customers.to_dict(
                orient="records"
            ),
        }

    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
        }






@app.get("/analytics/return-risk")
def return_risk():
    try:
        result = run_return_risk_model()

        return {
            "success": True,
            "dataset_summary": result["dataset_summary"],
            "model_metrics": result["model_metrics"],
            "best_model_name": result["best_model_name"],
            "best_metrics": result["best_metrics"],
            "feature_importance": result[
                "feature_importance"
            ].to_dict(orient="records"),
            "high_risk_items": result[
                "high_risk_items"
            ].to_dict(orient="records"),
        }

    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
        }



    