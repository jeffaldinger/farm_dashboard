import streamlit as st
import pandas as pd
from utils import get_range, line_chart

TEMP_SENSORS = ["CBT1_temp", "CBT2_temp", "CBT3A_temp", "CBT3B_temp"]
TEMP_LABELS  = ["CBT1", "CBT2", "CBT3A", "CBT3B"]


def render(df, last, alerts, THRESH):
    st.title("🌡️ Temperature Analysis")

    st.markdown("### Current Readings")
    cols = st.columns(4)
    for col, s, l in zip(cols, TEMP_SENSORS, TEMP_LABELS):
        val = last[s]
        status = "🔴" if val < THRESH["temp_frost"] or val > THRESH["temp_heat"] else "🟢"
        col.metric(f"{status} {l}", f"{val:.1f}°F")

    tab1, tab2, tab3 = st.tabs(["24 Hours", "3 Days", "7 Days"])
    for tab, days in zip([tab1, tab2, tab3], [1, 3, 7]):
        with tab:
            df_r = get_range(df, days)
            st.plotly_chart(line_chart(df_r, TEMP_SENSORS, TEMP_LABELS,
                "Temperature — All Sensors", "°F"), width='stretch')

    st.markdown("### 7-Day Statistics")
    st.dataframe(pd.DataFrame({
        "Sensor":      TEMP_LABELS,
        "Min (°F)":    [round(df[s].min(), 1) for s in TEMP_SENSORS],
        "Max (°F)":    [round(df[s].max(), 1) for s in TEMP_SENSORS],
        "Avg (°F)":    [round(df[s].mean(), 1) for s in TEMP_SENSORS],
        "Current (°F)":[round(last[s], 1) for s in TEMP_SENSORS],
    }), width='stretch', hide_index=True)