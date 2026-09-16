
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Model Performance",
    page_icon="△",
    layout="wide"
)

st.title("Model Performance")

st.caption(
    "Validated forecasting performance on an unseen "
    "28-day future holdout period."
)

metrics = pd.DataFrame({
    "Model": [
        "Naive Lag-1",
        "HistGradientBoosting"
    ],
    "MAE": [
        1.348,
        1.092
    ],
    "RMSE": [
        2.761,
        2.034
    ],
    "R²": [
        0.411,
        0.680
    ]
})

c1, c2, c3 = st.columns(3)

c1.metric(
    "Test MAE",
    "1.092",
    delta="-19.0% vs baseline",
    delta_color="inverse"
)

c2.metric(
    "Test RMSE",
    "2.034",
    delta="-26.3% vs baseline",
    delta_color="inverse"
)

c3.metric(
    "Test R²",
    "0.680",
    delta="+0.269"
)

st.divider()

st.subheader(
    "Benchmark Comparison"
)

st.dataframe(
    metrics,
    use_container_width=True,
    hide_index=True
)

st.subheader(
    "MAE Comparison"
)

st.bar_chart(
    metrics.set_index("Model")[
        ["MAE"]
    ]
)

st.subheader(
    "RMSE Comparison"
)

st.bar_chart(
    metrics.set_index("Model")[
        ["RMSE"]
    ]
)

st.info(
    """
    The evaluation uses a chronological train/test split.
    The final 28 days were excluded from training and used
    as unseen future observations.
    """
)

st.warning(
    """
    Current lag-based evaluation represents a rolling
    one-step-ahead forecasting setup rather than a fully
    recursive 28-day forecast.
    """
)
