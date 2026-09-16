
import json
import joblib
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "models" / "demand_forecaster.joblib"
FEATURES_PATH = BASE_DIR / "models" / "features.json"
ELASTICITY_PATH = BASE_DIR / "data" / "master_product_elasticities.csv"

model = joblib.load(MODEL_PATH)

with open(FEATURES_PATH, "r") as f:
    features = json.load(f)

elasticities = pd.read_csv(ELASTICITY_PATH)


def get_elasticity(item_id):
    row = elasticities[elasticities["item_id"] == item_id]

    if row.empty:
        return None

    return {
        "elasticity": float(row["elasticity"].iloc[0]),
        "classification": str(row["classification"].iloc[0])
    }


def forecast_demand(feature_values):
    X = pd.DataFrame([feature_values])[features]
    prediction = model.predict(X)[0]

    return max(float(prediction), 0.0)


def optimize_price(base_price, base_demand, elasticity, candidate_prices):
    scenarios = []

    for price in candidate_prices:
        demand = base_demand * (price / base_price) ** elasticity
        demand = max(float(demand), 0.0)
        revenue = float(price * demand)

        scenarios.append({
            "price": float(price),
            "forecast_demand": demand,
            "expected_revenue": revenue
        })

    best = max(scenarios, key=lambda x: x["expected_revenue"])

    return {
        "recommended_price": best["price"],
        "forecast_demand": best["forecast_demand"],
        "expected_revenue": best["expected_revenue"],
        "scenarios": scenarios
    }


# ============================================================
# BACKEND V2 — AUTOMATIC PRICING RECOMMENDATION
# ============================================================

FEATURE_STORE_PATH = (
    BASE_DIR
    / "data"
    / "latest_product_features.csv"
)

latest_product_features = pd.read_csv(
    FEATURE_STORE_PATH
)


def get_latest_product_features(item_id):
    """
    Retrieve the most recent ML feature snapshot
    available for a product.
    """

    row = latest_product_features[
        latest_product_features["item_id"] == item_id
    ]

    if row.empty:
        return None

    row = row.iloc[0]

    return {
        "item_id": item_id,
        "date": str(row["date"]),
        "sell_price": float(row["sell_price"]),
        "day_of_week": float(row["day_of_week"]),
        "month": float(row["month"]),
        "year": float(row["year"]),
        "demand_lag_1": float(row["demand_lag_1"]),
        "demand_lag_7": float(row["demand_lag_7"]),
        "rolling_mean_7": float(row["rolling_mean_7"]),
        "rolling_mean_28": float(row["rolling_mean_28"])
    }


def generate_candidate_prices(
    base_price,
    max_change_pct=0.10
):
    """
    Generate five cent-level candidate prices while
    strictly respecting the configured price-change limit.
    """

    import math

    minimum_price = (
        math.ceil(
            base_price * (1 - max_change_pct) * 100
        )
        / 100
    )

    maximum_price = (
        math.floor(
            base_price * (1 + max_change_pct) * 100
        )
        / 100
    )

    current_price = round(
        base_price,
        2
    )

    lower_mid = round(
        (minimum_price + current_price) / 2,
        2
    )

    upper_mid = round(
        (current_price + maximum_price) / 2,
        2
    )

    prices = [
        minimum_price,
        lower_mid,
        current_price,
        upper_mid,
        maximum_price
    ]

    return sorted(
        set(
            price
            for price in prices
            if price > 0
        )
    )

def validate_price_guardrails(
    base_price,
    candidate_prices,
    max_change_pct=0.10
):
    """
    Prevent prices outside the allowed
    percentage change around the current price.
    """

    import math

    # Strict commercial guardrails on a 2-decimal price grid.
    # Lower limit rounds UP and upper limit rounds DOWN,
    # ensuring the configured percentage is never exceeded.
    minimum_price = (
        math.ceil(
            base_price * (1 - max_change_pct) * 100
        )
        / 100
    )

    maximum_price = (
        math.floor(
            base_price * (1 + max_change_pct) * 100
        )
        / 100
    )

    approved = []

    for price in candidate_prices:

        if (
            price >= minimum_price - 0.001
            and
            price <= maximum_price + 0.001
            and
            price > 0
        ):
            approved.append(
                round(float(price), 2)
            )

    return sorted(set(approved))


