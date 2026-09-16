
import sys
from pathlib import Path

import altair as alt
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
    friendly_product_name
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Portfolio Opportunities",
    page_icon="◈",
    layout="wide"
)

apply_professional_style()

API_URL = "http://127.0.0.1:8001"


# ============================================================
# PAGE-SPECIFIC STYLE
# ============================================================

st.html(
    """
    <style>

    .portfolio-hero {
        padding: 0.8rem 0 1.6rem 0;
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
        font-weight: 750;
        letter-spacing: -0.045em;
        color: #0f172a;
        line-height: 1.08;
    }

    .hero-copy {
        max-width: 850px;
        margin-top: 0.7rem;
        color: #64748b;
        line-height: 1.55;
    }

    .opportunity-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.15rem 1.25rem;
        min-height: 140px;
    }

    .card-label {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #64748b;
    }

    .card-value {
        font-size: 2rem;
        font-weight: 730;
        letter-spacing: -0.04em;
        color: #0f172a;
        margin-top: 0.25rem;
    }

    .card-sub {
        font-size: 0.78rem;
        color: #64748b;
        margin-top: 0.35rem;
    }

    .positive {
        color: #15803d;
        font-weight: 700;
    }

    .action-increase {
        display: inline-block;
        background: #ecfdf5;
        color: #166534;
        border: 1px solid #bbf7d0;
        border-radius: 999px;
        padding: 0.25rem 0.55rem;
        font-size: 0.72rem;
        font-weight: 700;
    }

    .action-decrease {
        display: inline-block;
        background: #fff7ed;
        color: #9a3412;
        border: 1px solid #fed7aa;
        border-radius: 999px;
        padding: 0.25rem 0.55rem;
        font-size: 0.72rem;
        font-weight: 700;
    }

    .insight-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1.1rem 1.2rem;
        line-height: 1.55;
    }

    </style>
    """
)


# ============================================================
# API
# ============================================================

@st.cache_data(ttl=300)
def load_portfolio(
    top_n=20,
    max_change_pct=0.10
):

    response = requests.get(
        f"{API_URL}/portfolio-opportunities",
        params={
            "top_n": top_n,
            "max_change_pct": max_change_pct
        },
        timeout=90
    )

    response.raise_for_status()

    return response.json()


try:

    payload = load_portfolio(
        top_n=20,
        max_change_pct=0.10
    )

except requests.exceptions.ConnectionError:

    st.error(
        "FastAPI backend is offline. "
        "Start the backend on port 8001."
    )

    st.stop()

except Exception as e:

    st.error(
        f"Unable to load portfolio opportunities: {e}"
    )

    st.stop()


df = pd.DataFrame(
    payload["opportunities"]
)

summary = payload["summary"]


if df.empty:

    st.warning(
        "No eligible pricing opportunities were returned."
    )

    st.stop()


# ============================================================
# CLEAN BUSINESS LABELS
# ============================================================

df["product"] = (
    df["item_id"]
    .apply(friendly_product_name)
)

df["action"] = df.apply(
    lambda row:
        "Increase"
        if row["recommended_price"]
        > row["current_price"]
        else "Decrease"
        if row["recommended_price"]
        < row["current_price"]
        else "Hold",
    axis=1
)


# ============================================================
# HERO
# ============================================================

st.html(
    """
    <div class="portfolio-hero">

        <div class="eyebrow">
            Portfolio intelligence
        </div>

        <div class="hero-title">
            Pricing Opportunity Radar
        </div>

        <div class="hero-copy">
            Portfolio-level prioritization of automated pricing
            opportunities using demand forecasts, elasticity estimates
            and commercial pricing guardrails.
        </div>

    </div>
    """
)


# ============================================================
# FILTERS
# ============================================================

st.markdown("## Opportunity Filters")

f1, f2, f3 = st.columns(
    [1.2, 1, 1]
)

with f1:

    classifications = (
        ["All"]
        +
        sorted(
            df["classification"]
            .dropna()
            .unique()
            .tolist()
        )
    )

    classification_filter = st.selectbox(
        "Elasticity Segment",
        classifications
    )


with f2:

    min_uplift = st.slider(
        "Minimum Revenue Uplift",
        min_value=0.0,
        max_value=float(
            max(
                20.0,
                round(
                    df[
                        "expected_revenue_uplift_pct"
                    ].max(),
                    1
                )
            )
        ),
        value=0.0,
        step=0.5,
        format="%.1f%%"
    )


with f3:

    top_n = st.slider(
        "Show Top Opportunities",
        min_value=5,
        max_value=len(df),
        value=min(
            10,
            len(df)
        )
    )


filtered = df.copy()

if classification_filter != "All":

    filtered = filtered[
        filtered["classification"]
        == classification_filter
    ]


