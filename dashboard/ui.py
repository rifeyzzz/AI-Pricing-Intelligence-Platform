
import streamlit as st


# ============================================================
# PRODUCT LABELS
# ============================================================

def friendly_product_name(item_id):
    """
    Convert technical M5 IDs into cleaner business-facing labels
    without inventing product information.
    """

    if not isinstance(item_id, str):
        return str(item_id)

    parts = item_id.split("_")

    if len(parts) >= 3:

        category = parts[0].title()
        family = parts[1]
        sku = parts[2]

        return f"{category} · SKU {family}-{sku}"

    return item_id


def product_label_with_id(item_id):
    return f"{friendly_product_name(item_id)}  ·  {item_id}"


# ============================================================
# GLOBAL PROFESSIONAL STYLING
# ============================================================

def apply_professional_style():

    st.markdown(
        """
        <style>

        /* Main application */
        .block-container {
            max-width: 1450px;
            padding-top: 2.2rem;
            padding-bottom: 4rem;
        }


        /* Main headings */
        h1 {
            font-size: 2.25rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.035em !important;
        }

        h2 {
            font-size: 1.45rem !important;
            font-weight: 650 !important;
            letter-spacing: -0.02em !important;
            margin-top: 1.8rem !important;
        }

        h3 {
            font-size: 1.05rem !important;
            font-weight: 650 !important;
        }


        /* KPI cards */
        div[data-testid="stMetric"] {
            background: rgba(248, 250, 252, 0.72);
            border: 1px solid rgba(148, 163, 184, 0.24);
            padding: 1.15rem 1.25rem;
            border-radius: 14px;
            min-height: 122px;
        }

        div[data-testid="stMetricLabel"] {
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.025em;
            color: #64748b;
        }

        div[data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 650;
            letter-spacing: -0.035em;
        }


        /* Tables */
        div[data-testid="stDataFrame"] {
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 12px;
            overflow: hidden;
        }


        /* Inputs */
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div {
            border-radius: 10px;
        }


        /* Buttons */
        div.stButton > button {
            border-radius: 10px;
            font-weight: 600;
            min-height: 44px;
        }


        /* Info / success / warning containers */
        div[data-testid="stAlert"] {
            border-radius: 12px;
        }


        /* Sidebar */
        section[data-testid="stSidebar"] {
            border-right: 1px solid rgba(148, 163, 184, 0.16);
        }

        </style>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# SECTION HEADER
# ============================================================

def section_header(title, subtitle=None):

    st.markdown(f"## {title}")

    if subtitle:
        st.caption(subtitle)


# ============================================================
# BUSINESS MODEL NAMES
# ============================================================

def clean_model_name(model_name):

    mapping = {
        "HistGradientBoostingRegressor":
            "AI Demand Model",

        "Lag-1 Naive Forecast":
            "Baseline Forecast"
    }

    return mapping.get(
        model_name,
        model_name
    )