def recommend_price_auto(
    item_id,
    max_change_pct=0.10
):
    """
    Fully automatic pricing workflow.

    Product ID
        ↓
    Feature store
        ↓
    Demand forecast
        ↓
    Elasticity lookup
        ↓
    Governance
        ↓
    Candidate price generation
        ↓
    Guardrails
        ↓
    Revenue optimization
    """

    # ------------------------------------------
    # 1. Product features
    # ------------------------------------------

    snapshot = get_latest_product_features(
        item_id
    )

    if snapshot is None:

        return {
            "status": "NOT_FOUND",
            "item_id": item_id,
            "reason": (
                "Latest product features "
                "not available."
            )
        }


    # ------------------------------------------
    # 2. Elasticity
    # ------------------------------------------

    elasticity_info = get_elasticity(
        item_id
    )

    if elasticity_info is None:

        return {
            "status": "NOT_FOUND",
            "item_id": item_id,
            "reason": (
                "Product elasticity "
                "not available."
            )
        }


    # ------------------------------------------
    # 3. Automatic ML demand forecast
    # ------------------------------------------

    feature_values = {
        feature:
        snapshot[feature]
        for feature in features
    }

    predicted_demand = forecast_demand(
        feature_values
    )

    current_price = float(
        snapshot["sell_price"]
    )


    # ------------------------------------------
    # 4. Human-in-the-loop governance
    # ------------------------------------------

    if (
        elasticity_info[
            "classification"
        ]
        ==
        "Investigate"
    ):

        return {
            "status": "MANUAL_REVIEW",
            "item_id": item_id,
            "current_price": current_price,
            "forecast_demand": predicted_demand,
            "elasticity": elasticity_info[
                "elasticity"
            ],
            "classification": elasticity_info[
                "classification"
            ],
            "reason": (
                "Elasticity estimate requires "
                "human validation before repricing."
            )
        }


    # ------------------------------------------
    # 5. Automatic candidate prices
    # ------------------------------------------

    candidate_prices = (
        generate_candidate_prices(
            current_price,
            max_change_pct
        )
    )


    # ------------------------------------------
    # 6. Business guardrails
    # ------------------------------------------

    approved_prices = (
        validate_price_guardrails(
            current_price,
            candidate_prices,
            max_change_pct
        )
    )


    if not approved_prices:

        return {
            "status": "MANUAL_REVIEW",
            "item_id": item_id,
            "reason": (
                "No candidate price passed "
                "business guardrails."
            )
        }


    # ------------------------------------------
    # 7. Revenue optimization
    # ------------------------------------------

    optimization = optimize_price(
        base_price=current_price,
        base_demand=predicted_demand,
        elasticity=elasticity_info[
            "elasticity"
        ],
        candidate_prices=approved_prices
    )


    current_revenue = (
        current_price
        *
        predicted_demand
    )

    recommended_revenue = (
        optimization[
            "expected_revenue"
        ]
    )

    revenue_uplift_pct = (
        (
            recommended_revenue
            -
            current_revenue
        )
        /
        current_revenue
        *
        100
        if current_revenue > 0
        else 0.0
    )


    return {
        "status": "AUTO_RECOMMEND",
        "item_id": item_id,

        "snapshot_date":
        snapshot["date"],

        "current_price":
        current_price,

        "forecast_demand":
        predicted_demand,

        "elasticity":
        elasticity_info[
            "elasticity"
        ],

        "classification":
        elasticity_info[
            "classification"
        ],

        "candidate_prices":
        approved_prices,

        "recommended_price":
        optimization[
            "recommended_price"
        ],

        "forecast_demand_at_recommended_price":
        optimization[
            "forecast_demand"
        ],

        "current_expected_revenue":
        current_revenue,

        "recommended_expected_revenue":
        recommended_revenue,

        "expected_revenue_uplift_pct":
        revenue_uplift_pct,

        "guardrail_max_change_pct":
        max_change_pct * 100,

        "scenarios":
        optimization[
            "scenarios"
        ]
    }


# ============================================================
# BACKEND V3 — PROFIT OPTIMIZATION
# ============================================================

