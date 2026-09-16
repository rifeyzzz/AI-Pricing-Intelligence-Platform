
import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

# ============================================================
# PROJECT IMPORTS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from dashboard.ui import (
    apply_professional_style,
    clean_model_name
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Model Intelligence",
    page_icon="◈",
    layout="wide"
)

apply_professional_style()

API_URL = "http://127.0.0.1:8001"


# ============================================================
# EXTRA PAGE STYLING
# ============================================================

st.html("""
    <style>

    .hero {
        padding: 1.1rem 0 1.8rem 0;
    }

    .eyebrow {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #64748b;
        margin-bottom: 0.4rem;
    }

    .hero-title {
        font-size: 2.35rem;
        line-height: 1.05;
        font-weight: 750;
        letter-spacing: -0.045em;
        color: #0f172a;
    }

    .hero-subtitle {
        margin-top: 0.7rem;
        max-width: 850px;
        color: #64748b;
        font-size: 0.98rem;
        line-height: 1.55;
    }

    .status-row {
        display: flex;
        gap: 0.55rem;
        flex-wrap: wrap;
        margin-top: 1rem;
    }

    .status-chip {
        padding: 0.36rem 0.7rem;
        border-radius: 999px;
        font-size: 0.76rem;
        font-weight: 650;
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        color: #334155;
    }

    .status-chip.good {
        background: #ecfdf5;
        border-color: #bbf7d0;
        color: #166534;
    }

    .benchmark-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.2rem 1.3rem;
        margin-bottom: 0.85rem;
    }

    .benchmark-label {
        font-size: 0.74rem;
        color: #64748b;
        font-weight: 650;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    .benchmark-value {
        font-size: 1.7rem;
        font-weight: 720;
        letter-spacing: -0.035em;
        color: #0f172a;
        margin-top: 0.2rem;
    }

    .benchmark-sub {
        font-size: 0.77rem;
        color: #64748b;
        margin-top: 0.25rem;
    }

    .benchmark-win {
        color: #15803d;
        font-weight: 700;
    }

    .bar-bg {
        height: 9px;
        width: 100%;
        border-radius: 999px;
        background: #eef2f7;
        overflow: hidden;
        margin-top: 0.65rem;
    }

    .bar-ai {
        height: 100%;
        border-radius: 999px;
        background: #2563eb;
    }

    .bar-base {
        height: 100%;
        border-radius: 999px;
        background: #94a3b8;
    }

    .feature-row {
        display: grid;
        grid-template-columns: 185px 1fr 75px;
        gap: 14px;
        align-items: center;
        margin: 0.72rem 0;
    }

    .feature-name {
        font-size: 0.85rem;
        font-weight: 600;
        color: #334155;
    }

    .feature-value {
        font-size: 0.78rem;
        text-align: right;
        font-variant-numeric: tabular-nums;
        color: #475569;
    }

    .feature-bg {
        height: 11px;
        border-radius: 999px;
        background: #eef2f7;
        overflow: hidden;
    }

    .feature-fill {
        height: 100%;
        border-radius: 999px;
        background: #2563eb;
    }

    .governance-card {
        border: 1px solid #dcfce7;
        background: #f0fdf4;
        border-radius: 13px;
        padding: 0.85rem 1rem;
        min-height: 92px;
    }

    .governance-title {
        font-size: 0.83rem;
        font-weight: 700;
        color: #166534;
    }

    .governance-copy {
        font-size: 0.73rem;
        color: #4b5563;
        margin-top: 0.25rem;
    }

    .interpretation-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1.1rem 1.2rem;
        line-height: 1.55;
    }

    </style>
    """)


# ============================================================
# API LOADERS
# ============================================================

@st.cache_data(ttl=300)
def load_model_info():

    response = requests.get(
        f"{API_URL}/model-info",
        timeout=10
    )

    response.raise_for_status()

    return response.json()


@st.cache_data(ttl=300)
def load_feature_importance():

    response = requests.get(
        f"{API_URL}/feature-importance",
        timeout=10
    )

    response.raise_for_status()

    return response.json()


try:

    model = load_model_info()
    importance_payload = load_feature_importance()

except requests.exceptions.ConnectionError:

    st.error(
        "FastAPI backend is offline. "
        "Start the backend on port 8001."
    )

    st.stop()

except Exception as e:

    st.error(
        f"Unable to load model intelligence: {e}"
    )

    st.stop()


evaluation = model["evaluation"]
baseline = model["baseline"]

improvement_mae = float(
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
    -
    baseline["r2"]
)


# ============================================================
# HERO
# ============================================================

business_model_name = clean_model_name(
    model["model_type"]
)

