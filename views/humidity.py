import streamlit as st
import pandas as pd
from utils import get_range, line_chart

HUM_SENSORS = ["CBT1_humidity", "CBT2_humidity", "CBT3A_humidity", "CBT3B_humidity"]
TEMP_LABELS = ["CBT1", "CBT2", "CBT3A", "CBT3B"]


def render(df, last, alerts, THRESH):
    st.title("💧 Humidity Analysis")

    st.markdown("### Current Readings")
    cols = st.columns(4)
    for col, s, l in zip(cols, HUM_SENSORS, TEMP_LABELS):
        val = last[s]
        status = "🟡" if val < THRESH["hum_dry"] or val > THRESH["hum_mold"] else "🟢"
        col.metric(f"{status} {l}", f"{round(val)}%")

    tab1, tab2, tab3 = st.tabs(["24 Hours", "3 Days", "7 Days"])
    for tab, days in zip([tab1, tab2, tab3], [1, 3, 7]):
        with tab:
            df_r = get_range(df, days)
            st.plotly_chart(line_chart(df_r, HUM_SENSORS, TEMP_LABELS,
                "Humidity — All Sensors", "%"), width='stretch')

    st.markdown("### 7-Day Statistics")
    st.dataframe(pd.DataFrame({
        "Sensor":     TEMP_LABELS,
        "Min (%)":    [round(df[s].min()) for s in HUM_SENSORS],
        "Max (%)":    [round(df[s].max()) for s in HUM_SENSORS],
        "Avg (%)":    [round(df[s].mean()) for s in HUM_SENSORS],
        "Current (%)":[round(last[s]) for s in HUM_SENSORS],
    }), width='stretch', hide_index=True)