def optimize_profit(
    base_price,
    base_demand,
    elasticity,
    candidate_prices,
    unit_cost
):
    """
    Compare candidate prices using both expected
    revenue and expected gross profit.

    Profit = (Price - Unit Cost) * Forecast Demand
    """

    if unit_cost < 0:
        raise ValueError(
            "unit_cost cannot be negative."
        )

    scenarios = []

    for price in candidate_prices:

        demand = (
            base_demand
            *
            (price / base_price)
            ** elasticity
        )

        demand = max(
            float(demand),
            0.0
        )

        revenue = float(
            price * demand
        )

        profit = float(
            (price - unit_cost)
            * demand
        )

        margin_pct = (
            (
                price - unit_cost
            )
            /
            price
            *
            100
            if price > 0
            else 0.0
        )

        scenarios.append({
            "price": float(price),
            "forecast_demand": demand,
            "expected_revenue": revenue,
            "expected_profit": profit,
            "gross_margin_pct": margin_pct
        })


    revenue_best = max(
        scenarios,
        key=lambda x:
        x["expected_revenue"]
    )

    profit_best = max(
        scenarios,
        key=lambda x:
        x["expected_profit"]
    )


    current_profit = (
        (base_price - unit_cost)
        *
        base_demand
    )

    profit_uplift_pct = (
        (
            profit_best["expected_profit"]
            -
            current_profit
        )
        /
        abs(current_profit)
        *
        100
        if current_profit != 0
        else 0.0
    )


    return {
        "unit_cost": float(unit_cost),

        "revenue_maximizing_price":
        revenue_best["price"],

        "profit_maximizing_price":
        profit_best["price"],

        "expected_revenue_at_revenue_optimum":
        revenue_best["expected_revenue"],

        "expected_profit_at_profit_optimum":
        profit_best["expected_profit"],

        "forecast_demand_at_profit_optimum":
        profit_best["forecast_demand"],

        "current_expected_profit":
        float(current_profit),

        "expected_profit_uplift_pct":
        float(profit_uplift_pct),

        "scenarios":
        scenarios
    }


# ============================================================
# BACKEND V3 — AUTOMATIC PROFIT-AWARE RECOMMENDATION
# ============================================================