st.html(f"""
    <div class="hero">

        <div class="eyebrow">
            Model intelligence
        </div>

        <div class="hero-title">
            Forecast Performance & Explainability
        </div>

        <div class="hero-subtitle">
            Validation, benchmarking and predictive explainability
            for the demand forecasting engine powering automated
            pricing recommendations.
        </div>

        <div class="status-row">

            <span class="status-chip good">
                ● {model["status"]}
            </span>

            <span class="status-chip">
                {business_model_name}
            </span>

            <span class="status-chip">
                v{model["version"]}
            </span>

            <span class="status-chip">
                28-day chronological holdout
            </span>

        </div>

    </div>
    """)


# ============================================================
# EXECUTIVE KPI CARDS
# ============================================================

st.markdown("## Executive Model KPIs")

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Mean Absolute Error",
    f"{evaluation['mae']:.3f}",
    delta=f"{improvement_mae:.1f}% lower vs baseline",
    delta_color="normal"
)

k2.metric(
    "Root Mean Squared Error",
    f"{evaluation['rmse']:.3f}",
    delta=f"{rmse_improvement:.1f}% lower vs baseline",
    delta_color="normal"
)

k3.metric(
    "R² Score",
    f"{evaluation['r2']:.3f}",
    delta=f"+{r2_gain:.3f} vs baseline"
)

k4.metric(
    "Active Features",
    len(model["features"]),
    delta="Production feature set",
    delta_color="off"
)


# ============================================================
# PROFESSIONAL BENCHMARK
# ============================================================

st.divider()

st.markdown("## Forecast Benchmark")

st.caption(
    "AI Demand Model versus a lag-1 naive forecasting baseline."
)

ai_name = clean_model_name(
    model["model_type"]
)

baseline_name = clean_model_name(
    baseline["model"]
)


# MAE
mae_max = max(
    baseline["mae"],
    evaluation["mae"]
)

ai_mae_width = (
    evaluation["mae"]
    / mae_max
    * 100
)

base_mae_width = (
    baseline["mae"]
    / mae_max
    * 100
)

left, right = st.columns(2)

with left:

    st.html(f"""
        <div class="benchmark-card">

            <div class="benchmark-label">
                MAE · Lower is better
            </div>

            <div class="benchmark-value">
                {evaluation["mae"]:.3f}
            </div>

            <div class="benchmark-sub">
                {ai_name}
                ·
                <span class="benchmark-win">
                    {improvement_mae:.1f}% lower error
                </span>
            </div>

            <div class="bar-bg">
                <div class="bar-ai"
                     style="width:{ai_mae_width:.1f}%;">
                </div>
            </div>

            <div class="benchmark-sub">
                Baseline {baseline["mae"]:.3f}
            </div>

            <div class="bar-bg">
                <div class="bar-base"
                     style="width:{base_mae_width:.1f}%;">
                </div>
            </div>

        </div>
        """)


with right:

    rmse_max = max(
        baseline["rmse"],
        evaluation["rmse"]
    )

    ai_rmse_width = (
        evaluation["rmse"]
        / rmse_max
        * 100
    )

    base_rmse_width = (
        baseline["rmse"]
        / rmse_max
        * 100
    )

    st.html(f"""
        <div class="benchmark-card">

            <div class="benchmark-label">
                RMSE · Lower is better
            </div>

            <div class="benchmark-value">
                {evaluation["rmse"]:.3f}
            </div>

            <div class="benchmark-sub">
                {ai_name}
                ·
                <span class="benchmark-win">
                    {rmse_improvement:.1f}% lower error
                </span>
            </div>

            <div class="bar-bg">
                <div class="bar-ai"
                     style="width:{ai_rmse_width:.1f}%;">
                </div>
            </div>

            <div class="benchmark-sub">
                Baseline {baseline["rmse"]:.3f}
            </div>

            <div class="bar-bg">
                <div class="bar-base"
                     style="width:{base_rmse_width:.1f}%;">
                </div>
            </div>

        </div>
        """)


# R2 benchmark

r2_left, r2_right = st.columns([1, 1])

with r2_left:

    st.html(f"""
        <div class="benchmark-card">

            <div class="benchmark-label">
                R² · Higher is better
            </div>

            <div class="benchmark-value">
                {evaluation["r2"]:.3f}
            </div>

            <div class="benchmark-sub">
                Baseline: {baseline["r2"]:.3f}
            </div>

            <div class="benchmark-sub benchmark-win">
                +{r2_gain:.3f} absolute improvement
            </div>

        </div>
        """)


with r2_right:

    st.html(f"""
        <div class="interpretation-box">

        <b>Benchmark conclusion</b><br><br>

        The AI Demand Model reduces average forecast error
        by <b>{improvement_mae:.1f}%</b> against the lag-1 baseline
        and improves R² from <b>{baseline["r2"]:.3f}</b>
        to <b>{evaluation["r2"]:.3f}</b>.

        </div>
        """)


# ============================================================
# TECHNICAL BENCHMARK TABLE
# ============================================================

