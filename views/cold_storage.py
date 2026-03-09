import streamlit as st
from utils import get_range, line_chart


def render(df, last, alerts, THRESH):
    st.title("❄️ Cold Storage Monitoring")

    cs_val = last["cold_storage_temp"]
    cs_hum = last["cold_storage_humidity"]

    cs_cls = "critical" if (cs_val < THRESH["cold_too_cold"] or cs_val > THRESH["cold_too_warm"]) \
             else ("warning" if cs_val > THRESH["cold_warm_warn"] else "")
    cs_val_color = "#e74c3c" if cs_cls == "critical" else ("#f39c12" if cs_cls == "warning" else "#ffffff")
    cs_border    = "#e74c3c" if cs_cls == "critical" else ("#f39c12" if cs_cls == "warning" else "#2ecc71")

    st.markdown(f"""
    <div class="sensor-card" style="border-top-color:{cs_border};">
        <div class="sensor-name">Cold Storage</div>
        <div style="display:flex; justify-content:space-around; align-items:flex-start; margin-top:8px;">
            <div style="text-align:center;">
                <div class="reading-value" style="color:{cs_val_color};">{cs_val:.1f}°F</div>
                <div class="reading-label">Temp</div>
            </div>
            <div style="text-align:center;">
                <div class="reading-value">{round(cs_hum)}%</div>
                <div class="reading-label">Humidity</div>
            </div>
            <div style="text-align:center;">
                <div class="reading-value">100%</div>
                <div class="reading-label">Battery</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("###")
    tab1, tab2, tab3 = st.tabs(["24 Hours", "3 Days", "7 Days"])
    for tab, days in zip([tab1, tab2, tab3], [1, 3, 7]):
        with tab:
            df_r = get_range(df, days)
            fig = line_chart(df_r, ["cold_storage_temp"], ["Cold Storage"],
                             "Cold Storage Temperature History", "°F")
            fig.add_hline(y=THRESH["cold_warm_warn"], line_dash="dash",
                          line_color="#f39c12", annotation_text="Warn")
            fig.add_hline(y=THRESH["cold_too_warm"], line_dash="dash",
                          line_color="#e74c3c", annotation_text="Critical")
            st.plotly_chart(fig, width='stretch')