def recommend_profit_auto(
    item_id,
    unit_cost,
    max_change_pct=0.10
):
    """
    Fully automatic revenue + profit pricing workflow.

    Inputs:
        item_id
        unit_cost

    The engine automatically handles:
        product features
        demand forecasting
        elasticity
        governance
        candidate price generation
        pricing guardrails
        revenue optimization
        profit optimization
    """

    # ------------------------------------------
    # 1. Validate cost
    # ------------------------------------------

    if unit_cost < 0:
        return {
            "status": "INVALID_INPUT",
            "item_id": item_id,
            "reason": "unit_cost cannot be negative."
        }


    # ------------------------------------------
    # 2. Latest product snapshot
    # ------------------------------------------

    snapshot = get_latest_product_features(
        item_id
    )

    if snapshot is None:
        return {
            "status": "NOT_FOUND",
            "item_id": item_id,
            "reason": (
                "Latest product features "
                "not available."
            )
        }


    current_price = float(
        snapshot["sell_price"]
    )


    # ------------------------------------------
    # 3. Cost / margin guardrail
    # ------------------------------------------

    if unit_cost >= current_price:
        return {
            "status": "MANUAL_REVIEW",
            "item_id": item_id,
            "current_price": current_price,
            "unit_cost": float(unit_cost),
            "reason": (
                "Unit cost is greater than or equal "
                "to the current selling price."
            )
        }


    # ------------------------------------------
    # 4. Elasticity
    # ------------------------------------------

    elasticity_info = get_elasticity(
        item_id
    )

    if elasticity_info is None:
        return {
            "status": "NOT_FOUND",
            "item_id": item_id,
            "reason": (
                "Product elasticity "
                "not available."
            )
        }


    # ------------------------------------------
    # 5. Automatic ML demand forecast
    # ------------------------------------------

    feature_values = {
        feature:
        snapshot[feature]
        for feature in features
    }

    predicted_demand = forecast_demand(
        feature_values
    )


    # ------------------------------------------
    # 6. Governance
    # ------------------------------------------

    if (
        elasticity_info["classification"]
        ==
        "Investigate"
    ):
        return {
            "status": "MANUAL_REVIEW",
            "item_id": item_id,
            "current_price": current_price,
            "unit_cost": float(unit_cost),
            "forecast_demand": predicted_demand,
            "elasticity": elasticity_info[
                "elasticity"
            ],
            "classification": elasticity_info[
                "classification"
            ],
            "reason": (
                "Elasticity estimate requires "
                "human validation."
            )
        }


    # ------------------------------------------
    # 7. Generate candidate prices
    # ------------------------------------------

    candidate_prices = generate_candidate_prices(
        current_price,
        max_change_pct
    )


    # ------------------------------------------
    # 8. Apply pricing guardrails
    # ------------------------------------------

    approved_prices = validate_price_guardrails(
        current_price,
        candidate_prices,
        max_change_pct
    )


    # Never optimize toward a price at/below cost
    approved_prices = [
        price
        for price in approved_prices
        if price > unit_cost
    ]


    if not approved_prices:
        return {
            "status": "MANUAL_REVIEW",
            "item_id": item_id,
            "reason": (
                "No profitable candidate price "
                "passed the business guardrails."
            )
        }


    # ------------------------------------------
    # 9. Profit + revenue optimization
    # ------------------------------------------

    optimization = optimize_profit(
        base_price=current_price,
        base_demand=predicted_demand,
        elasticity=elasticity_info[
            "elasticity"
        ],
        candidate_prices=approved_prices,
        unit_cost=unit_cost
    )


    current_revenue = (
        current_price
        *
        predicted_demand
    )

    current_profit = (
        (current_price - unit_cost)
        *
        predicted_demand
    )


    return {
        "status": "AUTO_RECOMMEND",
        "item_id": item_id,

        "snapshot_date":
        snapshot["date"],

        "current_price":
        current_price,

        "unit_cost":
        float(unit_cost),

        "forecast_demand":
        predicted_demand,

        "elasticity":
        elasticity_info[
            "elasticity"
        ],

        "classification":
        elasticity_info[
            "classification"
        ],

        "current_expected_revenue":
        current_revenue,

        "current_expected_profit":
        current_profit,

        "candidate_prices":
        approved_prices,

        "revenue_maximizing_price":
        optimization[
            "revenue_maximizing_price"
        ],

        "profit_maximizing_price":
        optimization[
            "profit_maximizing_price"
        ],

        "expected_revenue_at_revenue_optimum":
        optimization[
            "expected_revenue_at_revenue_optimum"
        ],

        "expected_profit_at_profit_optimum":
        optimization[
            "expected_profit_at_profit_optimum"
        ],

        "expected_profit_uplift_pct":
        optimization[
            "expected_profit_uplift_pct"
        ],

        "forecast_demand_at_profit_optimum":
        optimization[
            "forecast_demand_at_profit_optimum"
        ],

        "guardrail_max_change_pct":
        max_change_pct * 100,

        "scenarios":
        optimization[
            "scenarios"
        ]
    }


# ============================================================
# BACKEND V4 — EXECUTIVE DECISION EXPLANATION
# ============================================================