filtered = filtered[
    filtered[
        "expected_revenue_uplift_pct"
    ] >= min_uplift
]


filtered = (
    filtered
    .sort_values(
        "expected_revenue_gain",
        ascending=False
    )
    .head(top_n)
    .copy()
)


# ============================================================
# EXECUTIVE KPIs
# ============================================================

st.divider()

st.markdown("## Executive Portfolio KPIs")

total_gain = (
    filtered[
        "expected_revenue_gain"
    ].sum()
    if not filtered.empty
    else 0
)

average_uplift = (
    filtered[
        "expected_revenue_uplift_pct"
    ].mean()
    if not filtered.empty
    else 0
)

largest_gain = (
    filtered[
        "expected_revenue_gain"
    ].max()
    if not filtered.empty
    else 0
)

increase_count = int(
    (
        filtered["action"]
        == "Increase"
    ).sum()
)

decrease_count = int(
    (
        filtered["action"]
        == "Decrease"
    ).sum()
)


k1, k2, k3, k4 = st.columns(4)


with k1:

    st.html(
        f"""
        <div class="opportunity-card">

            <div class="card-label">
                Priority Opportunities
            </div>

            <div class="card-value">
                {len(filtered)}
            </div>

            <div class="card-sub">
                Highest-ranked eligible SKUs
            </div>

        </div>
        """
    )


with k2:

    st.html(
        f"""
        <div class="opportunity-card">

            <div class="card-label">
                Expected Revenue Gain
            </div>

            <div class="card-value">
                {total_gain:.2f}
            </div>

            <div class="card-sub positive">
                Portfolio opportunity value
            </div>

        </div>
        """
    )


with k3:

    st.html(
        f"""
        <div class="opportunity-card">

            <div class="card-label">
                Average Revenue Uplift
            </div>

            <div class="card-value">
                {average_uplift:.2f}%
            </div>

            <div class="card-sub">
                Across displayed opportunities
            </div>

        </div>
        """
    )


with k4:

    st.html(
        f"""
        <div class="opportunity-card">

            <div class="card-label">
                Largest Single Gain
            </div>

            <div class="card-value">
                {largest_gain:.2f}
            </div>

            <div class="card-sub">
                Best individual opportunity
            </div>

        </div>
        """
    )


# ============================================================
# TOP OPPORTUNITY
# ============================================================

if not filtered.empty:

    best = filtered.iloc[0]

    action = best["action"]

    action_html = (
        '<span class="action-increase">↑ Increase</span>'
        if action == "Increase"
        else
        '<span class="action-decrease">↓ Decrease</span>'
        if action == "Decrease"
        else
        "Hold"
    )


    st.divider()

    st.markdown(
        "## Highest-Priority Recommendation"
    )

    st.html(
        f"""
        <div class="insight-box">

            <b>{best["product"]}</b>
            &nbsp;&nbsp;
            {action_html}

            <br><br>

            Current price:
            <b>{best["current_price"]:.2f}</b>

            &nbsp;→&nbsp;

            Recommended:
            <b>{best["recommended_price"]:.2f}</b>

            <br><br>

            Estimated revenue uplift:
            <b>{best["expected_revenue_uplift_pct"]:.2f}%</b>

            &nbsp;·&nbsp;

            Expected revenue gain:
            <b>{best["expected_revenue_gain"]:.2f}</b>

            &nbsp;·&nbsp;

            Elasticity:
            <b>{best["elasticity"]:.3f}</b>

        </div>
        """
    )


# ============================================================
# OPPORTUNITY RANKING
# ============================================================

st.divider()

st.markdown(
    "## Opportunity Ranking"
)

st.caption(
    "Expected revenue gain by prioritized SKU."
)


ranking_chart = (
    alt.Chart(
        filtered
    )
    .mark_bar(
        cornerRadiusEnd=5
    )
    .encode(
        y=alt.Y(
            "product:N",
            sort="-x",
            title=None
        ),

        x=alt.X(
            "expected_revenue_gain:Q",
            title="Expected revenue gain"
        ),

        tooltip=[
            alt.Tooltip(
                "product:N",
                title="Product"
            ),

            alt.Tooltip(
                "item_id:N",
                title="Technical ID"
            ),

            alt.Tooltip(
                "current_price:Q",
                title="Current Price",
                format=".2f"
            ),

            alt.Tooltip(
                "recommended_price:Q",
                title="Recommended Price",
                format=".2f"
            ),

            alt.Tooltip(
                "expected_revenue_gain:Q",
                title="Revenue Gain",
                format=".2f"
            ),

            alt.Tooltip(
                "expected_revenue_uplift_pct:Q",
                title="Uplift",
                format=".2f"
            )
        ]
    )
    .properties(
        height=max(
            280,
            len(filtered) * 36
        )
    )
)

