
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import requests
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[2]

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


from dashboard.ui import (
    apply_professional_style,
    friendly_product_name
)


st.set_page_config(
    page_title="Pricing Decision Center",
    page_icon="◈",
    layout="wide"
)

apply_professional_style()

API_URL = "http://127.0.0.1:8001"


# ============================================================
# VISUAL STYLE
# ============================================================

st.html(
    """
    <style>

    .decision-hero {
        padding: 0.7rem 0 1.5rem 0;
    }

    .eyebrow {
        font-size: .72rem;
        font-weight: 700;
        letter-spacing: .12em;
        text-transform: uppercase;
        color: #64748b;
    }

    .decision-title {
        font-size: 2.4rem;
        font-weight: 750;
        letter-spacing: -.045em;
        color: #0f172a;
        margin-top: .35rem;
    }

    .decision-copy {
        color: #64748b;
        margin-top: .65rem;
        max-width: 850px;
        line-height: 1.55;
    }

    .decision-panel {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.2rem 1.3rem;
    }

    .decision-product {
        font-size: 1.2rem;
        font-weight: 720;
        color: #0f172a;
    }

    .decision-summary {
        margin-top: .75rem;
        color: #475569;
        line-height: 1.6;
    }

    .status-good {
        display: inline-block;
        padding: .28rem .62rem;
        border-radius: 999px;
        background: #ecfdf5;
        border: 1px solid #bbf7d0;
        color: #166534;
        font-size: .73rem;
        font-weight: 700;
    }

    .governance-card {
        padding: .85rem 1rem;
        border-radius: 12px;
        background: #f0fdf4;
        border: 1px solid #dcfce7;
        color: #166534;
        font-size: .8rem;
        font-weight: 650;
        min-height: 62px;
    }

    </style>
    """
)


# ============================================================
# PRODUCT LIST
# ============================================================

@st.cache_data
def load_products():

    path = (
        BASE_DIR
        / "data"
        / "master_product_elasticities.csv"
    )

    df = pd.read_csv(path)

    return sorted(
        df["item_id"]
        .dropna()
        .unique()
        .tolist()
    )


products = load_products()


# ============================================================
# HERO
# ============================================================

st.html(
    """
    <div class="decision-hero">

        <div class="eyebrow">
            Decision intelligence
        </div>

        <div class="decision-title">
            Pricing Decision Center
        </div>

        <div class="decision-copy">
            AI-assisted SKU pricing combining demand forecasting,
            elasticity, revenue optimization, unit economics and
            commercial governance.
        </div>

    </div>
    """
)


# ============================================================
# PRODUCT + BUSINESS INPUTS
# ============================================================

st.markdown("## Decision Inputs")

c1, c2, c3 = st.columns(
    [1.6, 1, 1]
)


with c1:

    selected_product = st.selectbox(
        "Product",
        products,
        format_func=friendly_product_name,
        index=(
            products.index("HOBBIES_1_295")
            if "HOBBIES_1_295" in products
            else 0
        )
    )


with c2:

    unit_cost = st.number_input(
        "Unit Cost",
        min_value=0.01,
        value=0.30,
        step=0.01,
        format="%.2f"
    )


with c3:

    guardrail_pct = st.slider(
        "Maximum Price Change",
        min_value=1,
        max_value=25,
        value=10,
        step=1,
        format="%d%%"
    )


run = st.button(
    "Run AI Pricing Decision",
    type="primary",
    use_container_width=True
)


# ============================================================
# API CALL
# ============================================================

if run:

    try:

        response = requests.post(
            f"{API_URL}/recommend-profit-auto",
            json={
                "item_id":
                    selected_product,

                "unit_cost":
                    unit_cost,

                "max_change_pct":
                    guardrail_pct / 100
            },
            timeout=60
        )

        response.raise_for_status()

        st.session_state[
            "pricing_result"
        ] = response.json()


    except requests.exceptions.ConnectionError:

        st.error(
            "FastAPI backend is offline."
        )


    except Exception as e:

        st.error(
            f"Pricing engine error: {e}"
        )