def build_pricing_explanation(result):
    """
    Convert pricing-engine outputs into a concise
    executive decision explanation and governance checks.
    """

    if result.get("status") != "AUTO_RECOMMEND":

        return {
            "decision_summary": (
                result.get(
                    "reason",
                    "Recommendation requires human review."
                )
            ),
            "governance_checks": {
                "automatic_recommendation": False
            }
        }


    current_price = float(
        result["current_price"]
    )

    recommended_price = float(
        result["profit_maximizing_price"]
    )

    elasticity = float(
        result["elasticity"]
    )

    classification = result[
        "classification"
    ]

    profit_uplift = float(
        result["expected_profit_uplift_pct"]
    )

    max_change = float(
        result["guardrail_max_change_pct"]
    )

    unit_cost = float(
        result["unit_cost"]
    )


    # ------------------------------------------
    # Price direction
    # ------------------------------------------

    if recommended_price > current_price:

        direction_text = (
            f"Increase the price from "
            f"{current_price:.2f} to "
            f"{recommended_price:.2f}."
        )

    elif recommended_price < current_price:

        direction_text = (
            f"Decrease the price from "
            f"{current_price:.2f} to "
            f"{recommended_price:.2f}."
        )

    else:

        direction_text = (
            f"Maintain the current price at "
            f"{current_price:.2f}."
        )


    # ------------------------------------------
    # Elasticity interpretation
    # ------------------------------------------

    if classification == "Inelastic":

        elasticity_text = (
            "The SKU is relatively price-inelastic, "
            "so forecast demand is expected to remain "
            "comparatively stable under moderate price changes."
        )

    elif classification == "Elastic":

        elasticity_text = (
            "The SKU is price-sensitive, so demand may "
            "respond materially to price changes."
        )

    else:

        elasticity_text = (
            "The estimated price-response relationship "
            "requires additional validation."
        )


    # ------------------------------------------
    # Profit interpretation
    # ------------------------------------------

    if profit_uplift > 0:

        profit_text = (
            f"The selected price is expected to improve "
            f"gross profit by approximately "
            f"{profit_uplift:.1f}%."
        )

    elif profit_uplift < 0:

        profit_text = (
            f"The scenario implies an expected gross-profit "
            f"change of {profit_uplift:.1f}%."
        )

    else:

        profit_text = (
            "The selected scenario does not materially "
            "change expected gross profit."
        )


    guardrail_text = (
        f"The recommendation remains inside the configured "
        f"±{max_change:.0f}% pricing guardrail."
    )


    decision_summary = " ".join(
        [
            direction_text,
            elasticity_text,
            profit_text,
            guardrail_text
        ]
    )


    # ------------------------------------------
    # Governance checks
    # ------------------------------------------

    price_change_pct = (
        (
            recommended_price
            -
            current_price
        )
        /
        current_price
        *
        100
        if current_price > 0
        else 0
    )


    governance_checks = {
        "elasticity_accepted":
        classification in [
            "Elastic",
            "Inelastic"
        ],

        "automatic_recommendation":
        result["status"]
        ==
        "AUTO_RECOMMEND",

        "price_within_guardrails":
        abs(price_change_pct)
        <=
        max_change + 0.01,

        "price_above_unit_cost":
        recommended_price
        >
        unit_cost,

        "positive_expected_profit":
        result[
            "expected_profit_at_profit_optimum"
        ]
        >
        0
    }


    return {
        "decision_summary":
        decision_summary,

        "governance_checks":
        governance_checks
    }


# ============================================================
# BACKEND V5 — PORTFOLIO OPPORTUNITY ENGINE
# ============================================================

def build_portfolio_opportunities(
    max_change_pct=0.10,
    top_n=None
):
    """
    Scan eligible products and rank automatic
    repricing opportunities by expected revenue gain.
    """

    opportunities = []

    portfolio_elasticity_table = pd.read_csv(
        ELASTICITY_PATH
    )

    eligible_products = portfolio_elasticity_table[
        portfolio_elasticity_table["classification"].isin(
            ["Elastic", "Inelastic"]
        )
    ]["item_id"].unique()


    for item_id in eligible_products:

        try:

            result = recommend_price_auto(
                item_id=item_id,
                max_change_pct=max_change_pct
            )

            if result.get("status") != "AUTO_RECOMMEND":
                continue


            current_revenue = float(
                result["current_expected_revenue"]
            )

            recommended_revenue = float(
                result["recommended_expected_revenue"]
            )

            revenue_gain = (
                recommended_revenue
                -
                current_revenue
            )


            price_change_pct = (
                (
                    result["recommended_price"]
                    -
                    result["current_price"]
                )
                /
                result["current_price"]
                *
                100
                if result["current_price"] > 0
                else 0
            )


            opportunities.append({
                "item_id":
                    item_id,

                "classification":
                    result["classification"],

                "elasticity":
                    result["elasticity"],

                "current_price":
                    result["current_price"],

                "recommended_price":
                    result["recommended_price"],

                "price_change_pct":
                    price_change_pct,

                "forecast_demand":
                    result["forecast_demand"],

                "current_expected_revenue":
                    current_revenue,

                "recommended_expected_revenue":
                    recommended_revenue,

                "expected_revenue_gain":
                    revenue_gain,

                "expected_revenue_uplift_pct":
                    result[
                        "expected_revenue_uplift_pct"
                    ],

                "snapshot_date":
                    result["snapshot_date"]
            })


        except Exception:
            continue


    portfolio = pd.DataFrame(
        opportunities
    )


    if portfolio.empty:
        return portfolio


    portfolio = portfolio.sort_values(
        [
            "expected_revenue_gain",
            "expected_revenue_uplift_pct"
        ],
        ascending=False
    ).reset_index(drop=True)


    portfolio.insert(
        0,
        "rank",
        range(
            1,
            len(portfolio) + 1
        )
    )


    if top_n is not None:

        portfolio = portfolio.head(
            int(top_n)
        )


    return portfolio
