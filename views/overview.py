import streamlit as st
import numpy as np
from datetime import datetime, timedelta
from utils import get_range, line_chart, sensor_card

TEMP_SENSORS = ["CBT1_temp",     "CBT2_temp",     "CBT3A_temp",    "CBT3B_temp"]
HUM_SENSORS  = ["CBT1_humidity", "CBT2_humidity", "CBT3A_humidity","CBT3B_humidity"]
BAT_SENSORS  = ["CBT1_battery",  "CBT2_battery",  "CBT3A_battery", "CBT3B_battery"]
TEMP_LABELS  = ["CBT1", "CBT2", "CBT3A", "CBT3B"]


def render(df, last, alerts, THRESH):
    st.title("📊 Sensor Overview")

    # ── Alert banner ───────────────────────────────────────────────────────────
    if alerts:
        sev = "error" if any(a[0] == "CRITICAL" for a in alerts) else "warning"
        getattr(st, sev)(f"⚠️ {len(alerts)} active alert{'s' if len(alerts)!=1 else ''} — check the Alerts page")
    else:
        st.success("✅ All sensors nominal")

    # ── KPI row ────────────────────────────────────────────────────────────────
    cols = st.columns(6)
    for col, (label, value, icon) in zip(cols, [
        ("Avg Temperature",        f"{np.mean([last[s] for s in TEMP_SENSORS]):.1f}°F", "🌡️"),
        ("Avg Humidity",           f"{round(np.mean([last[s] for s in HUM_SENSORS]))}%", "☁️"),
        ("Water Leak (4 sensors)", "OK",                                                  "💧"),
        ("Cold Storage",           f"{last['cold_storage_temp']:.1f}°F",                 "❄️"),
        ("Feed Bin Level",         f"{round(last['feed_bin_level'])}%",                  "🌾"),
        ("Sensors Online",         "6/10",                                                "📡"),
    ]):
        col.metric(f"{icon} {label}", value)

    # ── Temperature & Humidity cards ───────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🌡️ Temperature & Humidity")
    card_cols = st.columns(4)
    for col, label, ts, hs, bs in zip(card_cols, TEMP_LABELS, TEMP_SENSORS, HUM_SENSORS, BAT_SENSORS):
        with col:
            st.markdown(sensor_card(label, last[ts], last[hs], last[bs], THRESH), unsafe_allow_html=True)

    # ── Water Leak cards ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🚰 Water Leak Detection")
    cbw_cols = st.columns(4)
    for col, name in zip(cbw_cols, ["CBW1", "CBW2", "CBW6", "CBW8"]):
        with col:
            st.markdown(f"""
            <div class="sensor-card" style="border-top-color:#4a5568;">
                <div class="sensor-name" style="color:#6a88a8;">{name} - Water Leak</div>
                <div style="display:flex; justify-content:space-around; align-items:flex-start; margin-top:8px;">
                    <div style="text-align:center;">
                        <div class="reading-value" style="color:#4a5568;">--</div>
                        <div class="reading-label">Water Leak</div>
                    </div>
                    <div style="text-align:center;">
                        <div class="reading-value" style="color:#4a5568;">--%</div>
                        <div class="reading-label">Battery</div>
                    </div>
                </div>
                <div class="reading-label" style="text-align:center; margin-top:10px;">No recent data</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Cold Storage & Feed Bin cards ──────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ❄️ Cold Storage & Feed Bin")

    cs_val  = last["cold_storage_temp"]
    cs_hum  = last["cold_storage_humidity"]
    fb_val  = last["feed_bin_level"]
    fb_dist = last["feed_bin_distance"]

    cs_cls = "critical" if (cs_val < THRESH["cold_too_cold"] or cs_val > THRESH["cold_too_warm"]) \
             else ("warning" if cs_val > THRESH["cold_warm_warn"] else "")
    fb_cls = "critical" if fb_val < THRESH["bin_critical"] \
             else ("warning" if fb_val < THRESH["bin_low"] else "")

    cs_val_color = "#e74c3c" if cs_cls == "critical" else ("#f39c12" if cs_cls == "warning" else "#ffffff")
    fb_val_color = "#e74c3c" if fb_cls == "critical" else ("#f39c12" if fb_cls == "warning" else "#ffffff")
    cs_border    = "#e74c3c" if cs_cls == "critical" else ("#f39c12" if cs_cls == "warning" else "#2ecc71")
    fb_border    = "#e74c3c" if fb_cls == "critical" else ("#f39c12" if fb_cls == "warning" else "#2ecc71")

    last_ts     = last["timestamp"]
    total_mins  = int((datetime.now() - last_ts).total_seconds() // 60)
    if total_mins < 60:
        last_updated = f"Last updated {total_mins}m ago"
    else:
        hrs = total_mins // 60
        mins = total_mins % 60
        last_updated = f"Last updated {hrs}h {mins}m ago" if mins else f"Last updated {hrs}h ago"

    box_c1, box_c2 = st.columns(2)
    with box_c1:
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
            <div style="color:#6a88a8; font-size:11px; text-align:left; margin-top:12px;">{last_updated}</div>
        </div>
        """, unsafe_allow_html=True)
    with box_c2:
        st.markdown(f"""
        <div class="sensor-card" style="border-top-color:{fb_border};">
            <div class="sensor-name">Feed Bin</div>
            <div style="display:flex; justify-content:space-around; align-items:flex-start; margin-top:8px;">
                <div style="text-align:center;">
                    <div class="reading-value" style="color:{fb_val_color};">{round(fb_val)}%</div>
                    <div class="reading-label">Level</div>
                </div>
                <div style="text-align:center;">
                    <div class="reading-value">{fb_dist:.1f}cm</div>
                    <div class="reading-label">Distance</div>
                </div>
                <div style="text-align:center;">
                    <div class="reading-value">100%</div>
                    <div class="reading-label">Battery</div>
                </div>
            </div>
            <div style="color:#6a88a8; font-size:11px; text-align:left; margin-top:12px;">{last_updated}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Trend charts ───────────────────────────────────────────────────────────
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["24 Hours", "3 Days", "7 Days"])
    for tab, days in zip([tab1, tab2, tab3], [1, 3, 7]):
        with tab:
            df_r = get_range(df, days)
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(line_chart(df_r, TEMP_SENSORS, TEMP_LABELS, "Temperature Trend", "°F"),
                                width='stretch')
            with c2:
                st.plotly_chart(line_chart(df_r, HUM_SENSORS, TEMP_LABELS, "Humidity Trend", "%"),
                                width='stretch')