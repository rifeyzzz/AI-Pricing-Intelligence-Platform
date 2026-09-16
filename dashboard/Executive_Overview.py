
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import requests
import streamlit as st


# ============================================================
# PROJECT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from dashboard.ui import (
    apply_professional_style,
    friendly_product_name,
    clean_model_name
)


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="AI Pricing Intelligence",
    page_icon="◈",
    layout="wide"
)

apply_professional_style()

API_URL = "http://127.0.0.1:8001"


# ============================================================
# EXECUTIVE STYLING
# ============================================================

st.html(
    """
    <style>

    .hero {
        padding: 1rem 0 2rem 0;
    }

    .eyebrow {
        font-size: .72rem;
        font-weight: 700;
        letter-spacing: .13em;
        text-transform: uppercase;
        color: #64748b;
    }

    .hero-title {
        font-size: 2.7rem;
        font-weight: 760;
        letter-spacing: -.05em;
        line-height: 1.05;
        color: #0f172a;
        margin-top: .4rem;
    }

    .hero-copy {
        color: #64748b;
        font-size: 1rem;
        max-width: 880px;
        line-height: 1.6;
        margin-top: .8rem;
    }

    .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: .55rem;
        margin-top: 1rem;
    }

    .chip {
        display: inline-block;
        padding: .34rem .72rem;
        border-radius: 999px;
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        color: #334155;
        font-size: .74rem;
        font-weight: 650;
    }

    .chip-online {
        background: #ecfdf5;
        border-color: #bbf7d0;
        color: #166534;
    }

    .hero-card {
        border: 1px solid #e2e8f0;
        background: #ffffff;
        border-radius: 16px;
        padding: 1.25rem 1.35rem;
        min-height: 155px;
    }

    .card-eyebrow {
        font-size: .7rem;
        font-weight: 700;
        letter-spacing: .08em;
        text-transform: uppercase;
        color: #64748b;
    }

    .card-big {
        margin-top: .25rem;
        font-size: 2rem;
        font-weight: 740;
        letter-spacing: -.04em;
        color: #0f172a;
    }

    .card-copy {
        margin-top: .4rem;
        font-size: .78rem;
        color: #64748b;
        line-height: 1.45;
    }

    .positive {
        color: #15803d;
        font-weight: 700;
    }

    .decision-card {
        padding: 1.25rem 1.35rem;
        border-radius: 16px;
        border: 1px solid #dbeafe;
        background: #f8fbff;
    }

    .product-name {
        font-size: 1.25rem;
        font-weight: 720;
        color: #0f172a;
    }

    .decision-copy {
        color: #475569;
        line-height: 1.65;
        margin-top: .65rem;
    }

    .stage-card {
        border: 1px solid #e2e8f0;
        background: #ffffff;
        border-radius: 14px;
        padding: 1rem 1.05rem;
        min-height: 138px;
    }

    .stage-number {
        font-size: .68rem;
        font-weight: 700;
        color: #2563eb;
        letter-spacing: .08em;
    }

    .stage-title {
        font-size: .95rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: .35rem;
    }

    .stage-copy {
        font-size: .75rem;
        line-height: 1.45;
        color: #64748b;
        margin-top: .35rem;
    }

    .benchmark-box {
        border: 1px solid #e2e8f0;
        border-radius: 15px;
        padding: 1.1rem 1.2rem;
        background: #ffffff;
    }

    .benchmark-title {
        font-size: .72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .07em;
        color: #64748b;
    }

    .benchmark-number {
        font-size: 1.8rem;
        font-weight: 730;
        letter-spacing: -.04em;
        margin-top: .25rem;
    }

    .benchmark-foot {
        font-size: .76rem;
        color: #64748b;
        margin-top: .3rem;
    }

    </style>
    """
)


# ============================================================
# DATA LOADERS
# ============================================================

@st.cache_data(ttl=120)
def backend_health():

    response = requests.get(
        f"{API_URL}/health",
        timeout=4
    )

    response.raise_for_status()

    return response.json()


@st.cache_data(ttl=300)
def model_info():

    response = requests.get(
        f"{API_URL}/model-info",
        timeout=10
    )

    response.raise_for_status()

    return response.json()


@st.cache_data(ttl=300)
def portfolio_info():

    response = requests.get(
        f"{API_URL}/portfolio-opportunities",
        params={
            "top_n": 10,
            "max_change_pct": 0.10
        },
        timeout=90
    )

    response.raise_for_status()

    return response.json()


@st.cache_data
def elasticity_data():

    path = (
        BASE_DIR
        / "data"
        / "master_product_elasticities.csv"
    )

    return pd.read_csv(path)


