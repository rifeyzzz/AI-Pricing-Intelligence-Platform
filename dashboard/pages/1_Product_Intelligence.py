
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
    page_title="Product Intelligence",
    page_icon="◇",
    layout="wide"
)

st.title("Product Intelligence")
st.caption(
    "Explore SKU-level price sensitivity and demand characteristics."
)

@st.cache_data
def load_data():
    return pd.read_csv(DATA_FILE)

df = load_data()

item_id = st.selectbox(
    "Select Product",
    sorted(df["item_id"].unique())
)

product = df[
    df["item_id"] == item_id
].iloc[0]

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Elasticity",
    f"{product['elasticity']:.3f}"
)

c2.metric(
    "Classification",
    product["classification"]
)

c3.metric(
    "Average Price",
    f"{product['avg_price']:.2f}"
)

c4.metric(
    "Average Demand",
    f"{product['avg_demand']:.2f}"
)

st.divider()

left, right = st.columns(2)

with left:

    st.subheader("Historical Support")

    st.metric(
        "Observations",
        f"{int(product['observations']):,}"
    )

    st.metric(
        "Unique Prices",
        int(product["unique_prices"])
    )

with right:

    st.subheader("Interpretation")

    elasticity = product["elasticity"]

    if product["classification"] == "Investigate":

        st.warning(
            "Manual Review Required"
        )

        st.write(
            """
            The observed price-demand relationship is not considered
            sufficiently reliable for automated repricing.
            """
        )

    elif elasticity <= -1:

        st.success("Price-Sensitive Product")

        st.write(
            """
            Demand is relatively elastic. Price increases may result
            in proportionally larger demand reductions.
            """
        )

    else:

        st.success("Relatively Price-Inelastic")

        st.write(
            """
            Historical demand appears comparatively resistant to
            moderate price changes.
            """
        )

st.divider()

st.subheader("Raw Product Model Record")

st.dataframe(
    df[df["item_id"] == item_id],
    use_container_width=True,
    hide_index=True
)
