import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import requests

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FarmSense Dashboard",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1a2332; }
    [data-testid="stSidebar"] * { color: #e0e6ef !important; }
    [data-testid="stSidebar"] a { text-decoration: none !important; }
    [data-testid="stSidebar"] a:hover { background:#243447 !important; color:#ffffff !important; }
    [data-testid="stSidebar"] .stButton button {
        background-color: transparent !important;
        border: none !important;
        text-align: left !important;
        box-shadow: none !important;
        color: #c0cfe0 !important;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #243447 !important;
        color: #ffffff !important;
        border: none !important;
    }
    [data-testid="stSidebar"] .stButton button:focus {
        box-shadow: none !important;
        border: none !important;
        outline: none !important;
    }
    .stApp { background-color: #111c2b; }
    h1, h2, h3, h4 { color: #e0e6ef; }
    p, li { color: #c0cfe0; }
    div[data-testid="stChatMessage"] { background: #1e2d3d; border-radius: 10px; margin: 4px 0; }

    .sensor-card {
        background: #1e2d3d;
        border-radius: 10px;
        padding: 16px 20px;
        border-top: 4px solid #2ecc71;
        text-align: center;
    }
    .sensor-card.warning { border-top-color: #f39c12; }
    .sensor-card.critical { border-top-color: #e74c3c; }
    .sensor-name {
        color: #8fa8c8;
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 12px;
    }
    .reading-label {
        color: #6a88a8;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 2px;
    }
    .reading-value {
        color: #ffffff;
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .reading-value.warn { color: #f39c12; }
    .reading-value.crit { color: #e74c3c; }
    .battery-bar-bg {
        background: #2a3f55;
        border-radius: 4px;
        height: 6px;
        margin-top: 4px;
    }
    .battery-bar-fill {
        border-radius: 4px;
        height: 6px;
    }
</style>
""", unsafe_allow_html=True)

# ── Load data from CSVs ────────────────────────────────────────────────────────
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

def get_range(df, days):
    cutoff = datetime.now() - timedelta(days=days)
    return df[df["timestamp"] >= cutoff]

TEMP_SENSORS = ["CBT1_temp",     "CBT2_temp",     "CBT3A_temp",    "CBT3B_temp"]
HUM_SENSORS  = ["CBT1_humidity", "CBT2_humidity", "CBT3A_humidity","CBT3B_humidity"]
BAT_SENSORS  = ["CBT1_battery",  "CBT2_battery",  "CBT3A_battery", "CBT3B_battery"]
TEMP_LABELS  = ["CBT1", "CBT2", "CBT3A", "CBT3B"]

THRESH = {
    "temp_freeze": 32, "temp_frost": 36, "temp_heat": 85, "temp_extreme": 95,
    "hum_dry": 40, "hum_mold": 85,
    "cold_too_cold": 32, "cold_warm_warn": 40, "cold_too_warm": 45,
    "bin_low": 25, "bin_critical": 15,
}

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

# ── Chart helpers ──────────────────────────────────────────────────────────────
COLORS = ["#2ecc71", "#3498db", "#e67e22", "#9b59b6"]

def line_chart(df_r, cols, labels, title, yaxis="°F"):
    fig = go.Figure()
    for col, lab, color in zip(cols, labels, COLORS):
        fig.add_trace(go.Scatter(
            x=df_r["timestamp"], y=df_r[col],
            name=lab, line=dict(color=color, width=2),
            hovertemplate=f"{lab}: %{{y:.1f}}{yaxis}<extra></extra>"
        ))
    fig.update_layout(
        title=title, paper_bgcolor="#1e2d3d", plot_bgcolor="#1e2d3d",
        font_color="#c0cfe0", legend=dict(bgcolor="#1e2d3d"),
        xaxis=dict(gridcolor="#2a3f55"),
        yaxis=dict(gridcolor="#2a3f55", title=yaxis),
        margin=dict(l=0, r=0, t=40, b=0), height=320,
    )
    return fig

def gauge_chart(value, title, min_val, max_val, unit, warn, crit):
    color = "#e74c3c" if value >= crit else ("#f39c12" if value >= warn else "#2ecc71")
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        title={"text": title, "font": {"color": "#c0cfe0"}},
        number={"suffix": unit, "font": {"color": "#ffffff"}},
        gauge={
            "axis": {"range": [min_val, max_val], "tickcolor": "#8fa8c8"},
            "bar": {"color": color}, "bgcolor": "#2a3f55", "bordercolor": "#2a3f55",
            "steps": [
                {"range": [min_val, warn], "color": "#1e2d3d"},
                {"range": [warn, crit],    "color": "#2c2414"},
                {"range": [crit, max_val], "color": "#2c1a1a"},
            ],
        }
    ))
    fig.update_layout(paper_bgcolor="#1e2d3d", font_color="#c0cfe0",
                      height=220, margin=dict(l=10, r=10, t=40, b=10))
    return fig

# ── Sensor card HTML ───────────────────────────────────────────────────────────
def sensor_card(label, temp, humidity, battery):
    if temp < THRESH["temp_freeze"] or temp > THRESH["temp_extreme"]:
        card_class = "sensor-card critical"
    elif temp < THRESH["temp_frost"] or temp > THRESH["temp_heat"] or humidity > THRESH["hum_mold"]:
        card_class = "sensor-card warning"
    else:
        card_class = "sensor-card"

    temp_cls = "crit" if (temp < THRESH["temp_freeze"] or temp > THRESH["temp_extreme"]) \
               else ("warn" if (temp < THRESH["temp_frost"] or temp > THRESH["temp_heat"]) else "")
    hum_cls  = "warn" if (humidity > THRESH["hum_mold"] or humidity < THRESH["hum_dry"]) else ""

    bat_pct   = int(battery)
    bat_color = "#e74c3c" if bat_pct < 20 else ("#f39c12" if bat_pct < 40 else "#2ecc71")

    return f"""
    <div class="{card_class}">
        <div class="sensor-name">{label} - Temp & Humidity</div>
        <div style="display:flex; justify-content:space-around; align-items:flex-start; margin-top:8px;">
            <div style="text-align:center;">
                <div class="reading-value {temp_cls}">{temp:.1f}°F</div>
                <div class="reading-label">Temperature</div>
            </div>
            <div style="text-align:center;">
                <div class="reading-value {hum_cls}">{round(humidity)}%</div>
                <div class="reading-label">Humidity</div>
            </div>
            <div style="text-align:center;">
                <div class="reading-value">{bat_pct}%</div>
                <div class="reading-label">Battery</div>
            </div>
        </div>
    </div>
    """

# ══════════════════════════════════════════════════════════════════════════════
# PAGES
# ══════════════════════════════════════════════════════════════════════════════

if page == "📊 Overview":
    st.title("📊 Sensor Overview")

    if alerts:
        sev = "error" if any(a[0] == "CRITICAL" for a in alerts) else "warning"
        getattr(st, sev)(f"⚠️ {len(alerts)} active alert{'s' if len(alerts)!=1 else ''} — check the Alerts tab")
    else:
        st.success("✅ All sensors nominal")

    cols = st.columns(6)
    for col, (label, value, icon) in zip(cols, [
        ("Avg Temperature",      f"{np.mean([last[s] for s in TEMP_SENSORS]):.1f}°F", "🌡️"),
        ("Avg Humidity",         f"{round(np.mean([last[s] for s in HUM_SENSORS]))}%", "☁️"),
        ("Water Leak (4 sensors)", "OK",                                               "💧"),
        ("Cold Storage",         f"{last['cold_storage_temp']:.1f}°F",                "❄️"),
        ("Feed Bin Level",       f"{round(last['feed_bin_level'])}%",                 "🌾"),
        ("Sensors Online",       "6/10",                                               "📡"),
    ]):
        col.metric(f"{icon} {label}", value)

    # ── Temperature & Humidity sensor cards ───────────────────────────────────
    st.markdown("---")
    st.markdown("### 🌡️ Temperature & Humidity")
    card_cols = st.columns(4)
    for col, label, ts, hs, bs in zip(card_cols, TEMP_LABELS, TEMP_SENSORS, HUM_SENSORS, BAT_SENSORS):
        with col:
            st.markdown(sensor_card(label, last[ts], last[hs], last[bs]), unsafe_allow_html=True)

    # ── Water Leak Detection section ───────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🚰 Water Leak Detection")
    cbw_sensors = ["CBW1", "CBW2", "CBW6", "CBW8"]
    cbw_cols = st.columns(4)
    for col, name in zip(cbw_cols, cbw_sensors):
        with col:
            st.markdown(f"""
            <div class="sensor-card" style="border-top-color:#6a88a8;">
                <div class="sensor-name">{name} - Water Leak</div>
                <div style="display:flex; justify-content:space-around; align-items:flex-start; margin-top:8px;">
                    <div style="text-align:center;">
                        <div class="reading-value" style="color:#8fa8c8;">--</div>
                        <div class="reading-label">Water Leak</div>
                    </div>
                    <div style="text-align:center;">
                        <div class="reading-value" style="color:#8fa8c8;">--%</div>
                        <div class="reading-label">Battery</div>
                    </div>
                </div>
                <div class="reading-label" style="text-align:center; margin-top:10px;">No recent data</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Cold Storage & Feed Bin section ────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ❄️ Cold Storage & Feed Bin")
    cs_val = last["cold_storage_temp"]
    cs_hum = last["cold_storage_humidity"]
    fb_val = last["feed_bin_level"]
    fb_dist = last["feed_bin_distance"]

    cs_cls = "critical" if (cs_val < THRESH["cold_too_cold"] or cs_val > THRESH["cold_too_warm"]) \
             else ("warning" if cs_val > THRESH["cold_warm_warn"] else "")
    fb_cls = "critical" if fb_val < THRESH["bin_critical"] \
             else ("warning" if fb_val < THRESH["bin_low"] else "")

    cs_val_color = "#e74c3c" if cs_cls == "critical" else ("#f39c12" if cs_cls == "warning" else "#ffffff")
    fb_val_color = "#e74c3c" if fb_cls == "critical" else ("#f39c12" if fb_cls == "warning" else "#ffffff")
    cs_border = "#e74c3c" if cs_cls == "critical" else ("#f39c12" if cs_cls == "warning" else "#2ecc71")
    fb_border = "#e74c3c" if fb_cls == "critical" else ("#f39c12" if fb_cls == "warning" else "#2ecc71")

    # Last updated time from the CSV timestamp
    last_ts = last["timestamp"]
    now = datetime.now()
    delta = now - last_ts
    total_mins = int(delta.total_seconds() // 60)
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

    # ── Trend charts at the bottom ─────────────────────────────────────────────
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

# ── Temperature ────────────────────────────────────────────────────────────────
elif page == "🌡️ Temperature":
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

# ── Humidity ───────────────────────────────────────────────────────────────────
elif page == "💧 Humidity":
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
        "Sensor":    TEMP_LABELS,
        "Min (%)":   [round(df[s].min()) for s in HUM_SENSORS],
        "Max (%)":   [round(df[s].max()) for s in HUM_SENSORS],
        "Avg (%)":   [round(df[s].mean()) for s in HUM_SENSORS],
        "Current (%)":[round(last[s]) for s in HUM_SENSORS],
    }), width='stretch', hide_index=True)

# ── Water Leak ─────────────────────────────────────────────────────────────────
elif page == "🚰 Water Leak":
    st.title("🚰 Water Leak Detection")

    if last["water_leak"]:
        st.error("🚨 WATER LEAK CURRENTLY DETECTED")
    else:
        st.success("✅ No active water leak detected")

    df_r = get_range(df, 7)
    leak_events = df_r[df_r["water_leak"] > 0][["timestamp", "water_leak"]].copy()
    leak_events.columns = ["Timestamp", "Leak Detected"]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_r["timestamp"], y=df_r["water_leak"],
                         marker_color="#e74c3c", name="Leak Event"))
    fig.update_layout(
        title="Water Leak Events (7 Days)", paper_bgcolor="#1e2d3d", plot_bgcolor="#1e2d3d",
        font_color="#c0cfe0", xaxis=dict(gridcolor="#2a3f55"),
        yaxis=dict(gridcolor="#2a3f55", title="Leak (1=Yes)"),
        height=280, margin=dict(l=0, r=0, t=40, b=0)
    )
    st.plotly_chart(fig, width='stretch')
    st.markdown(f"**Total leak events (7d):** {len(leak_events)}")
    if not leak_events.empty:
        st.dataframe(leak_events, width='stretch', hide_index=True)
    st.info("ℹ️ Sensors: CBW1, CBW2, CBW6, CBW8 — Binary detection. Any water triggers a CRITICAL alert.")

# ── Cold Storage ───────────────────────────────────────────────────────────────
elif page == "❄️ Cold Storage":
    st.title("❄️ Cold Storage Monitoring")

    val = last["cold_storage_temp"]
    status = "🔴 CRITICAL" if val > 44 or val < 32 else ("🟡 WARNING" if val > 40 else "🟢 NORMAL")
    st.metric("Current Temperature", f"{val:.1f}°F", delta=status)

    c1, c2 = st.columns([1, 2])
    with c1:
        st.plotly_chart(gauge_chart(val, "Cold Storage Temp", 28, 55, "°F", 40, 44),
                        width='stretch')
    with c2:
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

    st.markdown("### 7-Day Stats")
    cs = df["cold_storage_temp"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Min", f"{cs.min():.1f}°F")
    c2.metric("Max", f"{cs.max():.1f}°F")
    c3.metric("Avg", f"{cs.mean():.1f}°F")
    c4.metric("Std Dev", f"{cs.std():.2f}°F")

# ── Feed Bin ───────────────────────────────────────────────────────────────────
elif page == "🌾 Feed Bin":
    st.title("🌾 Feed Bin Level")

    val = last["feed_bin_level"]
    status = "🔴 CRITICAL — Refill Now!" if val < 15 else ("🟡 Low" if val < 25 else "🟢 OK")
    st.metric("Current Fill Level", f"{val:.1f}%", delta=status)

    c1, c2 = st.columns([1, 2])
    with c1:
        st.plotly_chart(gauge_chart(val, "Feed Bin Level", 0, 100, "%", 25, 15),
                        width='stretch')
    with c2:
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

# ── Alerts ─────────────────────────────────────────────────────────────────────
elif page == "⚠️ Alerts":
    st.title("⚠️ Active Alerts")

    if not alerts:
        st.success("✅ No active alerts — all sensors are within normal ranges.")
    else:
        for severity, message in alerts:
            if severity == "CRITICAL":
                st.error(f"🔴 **CRITICAL** — {message}")
            else:
                st.warning(f"🟡 **WARNING** — {message}")

    st.markdown("---")
    st.markdown("### Alert Threshold Reference")
    st.dataframe(pd.DataFrame([
        ("Temperature", "Freezing",      "CRITICAL", f"Below {THRESH['temp_freeze']}°F"),
        ("Temperature", "Frost Warning", "WARNING",  f"Below {THRESH['temp_frost']}°F"),
        ("Temperature", "Heat Warning",  "WARNING",  f"Above {THRESH['temp_heat']}°F"),
        ("Temperature", "Extreme Heat",  "CRITICAL", f"Above {THRESH['temp_extreme']}°F"),
        ("Humidity",    "Too Dry",       "WARNING",  f"Below {THRESH['hum_dry']}%"),
        ("Humidity",    "Mold Risk",     "WARNING",  f"Above {THRESH['hum_mold']}%"),
        ("Cold Storage","Too Cold",      "CRITICAL", f"Below {THRESH['cold_too_cold']}°F"),
        ("Cold Storage","Warming Up",    "WARNING",  f"Above {THRESH['cold_warm_warn']}°F"),
        ("Cold Storage","Too Warm",      "CRITICAL", f"Above {THRESH['cold_too_warm']}°F"),
        ("Feed Bin",    "Running Low",   "WARNING",  f"Below {THRESH['bin_low']}%"),
        ("Feed Bin",    "Refill Now",    "CRITICAL", f"Below {THRESH['bin_critical']}%"),
        ("Water Leak",  "Leak Detected", "CRITICAL", "Any detection"),
    ], columns=["Category", "Alert", "Severity", "Condition"]),
    width='stretch', hide_index=True)

# ── Sensor Status ──────────────────────────────────────────────────────────────
elif page == "⚙️ Sensor Status":
    st.title("⚙️ Sensor Status & Diagnostics")

    st.dataframe(pd.DataFrame([
        ("CBT1",     "Temperature/Humidity", "Online",  "2 min ago",  "100%"),
        ("CBT2",     "Temperature/Humidity", "Online",  "4 min ago",  "100%"),
        ("CBT3A",    "Temperature/Humidity", "Online",  "1 min ago",  "100%"),
        ("CBT3B",    "Temperature/Humidity", "Online",  "6 min ago",  "100%"),
        ("CBW1",     "Water Leak",           "Online",  "3 min ago",  "80%"),
        ("CBW2",     "Water Leak",           "Online",  "5 min ago",  "78%"),
        ("CBW6",     "Water Leak",           "Online",  "2 min ago",  "88%"),
        ("CBW8",     "Water Leak",           "Offline", "26 hrs ago", "12%"),
        ("Cold1",    "Cold Storage",         "Online",  "1 min ago",  "94%"),
        ("FeedBin1", "Feed Bin Level",       "Online",  "8 min ago",  "60%"),
    ], columns=["Sensor ID", "Type", "Status", "Last Seen", "Battery"]),
    width='stretch', hide_index=True)

    st.markdown("### Data Pipeline Status")
    c1, c2, c3 = st.columns(3)
    c1.success("✅ LoRaWAN Gateway: Connected")
    c2.success("✅ Event Hub Ingestion: Running")
    c3.success("✅ Database: Connected")

    with st.expander("🔧 Troubleshooting Guide"):
        st.markdown("""
**Sensor Offline (No data > 24 hours)**
- Check LoRaWAN gateway connectivity
- Verify sensor battery level
- Check for physical damage

**Stale Data (12–24 hours old)**
- Check gateway internet connection
- Sensor may be in low-power mode

**Unusual Readings**
- Check sensor placement/positioning
- Verify sensor calibration
        """)

# ── Thresholds ─────────────────────────────────────────────────────────────────
elif page == "🎚️ Thresholds":
    st.title("🎚️ Alert Threshold Settings")
    st.info("Adjust thresholds below. Changes apply to the current session.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 🌡️ Temperature Alerts (°F)")
        THRESH["temp_freeze"]  = st.number_input("Freezing (CRITICAL below)",    value=THRESH["temp_freeze"])
        THRESH["temp_frost"]   = st.number_input("Frost Warning (WARNING below)", value=THRESH["temp_frost"])
        THRESH["temp_heat"]    = st.number_input("Heat Warning (WARNING above)",  value=THRESH["temp_heat"])
        THRESH["temp_extreme"] = st.number_input("Extreme Heat (CRITICAL above)", value=THRESH["temp_extreme"])
        st.markdown("#### 💧 Humidity Alerts (%)")
        THRESH["hum_dry"]  = st.number_input("Too Dry (WARNING below)",  value=THRESH["hum_dry"])
        THRESH["hum_mold"] = st.number_input("Mold Risk (WARNING above)", value=THRESH["hum_mold"])
    with c2:
        st.markdown("#### ❄️ Cold Storage Alerts (°F)")
        THRESH["cold_too_cold"]  = st.number_input("Too Cold (CRITICAL below)",  value=THRESH["cold_too_cold"])
        THRESH["cold_warm_warn"] = st.number_input("Warming Up (WARNING above)",  value=THRESH["cold_warm_warn"])
        THRESH["cold_too_warm"]  = st.number_input("Too Warm (CRITICAL above)",   value=THRESH["cold_too_warm"])
        st.markdown("#### 🌾 Feed Bin Alerts (%)")
        THRESH["bin_low"]      = st.number_input("Running Low (WARNING below)", value=THRESH["bin_low"])
        THRESH["bin_critical"] = st.number_input("Refill Now (CRITICAL below)", value=THRESH["bin_critical"])
        st.markdown("#### 💧 Water Leak")
        st.info("Binary detection — any water triggers CRITICAL. No threshold to set.")

    if st.button("💾 Save Changes", type="primary"):
        st.success("Thresholds updated for this session.")
    if st.button("↩️ Reset to Defaults"):
        st.rerun()

# ── AI Chat ────────────────────────────────────────────────────────────────────
elif page == "🤖 AI Chat":
    st.title("🤖 AI Chat")
    st.caption("Ask questions about your sensor data — temperature, humidity, water leaks, cold storage, feed bin, and more.")

    st.markdown("**Quick questions:**")
    qc1, qc2, qc3, qc4 = st.columns(4)
    quick = None
    if qc1.button("Sensor Status"):  quick = "What is the current status of all sensors?"
    if qc2.button("Active Alerts"):  quick = "Are there any active alerts right now?"
    if qc3.button("Temperatures"):   quick = "What are the current temperature readings?"
    if qc4.button("Feed Bin"):       quick = "What is the feed bin level and should I be concerned?"

    context_summary = f"""
You are an AI assistant for a farm sensor monitoring dashboard. Here is the current sensor data:

Temperature sensors (°F): CBT1={last['CBT1_temp']:.1f}, CBT2={last['CBT2_temp']:.1f}, CBT3A={last['CBT3A_temp']:.1f}, CBT3B={last['CBT3B_temp']:.1f}
Humidity sensors (%): CBT1={last['CBT1_humidity']:.1f}, CBT2={last['CBT2_humidity']:.1f}, CBT3A={last['CBT3A_humidity']:.1f}, CBT3B={last['CBT3B_humidity']:.1f}
Battery: all CBT sensors at 100%
Cold storage temperature: {last['cold_storage_temp']:.1f}°F
Feed bin level: {last['feed_bin_level']:.1f}%
Water leak detected: {'Yes' if last['water_leak'] else 'No'}
Active alerts: {alerts if alerts else 'None'}
Alert thresholds: {THRESH}

Answer questions helpfully and concisely. If asked something outside farm sensor monitoring, politely redirect.
"""

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Ask about your farm sensors...") or quick

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    messages = [{"role": "user", "content": context_summary + "\n\nUser question: " + user_input}]
                    if len(st.session_state.chat_history) > 2:
                        for h in st.session_state.chat_history[-6:-1]:
                            messages.append({"role": h["role"], "content": h["content"]})
                        messages.append({"role": "user", "content": user_input})
                    resp = requests.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={"Content-Type": "application/json"},
                        json={"model": "claude-sonnet-4-20250514", "max_tokens": 1000, "messages": messages},
                        timeout=30,
                    )
                    reply = resp.json()["content"][0]["text"]
                except Exception as e:
                    reply = f"Sorry, I couldn't connect to the AI service. ({e})"
                st.write(reply)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})