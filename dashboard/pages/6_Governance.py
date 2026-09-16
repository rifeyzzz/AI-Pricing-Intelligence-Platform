
import streamlit as st
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_FILE = (
    BASE_DIR
    / "data"
    / "master_product_elasticities.csv"
)

st.set_page_config(
    page_title="AI Governance",
    page_icon="◇",
    layout="wide"
)

st.title("AI Governance & Human Review")

st.caption(
    "Decision safeguards around automated pricing recommendations."
)

df = pd.read_csv(DATA_FILE)

investigate = df[
    df["classification"] == "Investigate"
]

safe = df[
    df["classification"] != "Investigate"
]

c1, c2, c3 = st.columns(3)

c1.metric(
    "Total Products",
    len(df)
)

c2.metric(
    "Auto Eligible",
    len(safe)
)

c3.metric(
    "Manual Review",
    len(investigate)
)

st.divider()

st.subheader(
    "Decision Policy"
)

st.markdown(
"""
### AUTO_RECOMMEND

Allowed when the product-level elasticity is economically
coherent and sufficient historical support exists.

### MANUAL_REVIEW

Triggered when the elasticity estimate is classified as
**Investigate**.

The system therefore separates:

**model prediction → decision recommendation → human authorization**

rather than treating every statistical output as an
automatic business decision.
"""
)

st.divider()

st.subheader(
    "Products Requiring Review"
)

st.dataframe(
    investigate[
        [
            "item_id",
            "elasticity",
            "avg_price",
            "avg_demand",
            "observations",
            "unique_prices"
        ]
    ],
    use_container_width=True,
    hide_index=True
)

st.warning(
    """
    Elasticity estimates are observational rather than causal.
    Promotions, seasonality, lifecycle effects and other
    confounders may influence both price and demand.
    """
)
