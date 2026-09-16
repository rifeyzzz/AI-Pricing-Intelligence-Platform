import pandas as pd

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List

from src.pricing_engine import (
    get_elasticity,
    forecast_demand,
    optimize_price
)

app = FastAPI(
    title="AI Demand & Pricing Engine",
    version="1.0.0",
    description="Demand forecasting and price recommendation API"
)


class ForecastRequest(BaseModel):
    features: Dict[str, float]


class PricingRequest(BaseModel):
    item_id: str
    base_price: float
    base_demand: float
    candidate_prices: List[float]


@app.get("/")
def root():
    return {
        "service": "AI Demand & Pricing Engine",
        "status": "running"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/elasticity/{item_id}")
def elasticity(item_id: str):

    result = get_elasticity(item_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Product elasticity not found"
        )

    return {
        "item_id": item_id,
        **result
    }


@app.post("/forecast")
def forecast(request: ForecastRequest):

    prediction = forecast_demand(
        request.features
    )

    return {
        "predicted_demand": prediction
    }


@app.post("/recommend-price")
def recommend_price(request: PricingRequest):

    info = get_elasticity(request.item_id)

    if info is None:
        raise HTTPException(
            status_code=404,
            detail="Product elasticity not found"
        )

    if info["classification"] == "Investigate":
        return {
            "item_id": request.item_id,
            "status": "MANUAL_REVIEW",
            "elasticity": info["elasticity"],
            "classification": info["classification"]
        }

    result = optimize_price(
        base_price=request.base_price,
        base_demand=request.base_demand,
        elasticity=info["elasticity"],
        candidate_prices=request.candidate_prices
    )

    return {
        "item_id": request.item_id,
        "status": "AUTO_RECOMMEND",
        "elasticity": info["elasticity"],
        "classification": info["classification"],
        **result
    }


# ============================================================
# BACKEND V2 — AUTOMATIC RECOMMENDATION ENDPOINT
# ============================================================

from src.pricing_engine import recommend_price_auto


@app.get("/recommend-auto/{item_id}")
def recommend_auto(
    item_id: str,
    max_change_pct: float = 0.10
):
    """
    Generate a complete pricing recommendation
    automatically from a product ID.
    """

    if max_change_pct <= 0 or max_change_pct > 0.25:
        raise HTTPException(
            status_code=400,
            detail=(
                "max_change_pct must be greater than 0 "
                "and no higher than 0.25."
            )
        )

    result = recommend_price_auto(
        item_id=item_id,
        max_change_pct=max_change_pct
    )

    if result["status"] == "NOT_FOUND":
        raise HTTPException(
            status_code=404,
            detail=result["reason"]
        )

    return result


# ============================================================
# BACKEND V3 — PROFIT-AWARE API
# ============================================================

from src.pricing_engine import recommend_profit_auto, build_pricing_explanation


class ProfitAutoRequest(BaseModel):
    item_id: str
    unit_cost: float
    max_change_pct: float = 0.10


@app.post("/recommend-profit-auto")
def recommend_profit(
    request: ProfitAutoRequest
):
    """
    Generate an automatic pricing recommendation
    using both revenue and profit optimization.
    """

    if request.unit_cost < 0:
        raise HTTPException(
            status_code=400,
            detail="unit_cost cannot be negative."
        )

    if (
        request.max_change_pct <= 0
        or request.max_change_pct > 0.25
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "max_change_pct must be greater than 0 "
                "and no higher than 0.25."
            )
        )

    result = recommend_profit_auto(
        item_id=request.item_id,
        unit_cost=request.unit_cost,
        max_change_pct=request.max_change_pct
    )

    if result["status"] == "NOT_FOUND":
        raise HTTPException(
            status_code=404,
            detail=result["reason"]
        )

    if result["status"] == "INVALID_INPUT":
        raise HTTPException(
            status_code=400,
            detail=result["reason"]
        )

    explanation = build_pricing_explanation(
        result
    )

    result["decision_summary"] = explanation[
        "decision_summary"
    ]

    result["governance_checks"] = explanation[
        "governance_checks"
    ]

    return result


# ============================================================
# BACKEND V5 — PORTFOLIO OPPORTUNITIES API
# ============================================================

import json

from src.pricing_engine import build_portfolio_opportunities


@app.get("/portfolio-opportunities")
def get_portfolio_opportunities(
    top_n: int = 20,
    max_change_pct: float = 0.10
):
    """
    Rank the strongest automated pricing opportunities
    across the eligible product portfolio.
    """

    if top_n < 1 or top_n > 100:
        raise HTTPException(
            status_code=400,
            detail="top_n must be between 1 and 100."
        )

    if (
        max_change_pct <= 0
        or max_change_pct > 0.25
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "max_change_pct must be greater than 0 "
                "and no higher than 0.25."
            )
        )


    portfolio = build_portfolio_opportunities(
        max_change_pct=max_change_pct,
        top_n=top_n
    )


    if portfolio.empty:

        return {
            "summary": {
                "opportunities": 0,
                "total_expected_revenue_gain": 0.0,
                "average_revenue_uplift_pct": 0.0
            },
            "opportunities": []
        }


    # Convert DataFrame safely into JSON-native values
    records = json.loads(
        portfolio.to_json(
            orient="records"
        )
    )


    summary = {
        "opportunities":
            int(len(portfolio)),

        "total_expected_revenue_gain":
            float(
                portfolio[
                    "expected_revenue_gain"
                ].sum()
            ),

        "average_revenue_uplift_pct":
            float(
                portfolio[
                    "expected_revenue_uplift_pct"
                ].mean()
            ),

        "largest_expected_revenue_gain":
            float(
                portfolio[
                    "expected_revenue_gain"
                ].max()
            )
    }


    return {
        "summary": summary,
        "opportunities": records
    }


# ============================================================
# BACKEND V6 — MODEL MONITORING / METADATA API
# ============================================================

from pathlib import Path


@app.get("/model-info")
def model_info():
    """
    Return model performance, features,
    baseline comparison and governance metadata.
    """

    metadata_path = (
        Path(__file__).resolve().parent.parent
        / "models"
        / "model_metadata.json"
    )

    if not metadata_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Model metadata file not found."
        )

    with open(
        metadata_path,
        "r",
        encoding="utf-8"
    ) as file:
        metadata = json.load(file)

    # Additional computed metrics
    model_mae = metadata["evaluation"]["mae"]
    baseline_mae = metadata["baseline"]["mae"]

    mae_improvement_pct = (
        (baseline_mae - model_mae)
        / baseline_mae
        * 100
    )

    metadata["computed_metrics"] = {
        "mae_improvement_vs_baseline_pct":
            mae_improvement_pct
    }

    return metadata


# ============================================================
# BACKEND V6 — FEATURE IMPORTANCE API
# ============================================================

@app.get("/feature-importance")
def feature_importance():
    """
    Return permutation feature importance calculated
    on held-out demand forecasting observations.
    """

    importance_path = (
        Path(__file__).resolve().parent.parent
        / "models"
        / "feature_importance.csv"
    )

    if not importance_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Feature importance file not found."
        )

    importance_df = pd.read_csv(
        importance_path
    )

    return {
        "method": "Permutation Importance",
        "scoring": "Negative Mean Absolute Error",
        "features": json.loads(
            importance_df.to_json(
                orient="records"
            )
        )
    }
