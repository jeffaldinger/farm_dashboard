import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime, timedelta

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FarmSense Dashboard",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
CSS_PATH = os.path.join(os.path.dirname(__file__), "styles.css")
with open(CSS_PATH) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Data ───────────────────────────────────────────────────────────────────────
DATA_DIR    = os.path.join(os.path.dirname(__file__), "data")
SENSORS_CSV = os.path.join(DATA_DIR, "sensors.csv")
LATEST_CSV  = os.path.join(DATA_DIR, "latest.csv")

@st.cache_data(ttl=300)
def load_data():
    if not os.path.exists(SENSORS_CSV):
        st.error("⚠️ Data files not found. Please run: `python data/generate.py`")
        st.stop()
    df     = pd.read_csv(SENSORS_CSV, parse_dates=["timestamp"])
    latest = pd.read_csv(LATEST_CSV,  parse_dates=["timestamp"]).iloc[0]
    return df, latest

df, last = load_data()

# ── Constants ──────────────────────────────────────────────────────────────────
THRESH = {
    "temp_freeze": 32, "temp_frost": 36, "temp_heat": 85, "temp_extreme": 95,
    "hum_dry": 40, "hum_mold": 85,
    "cold_too_cold": 32, "cold_warm_warn": 40, "cold_too_warm": 45,
    "bin_low": 25, "bin_critical": 15,
}

TEMP_SENSORS = ["CBT1_temp",     "CBT2_temp",     "CBT3A_temp",    "CBT3B_temp"]
HUM_SENSORS  = ["CBT1_humidity", "CBT2_humidity", "CBT3A_humidity","CBT3B_humidity"]
TEMP_LABELS  = ["CBT1", "CBT2", "CBT3A", "CBT3B"]

# ── Alerts ─────────────────────────────────────────────────────────────────────
def check_alerts(row):
    alerts = []
    for s, l in zip(TEMP_SENSORS, TEMP_LABELS):
        t = row[s]
        if t < THRESH["temp_freeze"]:    alerts.append(("CRITICAL", f"{l} — Freezing! {t:.1f}°F"))
        elif t < THRESH["temp_frost"]:   alerts.append(("WARNING",  f"{l} — Frost warning {t:.1f}°F"))
        elif t > THRESH["temp_extreme"]: alerts.append(("CRITICAL", f"{l} — Extreme heat {t:.1f}°F"))
        elif t > THRESH["temp_heat"]:    alerts.append(("WARNING",  f"{l} — Heat warning {t:.1f}°F"))
    for s, l in zip(HUM_SENSORS, TEMP_LABELS):
        h = row[s]
        if h < THRESH["hum_dry"]:    alerts.append(("WARNING", f"{l} humidity — Too dry {h:.1f}%"))
        elif h > THRESH["hum_mold"]: alerts.append(("WARNING", f"{l} humidity — Mold risk {h:.1f}%"))
    cs = row["cold_storage_temp"]
    if cs < THRESH["cold_too_cold"]:    alerts.append(("CRITICAL", f"Cold Storage — Too cold {cs:.1f}°F"))
    elif cs > THRESH["cold_too_warm"]:  alerts.append(("CRITICAL", f"Cold Storage — Too warm {cs:.1f}°F"))
    elif cs > THRESH["cold_warm_warn"]: alerts.append(("WARNING",  f"Cold Storage — Warming up {cs:.1f}°F"))
    fb = row["feed_bin_level"]
    if fb < THRESH["bin_critical"]:     alerts.append(("CRITICAL", f"Feed Bin — Refill immediately! {fb:.1f}%"))
    elif fb < THRESH["bin_low"]:        alerts.append(("WARNING",  f"Feed Bin — Running low {fb:.1f}%"))
    if row["water_leak"] > 0:           alerts.append(("CRITICAL", "Water leak detected!"))
    return alerts

alerts = check_alerts(last)

# ── Sidebar ────────────────────────────────────────────────────────────────────
NAV_PAGES = [
    "📊 Overview",
    "🌡️ Temperature",
    "💧 Humidity",
    "🚰 Water Leak",
    "❄️ Cold Storage",
    "🌾 Feed Bin",
    "⚠️ Alerts",
    "⚙️ Sensor Status",
    "🎚️ Thresholds",
    "🤖 AI Chat",
]

if "page" not in st.session_state:
    st.session_state.page = "📊 Overview"

with st.sidebar:
    st.markdown("## 🌾 FarmSense")
    st.markdown("**Sensor Monitoring Dashboard**")
    st.markdown("---")
    for nav_item in NAV_PAGES:
        label = f"• {nav_item}" if st.session_state.page == nav_item else nav_item
        if st.button(label, key=f"nav_{nav_item}", width='stretch'):
            st.session_state.page = nav_item
            st.rerun()
    st.markdown("---")
    with st.expander("📥 Export Data"):
        start = st.date_input("Start Date", value=(datetime.now() - timedelta(days=7)).date())
        end   = st.date_input("End Date",   value=datetime.now().date())
        df_export = df[(df["timestamp"].dt.date >= start) & (df["timestamp"].dt.date <= end)]
        csv = df_export.to_csv(index=False).encode()
        st.download_button("⬇️ Download CSV", csv, "farmsense_export.csv", "text/csv")

page = st.session_state.page

# ── Routing ────────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from views import overview, temperature, humidity, water_leak, cold_storage, feed_bin, alerts as alerts_view, sensor_status, thresholds, ai_chat

ROUTES = {
    "📊 Overview":      overview,
    "🌡️ Temperature":  temperature,
    "💧 Humidity":      humidity,
    "🚰 Water Leak":    water_leak,
    "❄️ Cold Storage":  cold_storage,
    "🌾 Feed Bin":      feed_bin,
    "⚠️ Alerts":        alerts_view,
    "⚙️ Sensor Status": sensor_status,
    "🎚️ Thresholds":   thresholds,
    "🤖 AI Chat":       ai_chat,
}

ROUTES[page].render(df, last, alerts, THRESH)