with st.expander(
    "Technical benchmark details"
):

    benchmark_df = pd.DataFrame(
        {
            "Model": [
                ai_name,
                baseline_name
            ],

            "Technical Model": [
                model["model_type"],
                baseline["model"]
            ],

            "MAE": [
                evaluation["mae"],
                baseline["mae"]
            ],

            "RMSE": [
                evaluation["rmse"],
                baseline["rmse"]
            ],

            "R²": [
                evaluation["r2"],
                baseline["r2"]
            ]
        }
    )

    st.dataframe(
        benchmark_df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# EXPLAINABILITY
# ============================================================

st.divider()

st.markdown("## Predictive Explainability")

st.caption(
    "Permutation importance measured on held-out observations "
    "using negative mean absolute error."
)

importance_df = pd.DataFrame(
    importance_payload["features"]
).sort_values(
    "rank"
)

max_importance = max(
    importance_df["importance_mean"].max(),
    0.000001
)

for _, row in importance_df.iterrows():

    value = max(
        float(row["importance_mean"]),
        0
    )

    width = (
        value
        / max_importance
        * 100
    )

    st.html(f"""
        <div class="feature-row">

            <div class="feature-name">
                #{int(row["rank"])}
                &nbsp;
                {row["feature"]}
            </div>

            <div class="feature-bg">
                <div
                    class="feature-fill"
                    style="width:{width:.1f}%;">
                </div>
            </div>

            <div class="feature-value">
                {row["importance_mean"]:.4f}
            </div>

        </div>
        """)


top_feature = importance_df.iloc[0]

st.html(f"""
    <div class="interpretation-box">

    <b>What drives the forecast?</b><br><br>

    <b>{top_feature["feature"]}</b> is currently the strongest
    predictive feature. Overall, recent demand history and rolling
    demand signals contribute most strongly to forecasting accuracy.

    </div>
    """)


with st.expander(
    "Explainability methodology"
):

    st.write(
        """
        Permutation importance measures how much model performance
        deteriorates when a feature is randomly shuffled.

        A larger value means the model relies more heavily on that
        feature for predictive accuracy.
        """
    )

    st.warning(
        """
        Predictive importance is not causal importance.
        Correlated lag and rolling-demand variables can share
        predictive information.
        """
    )


# ============================================================
# FEATURE INVENTORY
# ============================================================

st.divider()

st.markdown("## Production Feature Set")

feature_groups = {
    "Demand History": [
        "demand_lag_1",
        "demand_lag_7",
        "rolling_mean_7",
        "rolling_mean_28"
    ],

    "Pricing": [
        "sell_price"
    ],

    "Calendar": [
        "day_of_week",
        "month",
        "year"
    ]
}

cols = st.columns(3)

for col, (group, features) in zip(
    cols,
    feature_groups.items()
):

    with col:

        st.markdown(
            f"### {group}"
        )

        for feature in features:

            if feature in model["features"]:

                st.write(
                    f"✓ {feature}"
                )


# ============================================================
# GOVERNANCE
# ============================================================

st.divider()

st.markdown("## Model Governance")

governance_copy = {
    "pricing_guardrails":
        (
            "Pricing Guardrails",
            "Limits automated price movement."
        ),

    "human_review":
        (
            "Human Review",
            "Routes uncertain decisions for validation."
        ),

    "elasticity_validation":
        (
            "Elasticity Validation",
            "Checks economic coherence before automation."
        ),

    "profit_guardrail":
        (
            "Profit Protection",
            "Protects against uneconomic price decisions."
        )
}

gcols = st.columns(4)

for col, (key, content) in zip(
    gcols,
    governance_copy.items()
):

    title, copy = content

    enabled = model[
        "governance"
    ].get(
        key,
        False
    )

    with col:

        if enabled:

            st.html(f"""
                <div class="governance-card">

                    <div class="governance-title">
                        ✓ {title}
                    </div>

                    <div class="governance-copy">
                        {copy}
                    </div>

                </div>
                """)

        else:

            st.error(
                title
            )


# ============================================================
# VALIDATION / LIMITATIONS
# ============================================================

st.divider()

st.markdown("## Validation Framework")

v1, v2 = st.columns(2)

with v1:

    st.html(f"""
        <div class="interpretation-box">

        <b>Evaluation design</b><br><br>

        {evaluation["test_strategy"]}.<br><br>

        A chronological holdout is used instead of a random split
        to reduce temporal leakage and better reflect a real
        forecasting workflow.

        </div>
        """)


with v2:

    st.warning(
        """
        The current evaluation uses lag-based one-step-ahead
        predictions.

        Results should not be interpreted as a fully recursive
        28-day forecasting experiment.
        """
    )


st.caption(
    "AI Demand & Pricing Engine · Model Intelligence Layer"
)