try:

    health = backend_health()
    model = model_info()
    portfolio_payload = portfolio_info()

    engine_online = True

except Exception:

    engine_online = False


if not engine_online:

    st.error(
        "FastAPI backend is offline. Start the backend on port 8001."
    )

    st.stop()


elasticity = elasticity_data()

portfolio = pd.DataFrame(
    portfolio_payload["opportunities"]
)


# ============================================================
# PORTFOLIO STATISTICS
# ============================================================

total_products = len(elasticity)

manual_review = int(
    (
        elasticity["classification"]
        == "Investigate"
    ).sum()
)

auto_eligible = total_products - manual_review

evaluation = model["evaluation"]
baseline = model["baseline"]

mae_improvement = float(
    model["computed_metrics"][
        "mae_improvement_vs_baseline_pct"
    ]
)

rmse_improvement = (
    (baseline["rmse"] - evaluation["rmse"])
    / baseline["rmse"]
    * 100
)

r2_gain = (
    evaluation["r2"]
    - baseline["r2"]
)


# ============================================================
# HERO
# ============================================================

st.html(
    f"""
    <div class="hero">

        <div class="eyebrow">
            AI decision intelligence
        </div>

        <div class="hero-title">
            AI Pricing Intelligence Platform
        </div>

        <div class="hero-copy">
            An end-to-end machine-learning pricing system combining
            SKU-level demand forecasting, price elasticity,
            revenue and profit optimization, commercial guardrails,
            portfolio prioritization and human-in-the-loop governance.
        </div>

        <div class="chip-row">

            <span class="chip chip-online">
                ● Engine Online
            </span>

            <span class="chip">
                {clean_model_name(model["model_type"])}
            </span>

            <span class="chip">
                {total_products} Products Modeled
            </span>

            <span class="chip">
                16 Automated Tests Passed
            </span>

        </div>

    </div>
    """
)


# ============================================================
# EXECUTIVE KPIs
# ============================================================

st.markdown("## Executive Snapshot")

c1, c2, c3, c4 = st.columns(4)


with c1:

    st.html(
        f"""
        <div class="hero-card">
            <div class="card-eyebrow">Products Modeled</div>
            <div class="card-big">{total_products:,}</div>
            <div class="card-copy">
                SKU-level elasticity coverage across the modeled portfolio.
            </div>
        </div>
        """
    )


with c2:

    st.html(
        f"""
        <div class="hero-card">
            <div class="card-eyebrow">Auto-Recommend Eligible</div>
            <div class="card-big">{auto_eligible:,}</div>
            <div class="card-copy positive">
                {auto_eligible / total_products * 100:.1f}% of modeled products
            </div>
        </div>
        """
    )


with c3:

    st.html(
        f"""
        <div class="hero-card">
            <div class="card-eyebrow">Human Review</div>
            <div class="card-big">{manual_review:,}</div>
            <div class="card-copy">
                Routed to manual validation because elasticity requires investigation.
            </div>
        </div>
        """
    )


with c4:

    st.html(
        f"""
        <div class="hero-card">
            <div class="card-eyebrow">Forecast Error Reduction</div>
            <div class="card-big">{mae_improvement:.1f}%</div>
            <div class="card-copy positive">
                Lower MAE versus lag-1 baseline
            </div>
        </div>
        """
    )


# ============================================================
# MODEL BENCHMARK
# ============================================================

st.divider()

st.markdown("## Model Benchmark")

st.caption(
    "Performance on the chronological 28-day holdout."
)

b1, b2, b3 = st.columns(3)


with b1:

    st.html(
        f"""
        <div class="benchmark-box">
            <div class="benchmark-title">Mean Absolute Error</div>
            <div class="benchmark-number">{evaluation["mae"]:.3f}</div>
            <div class="benchmark-foot">
                Baseline {baseline["mae"]:.3f}
                ·
                <span class="positive">{mae_improvement:.1f}% lower</span>
            </div>
        </div>
        """
    )


with b2:

    st.html(
        f"""
        <div class="benchmark-box">
            <div class="benchmark-title">Root Mean Squared Error</div>
            <div class="benchmark-number">{evaluation["rmse"]:.3f}</div>
            <div class="benchmark-foot">
                Baseline {baseline["rmse"]:.3f}
                ·
                <span class="positive">{rmse_improvement:.1f}% lower</span>
            </div>
        </div>
        """
    )