# ============================================================
# RESULTS
# ============================================================

result = st.session_state.get(
    "pricing_result"
)


if result:

    product_label = friendly_product_name(
        result["item_id"]
    )

    recommended_price = result.get(
        "profit_maximizing_price",
        result.get(
            "recommended_price"
        )
    )

    current_price = result[
        "current_price"
    ]

    profit_uplift = result.get(
        "expected_profit_uplift_pct",
        0
    )

    action = (
        "Increase"
        if recommended_price > current_price
        else
        "Decrease"
        if recommended_price < current_price
        else
        "Hold"
    )


    # ========================================================
    # EXECUTIVE DECISION
    # ========================================================

    st.divider()

    st.markdown(
        "## Executive Recommendation"
    )

    summary_text = result.get(
        "decision_summary",
        (
            f"{action} the price from "
            f"{current_price:.2f} to "
            f"{recommended_price:.2f}."
        )
    )


    st.html(
        f"""
        <div class="decision-panel">

            <div class="decision-product">
                {product_label}
                &nbsp;
                <span class="status-good">
                    ✓ {result["status"].replace("_", " ")}
                </span>
            </div>

            <div class="decision-summary">
                {summary_text}
            </div>

        </div>
        """
    )


    # ========================================================
    # CORE KPIs
    # ========================================================

    st.markdown("### Decision KPIs")

    k1, k2, k3, k4 = st.columns(4)

    k1.metric(
        "Current Price",
        f"{current_price:.2f}"
    )

    k2.metric(
        "Recommended Price",
        f"{recommended_price:.2f}",
        delta=(
            f"{((recommended_price/current_price)-1)*100:+.1f}%"
        )
    )

    k3.metric(
        "Expected Profit Uplift",
        f"{profit_uplift:.2f}%"
    )

    k4.metric(
        "Forecast Demand",
        f"{result['forecast_demand']:.2f}"
    )


    k5, k6, k7, k8 = st.columns(4)

    k5.metric(
        "Unit Cost",
        f"{result['unit_cost']:.2f}"
    )

    k6.metric(
        "Elasticity",
        f"{result['elasticity']:.3f}"
    )

    k7.metric(
        "Elasticity Segment",
        result["classification"]
    )

    k8.metric(
        "Guardrail",
        f"±{result['guardrail_max_change_pct']:.0f}%"
    )


    # ========================================================
    # REVENUE VS PROFIT OPTIMA
    # ========================================================

    st.divider()

    st.markdown(
        "## Revenue vs Profit Optimization"
    )

    r1, r2, r3 = st.columns(3)

    r1.metric(
        "Revenue-Max Price",
        f"{result['revenue_maximizing_price']:.2f}"
    )

    r2.metric(
        "Profit-Max Price",
        f"{result['profit_maximizing_price']:.2f}"
    )

    r3.metric(
        "Expected Profit at Optimum",
        f"{result['expected_profit_at_profit_optimum']:.2f}"
    )


    # ========================================================
    # SCENARIOS
    # ========================================================

    scenarios = pd.DataFrame(
        result["scenarios"]
    )

    st.divider()

    st.markdown(
        "## Pricing Scenario Analysis"
    )

    scenario_table = scenarios.copy()

    display_cols = [
        col
        for col in [
            "price",
            "forecast_demand",
            "expected_revenue",
            "expected_profit",
            "gross_margin_pct"
        ]
        if col in scenario_table.columns
    ]

    st.dataframe(
        scenario_table[display_cols],
        use_container_width=True,
        hide_index=True
    )


    # ========================================================
    # PROFESSIONAL CURVES
    # ========================================================

    left, right = st.columns(2)


    with left:

        st.markdown(
            "### Revenue Curve"
        )

        revenue_chart = (
            alt.Chart(
                scenarios
            )
            .mark_line(
                point=True,
                strokeWidth=3
            )
            .encode(
                x=alt.X(
                    "price:Q",
                    title="Candidate Price"
                ),

                y=alt.Y(
                    "expected_revenue:Q",
                    title="Expected Revenue"
                ),

                tooltip=[
                    alt.Tooltip(
                        "price:Q",
                        format=".2f"
                    ),

                    alt.Tooltip(
                        "expected_revenue:Q",
                        format=".2f"
                    ),

                    alt.Tooltip(
                        "forecast_demand:Q",
                        format=".2f"
                    )
                ]
            )
            .properties(
                height=330
            )
        )

        st.altair_chart(
            revenue_chart,
            use_container_width=True
        )


    with right:

        st.markdown(
            "### Profit Curve"
        )

        profit_chart = (
            alt.Chart(
                scenarios
            )
            .mark_line(
                point=True,
                strokeWidth=3
            )
            .encode(
                x=alt.X(
                    "price:Q",
                    title="Candidate Price"
                ),

                y=alt.Y(
                    "expected_profit:Q",
                    title="Expected Profit"
                ),

                tooltip=[
                    alt.Tooltip(
                        "price:Q",
                        format=".2f"
                    ),

                    alt.Tooltip(
                        "expected_profit:Q",
                        format=".2f"
                    ),

                    alt.Tooltip(
                        "forecast_demand:Q",
                        format=".2f"
                    )
                ]
            )
            .properties(
                height=330
            )
        )

        st.altair_chart(
            profit_chart,
            use_container_width=True
        )


    # ========================================================
    # DEMAND RESPONSE
    # ========================================================

    st.markdown(
        "### Demand Response"
    )

    demand_chart = (
        alt.Chart(
            scenarios
        )
        .mark_line(
            point=True,
            strokeWidth=3
        )
        .encode(
            x=alt.X(
                "price:Q",
                title="Price"
            ),

            y=alt.Y(
                "forecast_demand:Q",
                title="Forecast Demand"
            ),

            tooltip=[
                alt.Tooltip(
                    "price:Q",
                    format=".2f"
                ),

                alt.Tooltip(
                    "forecast_demand:Q",
                    format=".2f"
                )
            ]
        )
        .properties(
            height=300
        )
    )

    st.altair_chart(
        demand_chart,
        use_container_width=True
    )


    # ========================================================
    # GOVERNANCE
    # ========================================================

    governance = result.get(
        "governance_checks",
        {}
    )

    if governance:

        st.divider()

        st.markdown(
            "## Governance Status"
        )

        labels = {
            "elasticity_accepted":
                "Elasticity Accepted",

            "automatic_recommendation":
                "Auto Recommendation",

            "price_within_guardrails":
                "Within Guardrails",

            "price_above_unit_cost":
                "Above Unit Cost",

            "positive_expected_profit":
                "Positive Expected Profit"
        }

        cols = st.columns(
            len(labels)
        )

        for col, (
            key,
            label
        ) in zip(
            cols,
            labels.items()
        ):

            with col:

                passed = governance.get(
                    key,
                    False
                )

                if passed:

                    st.html(
                        f"""
                        <div class="governance-card">
                            ✓ {label}
                        </div>
                        """
                    )

                else:

                    st.error(
                        f"Review · {label}"
                    )


    # ========================================================
    # TECHNICAL TRACEABILITY
    # ========================================================

    with st.expander(
        "Technical decision details"
    ):

        st.write(
            "**Technical Product ID:**",
            result["item_id"]
        )

        st.write(
            "**Snapshot Date:**",
            result.get(
                "snapshot_date",
                "N/A"
            )
        )

        st.json(result)


else:

    st.info(
        """
        Select a product, provide unit cost and pricing guardrail,
        then run the AI Pricing Decision.
        """
    )


st.caption(
    """
    AI Demand & Pricing Engine · Pricing Decision Intelligence
    """
)
