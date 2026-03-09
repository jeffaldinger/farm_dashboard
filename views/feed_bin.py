import streamlit as st
from utils import get_range, line_chart


def render(df, last, alerts, THRESH):
    st.title("🌾 Feed Bin Level")

    fb_val  = last["feed_bin_level"]
    fb_dist = last["feed_bin_distance"]

    fb_cls = "critical" if fb_val < THRESH["bin_critical"] \
             else ("warning" if fb_val < THRESH["bin_low"] else "")
    fb_val_color = "#e74c3c" if fb_cls == "critical" else ("#f39c12" if fb_cls == "warning" else "#ffffff")
    fb_border    = "#e74c3c" if fb_cls == "critical" else ("#f39c12" if fb_cls == "warning" else "#2ecc71")

    st.markdown(f"""
    <div class="sensor-card" style="border-top-color:{fb_border};">
        <div class="sensor-name">Feed Bin</div>
        <div style="display:flex; justify-content:space-around; align-items:flex-start; margin-top:8px;">
            <div style="text-align:center;">
                <div class="reading-value" style="color:{fb_val_color};">{round(fb_val)}%</div>
                <div class="reading-label">Current Level</div>
            </div>
            <div style="text-align:center;">
                <div class="reading-value">{fb_dist:.1f}cm</div>
                <div class="reading-label">Distance to Fill</div>
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
            fig = line_chart(df_r, ["feed_bin_level"], ["Feed Bin"],
                             "Feed Bin Level History", "%")
            fig.add_hline(y=THRESH["bin_low"], line_dash="dash",
                          line_color="#f39c12", annotation_text="Low Warning")
            fig.add_hline(y=THRESH["bin_critical"], line_dash="dash",
                          line_color="#e74c3c", annotation_text="Critical")
            st.plotly_chart(fig, width='stretch')