st.altair_chart(
    ranking_chart,
    use_container_width=True
)


# ============================================================
# REVENUE UPLIFT + PRICE CHANGE
# ============================================================

left, right = st.columns(2)


with left:

    st.markdown(
        "### Revenue Uplift"
    )

    uplift_chart = (
        alt.Chart(
            filtered
        )
        .mark_bar(
            cornerRadiusEnd=4
        )
        .encode(
            x=alt.X(
                "product:N",
                sort="-y",
                title=None
            ),

            y=alt.Y(
                "expected_revenue_uplift_pct:Q",
                title="Expected uplift (%)"
            ),

            tooltip=[
                "product:N",

                alt.Tooltip(
                    "expected_revenue_uplift_pct:Q",
                    title="Uplift",
                    format=".2f"
                )
            ]
        )
        .properties(
            height=330
        )
    )

    st.altair_chart(
        uplift_chart,
        use_container_width=True
    )


with right:

    st.markdown(
        "### Recommended Price Change"
    )

    change_chart = (
        alt.Chart(
            filtered
        )
        .mark_bar(
            cornerRadiusEnd=4
        )
        .encode(
            x=alt.X(
                "product:N",
                sort="-y",
                title=None
            ),

            y=alt.Y(
                "price_change_pct:Q",
                title="Price change (%)"
            ),

            tooltip=[
                "product:N",

                alt.Tooltip(
                    "price_change_pct:Q",
                    title="Price Change",
                    format=".2f"
                )
            ]
        )
        .properties(
            height=330
        )
    )

    st.altair_chart(
        change_chart,
        use_container_width=True
    )


# ============================================================
# CURRENT VS RECOMMENDED
# ============================================================

st.divider()

st.markdown(
    "## Current vs Recommended Price"
)


price_long = filtered[
    [
        "product",
        "current_price",
        "recommended_price"
    ]
].melt(
    id_vars="product",
    var_name="price_type",
    value_name="price"
)


price_long["price_type"] = (
    price_long["price_type"]
    .replace(
        {
            "current_price":
                "Current Price",

            "recommended_price":
                "Recommended Price"
        }
    )
)


price_chart = (
    alt.Chart(
        price_long
    )
    .mark_bar()
    .encode(
        x=alt.X(
            "product:N",
            title=None
        ),

        y=alt.Y(
            "price:Q",
            title="Price"
        ),

        xOffset="price_type:N",

        color=alt.Color(
            "price_type:N",
            title=None
        ),

        tooltip=[
            "product:N",
            "price_type:N",

            alt.Tooltip(
                "price:Q",
                format=".2f"
            )
        ]
    )
    .properties(
        height=380
    )
)

st.altair_chart(
    price_chart,
    use_container_width=True
)


# ============================================================
# EXECUTIVE TABLE
# ============================================================

st.divider()

st.markdown(
    "## Decision Table"
)


table = filtered[
    [
        "rank",
        "product",
        "item_id",
        "classification",
        "current_price",
        "recommended_price",
        "price_change_pct",
        "expected_revenue_gain",
        "expected_revenue_uplift_pct"
    ]
].copy()


table.columns = [
    "Rank",
    "Product",
    "Technical ID",
    "Elasticity Segment",
    "Current Price",
    "Recommended Price",
    "Price Change %",
    "Revenue Gain",
    "Revenue Uplift %"
]


st.dataframe(
    table,
    use_container_width=True,
    hide_index=True,

    column_config={

        "Current Price":
            st.column_config.NumberColumn(
                format="%.2f"
            ),

        "Recommended Price":
            st.column_config.NumberColumn(
                format="%.2f"
            ),

        "Price Change %":
            st.column_config.NumberColumn(
                format="%.2f%%"
            ),

        "Revenue Gain":
            st.column_config.NumberColumn(
                format="%.2f"
            ),

        "Revenue Uplift %":
            st.column_config.NumberColumn(
                format="%.2f%%"
            )
    }
)


# ============================================================
# PORTFOLIO INTERPRETATION
# ============================================================

st.divider()

st.markdown(
    "## Executive Interpretation"
)


if not filtered.empty:

    st.html(
        f"""
        <div class="insight-box">

        The current opportunity set contains
        <b>{len(filtered)}</b> priority SKUs.

        <br><br>

        <b>{increase_count}</b> recommendations imply a price increase
        and <b>{decrease_count}</b> imply a price decrease.

        The strongest identified opportunity is
        <b>{best["product"]}</b>, with an estimated revenue uplift of
        <b>{best["expected_revenue_uplift_pct"]:.2f}%</b>.

        </div>
        """
    )


st.caption(
    """
    Portfolio ranking reflects modeled revenue opportunity under
    pricing guardrails. Estimates are decision-support outputs,
    not guaranteed realized commercial outcomes.
    """
)