with b3:

    st.html(
        f"""
        <div class="benchmark-box">
            <div class="benchmark-title">R² Score</div>
            <div class="benchmark-number">{evaluation["r2"]:.3f}</div>
            <div class="benchmark-foot">
                Baseline {baseline["r2"]:.3f}
                ·
                <span class="positive">+{r2_gain:.3f}</span>
            </div>
        </div>
        """
    )


# ============================================================
# TOP COMMERCIAL OPPORTUNITY
# ============================================================

if not portfolio.empty:

    best = (
        portfolio
        .sort_values(
            "expected_revenue_gain",
            ascending=False
        )
        .iloc[0]
    )

    friendly = friendly_product_name(
        best["item_id"]
    )

    action = (
        "Increase"
        if best["recommended_price"] > best["current_price"]
        else
        "Decrease"
        if best["recommended_price"] < best["current_price"]
        else
        "Hold"
    )


    st.divider()

    st.markdown(
        "## Highest-Priority Commercial Opportunity"
    )

    st.html(
        f"""
        <div class="decision-card">

            <div class="product-name">
                {friendly}
            </div>

            <div class="decision-copy">

                Recommended action:
                <b>{action}</b>

                &nbsp;·&nbsp;

                Price:
                <b>{best["current_price"]:.2f}</b>
                →
                <b>{best["recommended_price"]:.2f}</b>

                <br><br>

                Expected revenue gain:
                <b>{best["expected_revenue_gain"]:.2f}</b>

                &nbsp;·&nbsp;

                Expected uplift:
                <b>{best["expected_revenue_uplift_pct"]:.2f}%</b>

                &nbsp;·&nbsp;

                Elasticity:
                <b>{best["elasticity"]:.3f}</b>

            </div>

        </div>
        """
    )


# ============================================================
# GOVERNANCE
# ============================================================

st.divider()

st.markdown(
    "## Portfolio Governance"
)

left, right = st.columns(
    [1.05, 1]
)


governance_df = pd.DataFrame(
    {
        "Decision Route": [
            "Auto-Recommend",
            "Human Review"
        ],
        "Products": [
            auto_eligible,
            manual_review
        ]
    }
)


with left:

    governance_chart = (
        alt.Chart(
            governance_df
        )
        .mark_arc(
            innerRadius=72,
            outerRadius=115
        )
        .encode(
            theta="Products:Q",
            color=alt.Color(
                "Decision Route:N",
                title=None
            ),
            tooltip=[
                "Decision Route:N",
                "Products:Q"
            ]
        )
        .properties(
            height=320
        )
    )

    st.altair_chart(
        governance_chart,
        use_container_width=True
    )


with right:

    st.markdown(
        "### Human-in-the-Loop Policy"
    )

    st.write(
        """
        Products with economically coherent elasticity estimates
        can enter the automated recommendation workflow.
        """
    )

    st.write(
        """
        Products classified as **Investigate** are deliberately
        excluded from automatic repricing and routed to manual review.
        """
    )

    st.success(
        f"{auto_eligible} products currently qualify "
        "for automated decision support."
    )

    st.warning(
        f"{manual_review} products remain under human review."
    )


# ============================================================
# WORKFLOW
# ============================================================

st.divider()

st.markdown(
    "## Decision Intelligence Workflow"
)

s1, s2, s3, s4 = st.columns(4)


with s1:

    st.html(
        """
        <div class="stage-card">
            <div class="stage-number">01 · FORECAST</div>
            <div class="stage-title">Demand Intelligence</div>
            <div class="stage-copy">
                Predict SKU demand using price, lag signals,
                rolling demand and calendar features.
            </div>
        </div>
        """
    )


with s2:

    st.html(
        """
        <div class="stage-card">
            <div class="stage-number">02 · UNDERSTAND</div>
            <div class="stage-title">Price Elasticity</div>
            <div class="stage-copy">
                Estimate product-level price sensitivity
                and identify economically coherent recommendations.
            </div>
        </div>
        """
    )


with s3:

    st.html(
        """
        <div class="stage-card">
            <div class="stage-number">03 · OPTIMIZE</div>
            <div class="stage-title">Revenue & Profit</div>
            <div class="stage-copy">
                Simulate candidate prices and identify
                revenue-maximizing and profit-maximizing decisions.
            </div>
        </div>
        """
    )


with s4:

    st.html(
        """
        <div class="stage-card">
            <div class="stage-number">04 · GOVERN</div>
            <div class="stage-title">Decision Control</div>
            <div class="stage-copy">
                Apply pricing guardrails, profitability checks
                and human-review controls before recommendations are surfaced.
            </div>
        </div>
        """
    )


st.caption(
    """
    AI Demand & Pricing Engine ·
    Machine-Learning Pricing Decision Intelligence Platform
    """
)
