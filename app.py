import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random
import requests
import json

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
    [data-testid="stSidebar"] .stRadio label { font-size: 15px; padding: 4px 0; }
    .metric-card {
        background: #1e2d3d;
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 4px solid #2ecc71;
        margin-bottom: 8px;
    }
    .metric-card.warning { border-left-color: #f39c12; }
    .metric-card.critical { border-left-color: #e74c3c; }
    .metric-card h4 { color: #8fa8c8; margin: 0 0 4px 0; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; }
    .metric-card h2 { color: #ffffff; margin: 0; font-size: 26px; }
    .metric-card span { color: #8fa8c8; font-size: 12px; }
    .alert-box {
        background: #2c1a1a;
        border: 1px solid #e74c3c;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 6px 0;
    }
    .alert-box.warning { background: #2c2414; border-color: #f39c12; }
    .section-header {
        font-size: 20px;
        font-weight: 700;
        color: #e0e6ef;
        border-bottom: 2px solid #2ecc71;
        padding-bottom: 6px;
        margin: 24px 0 16px 0;
    }
    div[data-testid="stChatMessage"] { background: #1e2d3d; border-radius: 10px; margin: 4px 0; }
    .stApp { background-color: #111c2b; }
    h1, h2, h3, h4 { color: #e0e6ef; }
    p, li { color: #c0cfe0; }
</style>
""", unsafe_allow_html=True)

# ── Fake data generation ────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def generate_sensor_data(days=7):
    now = datetime.now()
    timestamps = [now - timedelta(minutes=15 * i) for i in range(days * 24 * 4)]
    timestamps.reverse()

    np.random.seed(42)
    n = len(timestamps)

    def smooth(base, noise, n):
        raw = base + noise * np.random.randn(n)
        return pd.Series(raw).rolling(4, min_periods=1).mean().values

    df = pd.DataFrame({
        "timestamp": timestamps,
        "CBT1_temp": smooth(58, 3, n),
        "CBT2_temp": smooth(61, 2.5, n),
        "CBT3A_temp": smooth(55, 4, n),
        "CBT3B_temp": smooth(57, 3.5, n),
        "CBT1_humidity": smooth(62, 5, n),
        "CBT2_humidity": smooth(65, 4, n),
        "CBT3A_humidity": smooth(70, 6, n),
        "CBT3B_humidity": smooth(68, 5, n),
        "cold_storage_temp": smooth(36, 1.5, n),
        "feed_bin_level": np.clip(smooth(72, 2, n), 10, 100),
    })

    # Water leak — mostly 0, occasional spike
    leak = np.zeros(n)
    for idx in random.sample(range(n), 2):
        leak[idx] = 1
    df["water_leak"] = leak

    return df

def latest(df):
    return df.iloc[-1]

def get_range(df, days):
    cutoff = datetime.now() - timedelta(days=days)
    return df[df["timestamp"] >= cutoff]

# ── Load data ───────────────────────────────────────────────────────────────────
df = generate_sensor_data(7)
last = latest(df)

TEMP_SENSORS = ["CBT1_temp", "CBT2_temp", "CBT3A_temp", "CBT3B_temp"]
HUM_SENSORS  = ["CBT1_humidity", "CBT2_humidity", "CBT3A_humidity", "CBT3B_humidity"]
TEMP_LABELS  = ["CBT1", "CBT2", "CBT3A", "CBT3B"]

# Alert thresholds (defaults)
THRESH = {
    "temp_freeze": 32, "temp_frost": 36, "temp_heat": 85, "temp_extreme": 95,
    "hum_dry": 40, "hum_mold": 85,
    "cold_too_cold": 32, "cold_warm_warn": 40, "cold_too_warm": 45,
    "bin_low": 25, "bin_critical": 15,
}

def check_alerts(df_last):
    alerts = []
    for s, l in zip(TEMP_SENSORS, TEMP_LABELS):
        t = df_last[s]
        if t < THRESH["temp_freeze"]:   alerts.append(("CRITICAL", f"{l} — Freezing! {t:.1f}°F"))
        elif t < THRESH["temp_frost"]:  alerts.append(("WARNING",  f"{l} — Frost warning {t:.1f}°F"))
        elif t > THRESH["temp_extreme"]:alerts.append(("CRITICAL", f"{l} — Extreme heat {t:.1f}°F"))
        elif t > THRESH["temp_heat"]:   alerts.append(("WARNING",  f"{l} — Heat warning {t:.1f}°F"))
    for s, l in zip(HUM_SENSORS, TEMP_LABELS):
        h = df_last[s]
        if h < THRESH["hum_dry"]:   alerts.append(("WARNING", f"{l} humidity — Too dry {h:.1f}%"))
        elif h > THRESH["hum_mold"]:alerts.append(("WARNING", f"{l} humidity — Mold risk {h:.1f}%"))
    cs = df_last["cold_storage_temp"]
    if cs < THRESH["cold_too_cold"]:    alerts.append(("CRITICAL", f"Cold Storage — Too cold {cs:.1f}°F"))
    elif cs > THRESH["cold_too_warm"]:  alerts.append(("CRITICAL", f"Cold Storage — Too warm {cs:.1f}°F"))
    elif cs > THRESH["cold_warm_warn"]: alerts.append(("WARNING",  f"Cold Storage — Warming up {cs:.1f}°F"))
    fb = df_last["feed_bin_level"]
    if fb < THRESH["bin_critical"]:     alerts.append(("CRITICAL", f"Feed Bin — Refill immediately! {fb:.1f}%"))
    elif fb < THRESH["bin_low"]:        alerts.append(("WARNING",  f"Feed Bin — Running low {fb:.1f}%"))
    if df_last["water_leak"] > 0:       alerts.append(("CRITICAL", "Water leak detected!"))
    return alerts

alerts = check_alerts(last)

# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌾 FarmSense")
    st.markdown("**Sensor Monitoring Dashboard**")
    st.markdown("---")
    page = st.radio("Navigation", [
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
    ])
    st.markdown("---")
    alert_color = "🔴" if any(a[0] == "CRITICAL" for a in alerts) else ("🟡" if alerts else "🟢")
    st.markdown(f"{alert_color} **{len(alerts)} Active Alert{'s' if len(alerts) != 1 else ''}**")
    st.markdown("---")
    st.caption("Data Source: LoRaWAN Sensors\nRefresh: Every 15 min")

# ── Helper: plotly line chart ───────────────────────────────────────────────────
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
        xaxis=dict(gridcolor="#2a3f55"), yaxis=dict(gridcolor="#2a3f55", title=yaxis),
        margin=dict(l=0, r=0, t=40, b=0), height=320,
    )
    return fig

def gauge_chart(value, title, min_val, max_val, unit, warn, crit):
    color = "#e74c3c" if value >= crit else ("#f39c12" if value >= warn else "#2ecc71")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title, "font": {"color": "#c0cfe0"}},
        number={"suffix": unit, "font": {"color": "#ffffff"}},
        gauge={
            "axis": {"range": [min_val, max_val], "tickcolor": "#8fa8c8"},
            "bar": {"color": color},
            "bgcolor": "#2a3f55",
            "bordercolor": "#2a3f55",
            "steps": [
                {"range": [min_val, warn], "color": "#1e2d3d"},
                {"range": [warn, crit], "color": "#2c2414"},
                {"range": [crit, max_val], "color": "#2c1a1a"},
            ],
        }
    ))
    fig.update_layout(paper_bgcolor="#1e2d3d", font_color="#c0cfe0",
                      height=220, margin=dict(l=10, r=10, t=40, b=10))
    return fig

# ── Range selector ──────────────────────────────────────────────────────────────
def range_selector():
    t1, t2, t3 = st.tabs(["24 Hours", "3 Days", "7 Days"])
    with t1: days = 1
    with t2: days = 3
    with t3: days = 7
    # Streamlit tabs don't return values easily — use session state
    return days

# ── Pages ───────────────────────────────────────────────────────────────────────

# ════════════════════════════════════════════════════════════════════════════════
if page == "📊 Overview":
    st.title("📊 Sensor Overview")

    # Alert banner
    if alerts:
        sev = "error" if any(a[0] == "CRITICAL" for a in alerts) else "warning"
        getattr(st, sev)(f"⚠️ {len(alerts)} active alert{'s' if len(alerts)!=1 else ''} — check the Alerts tab")
    else:
        st.success("✅ All sensors nominal")

    # KPI row
    cols = st.columns(4)
    kpis = [
        ("Avg Temperature", f"{np.mean([last[s] for s in TEMP_SENSORS]):.1f}°F", "🌡️"),
        ("Avg Humidity",    f"{np.mean([last[s] for s in HUM_SENSORS]):.1f}%",   "💧"),
        ("Cold Storage",    f"{last['cold_storage_temp']:.1f}°F",                "❄️"),
        ("Feed Bin Level",  f"{last['feed_bin_level']:.1f}%",                    "🌾"),
    ]
    for col, (label, value, icon) in zip(cols, kpis):
        col.metric(f"{icon} {label}", value)

    st.markdown("---")

    # Range tabs
    tab1, tab2, tab3 = st.tabs(["24 Hours", "3 Days", "7 Days"])
    for tab, days in zip([tab1, tab2, tab3], [1, 3, 7]):
        with tab:
            df_r = get_range(df, days)
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(line_chart(df_r, TEMP_SENSORS, TEMP_LABELS,
                    "Temperature Trend", "°F"), width='stretch')
            with c2:
                st.plotly_chart(line_chart(df_r, HUM_SENSORS, TEMP_LABELS,
                    "Humidity Trend", "%"), width='stretch')

    # Water leak + cold storage + feed bin summary
    c1, c2, c3 = st.columns(3)
    with c1:
        leak_count = int(df["water_leak"].sum())
        st.metric("🚰 Water Leak Events (7d)", leak_count,
                  delta="No current leak" if last["water_leak"] == 0 else "LEAK DETECTED")
    with c2:
        st.plotly_chart(gauge_chart(last["cold_storage_temp"], "Cold Storage",
            28, 55, "°F", 40, 44), width='stretch')
    with c3:
        st.plotly_chart(gauge_chart(last["feed_bin_level"], "Feed Bin Level",
            0, 100, "%", 25, 15), width='stretch')

# ════════════════════════════════════════════════════════════════════════════════
elif page == "🌡️ Temperature":
    st.title("🌡️ Temperature Analysis")

    tab1, tab2, tab3 = st.tabs(["24 Hours", "3 Days", "7 Days"])
    for tab, days in zip([tab1, tab2, tab3], [1, 3, 7]):
        with tab:
            df_r = get_range(df, days)
            st.plotly_chart(line_chart(df_r, TEMP_SENSORS, TEMP_LABELS,
                "Temperature — All Sensors", "°F"), width='stretch')

    st.markdown("### Current Readings")
    cols = st.columns(4)
    for col, s, l in zip(cols, TEMP_SENSORS, TEMP_LABELS):
        val = last[s]
        status = "🔴" if val < 36 or val > 85 else "🟢"
        col.metric(f"{status} {l}", f"{val:.1f}°F")

    # Stats table
    st.markdown("### Statistics (7-Day)")
    stats = pd.DataFrame({
        "Sensor": TEMP_LABELS,
        "Min (°F)": [df[s].min() for s in TEMP_SENSORS],
        "Max (°F)": [df[s].max() for s in TEMP_SENSORS],
        "Avg (°F)": [df[s].mean() for s in TEMP_SENSORS],
        "Current (°F)": [last[s] for s in TEMP_SENSORS],
    }).round(1)
    st.dataframe(stats, width='stretch', hide_index=True)

# ════════════════════════════════════════════════════════════════════════════════
elif page == "💧 Humidity":
    st.title("💧 Humidity Analysis")

    tab1, tab2, tab3 = st.tabs(["24 Hours", "3 Days", "7 Days"])
    for tab, days in zip([tab1, tab2, tab3], [1, 3, 7]):
        with tab:
            df_r = get_range(df, days)
            st.plotly_chart(line_chart(df_r, HUM_SENSORS, TEMP_LABELS,
                "Humidity — All Sensors", "%"), width='stretch')

    st.markdown("### Current Readings")
    cols = st.columns(4)
    for col, s, l in zip(cols, HUM_SENSORS, TEMP_LABELS):
        val = last[s]
        status = "🟡" if val < 40 or val > 85 else "🟢"
        col.metric(f"{status} {l}", f"{val:.1f}%")

    st.markdown("### Statistics (7-Day)")
    stats = pd.DataFrame({
        "Sensor": TEMP_LABELS,
        "Min (%)": [df[s].min() for s in HUM_SENSORS],
        "Max (%)": [df[s].max() for s in HUM_SENSORS],
        "Avg (%)": [df[s].mean() for s in HUM_SENSORS],
        "Current (%)": [last[s] for s in HUM_SENSORS],
    }).round(1)
    st.dataframe(stats, width='stretch', hide_index=True)

# ════════════════════════════════════════════════════════════════════════════════
elif page == "🚰 Water Leak":
    st.title("🚰 Water Leak Detection")

    current = last["water_leak"]
    if current:
        st.error("🚨 WATER LEAK CURRENTLY DETECTED")
    else:
        st.success("✅ No active water leak detected")

    st.markdown("### Leak Event History (7 Days)")
    df_r = get_range(df, 7)
    leak_events = df_r[df_r["water_leak"] > 0][["timestamp", "water_leak"]].copy()
    leak_events.columns = ["Timestamp", "Leak Detected"]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_r["timestamp"], y=df_r["water_leak"],
        marker_color="#e74c3c", name="Leak Event"
    ))
    fig.update_layout(
        title="Water Leak Events", paper_bgcolor="#1e2d3d",
        plot_bgcolor="#1e2d3d", font_color="#c0cfe0",
        xaxis=dict(gridcolor="#2a3f55"), yaxis=dict(gridcolor="#2a3f55", title="Leak (1=Yes)"),
        height=280, margin=dict(l=0, r=0, t=40, b=0)
    )
    st.plotly_chart(fig, width='stretch')

    st.markdown(f"**Total leak events (7d):** {len(leak_events)}")
    if not leak_events.empty:
        st.dataframe(leak_events, width='stretch', hide_index=True)

    st.info("ℹ️ Sensors: CBW1, CBW2, CBW6, CBW8 — Binary detection. Any water triggers a CRITICAL alert.")

# ════════════════════════════════════════════════════════════════════════════════
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

# ════════════════════════════════════════════════════════════════════════════════
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

# ════════════════════════════════════════════════════════════════════════════════
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
    thresh_df = pd.DataFrame([
        ("Temperature", "Freezing", "CRITICAL", f"Below {THRESH['temp_freeze']}°F"),
        ("Temperature", "Frost Warning", "WARNING", f"Below {THRESH['temp_frost']}°F"),
        ("Temperature", "Heat Warning", "WARNING", f"Above {THRESH['temp_heat']}°F"),
        ("Temperature", "Extreme Heat", "CRITICAL", f"Above {THRESH['temp_extreme']}°F"),
        ("Humidity", "Too Dry", "WARNING", f"Below {THRESH['hum_dry']}%"),
        ("Humidity", "Mold Risk", "WARNING", f"Above {THRESH['hum_mold']}%"),
        ("Cold Storage", "Too Cold", "CRITICAL", f"Below {THRESH['cold_too_cold']}°F"),
        ("Cold Storage", "Warming Up", "WARNING", f"Above {THRESH['cold_warm_warn']}°F"),
        ("Cold Storage", "Too Warm", "CRITICAL", f"Above {THRESH['cold_too_warm']}°F"),
        ("Feed Bin", "Running Low", "WARNING", f"Below {THRESH['bin_low']}%"),
        ("Feed Bin", "Refill Now", "CRITICAL", f"Below {THRESH['bin_critical']}%"),
        ("Water Leak", "Leak Detected", "CRITICAL", "Any detection"),
    ], columns=["Category", "Alert", "Severity", "Condition"])
    st.dataframe(thresh_df, width='stretch', hide_index=True)

# ════════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Sensor Status":
    st.title("⚙️ Sensor Status & Diagnostics")

    sensors = [
        ("CBT1", "Temperature/Humidity", "Online", "2 min ago", "87%"),
        ("CBT2", "Temperature/Humidity", "Online", "4 min ago", "72%"),
        ("CBT3A", "Temperature/Humidity", "Online", "1 min ago", "91%"),
        ("CBT3B", "Temperature/Humidity", "Online", "6 min ago", "65%"),
        ("CBW1", "Water Leak", "Online", "3 min ago", "80%"),
        ("CBW2", "Water Leak", "Online", "5 min ago", "78%"),
        ("CBW6", "Water Leak", "Online", "2 min ago", "88%"),
        ("CBW8", "Water Leak", "Offline", "26 hrs ago", "12%"),
        ("Cold1", "Cold Storage", "Online", "1 min ago", "94%"),
        ("FeedBin1", "Feed Bin Level", "Online", "8 min ago", "60%"),
    ]
    sensor_df = pd.DataFrame(sensors, columns=["Sensor ID", "Type", "Status", "Last Seen", "Battery"])
    st.dataframe(sensor_df, width='stretch', hide_index=True)

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
- Ensure sensor is within range of gateway

**Stale Data (12–24 hours old)**
- Check gateway internet connection
- Sensor may be in low-power mode

**Unusual Readings**
- Check sensor placement/positioning
- Verify sensor calibration
- Look for environmental interference
        """)

# ════════════════════════════════════════════════════════════════════════════════
elif page == "🎚️ Thresholds":
    st.title("🎚️ Alert Threshold Settings")
    st.info("Adjust thresholds below. Changes apply to the current session.")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### 🌡️ Temperature Alerts (°F)")
        THRESH["temp_freeze"] = st.number_input("Freezing (CRITICAL below)", value=THRESH["temp_freeze"])
        THRESH["temp_frost"]  = st.number_input("Frost Warning (WARNING below)", value=THRESH["temp_frost"])
        THRESH["temp_heat"]   = st.number_input("Heat Warning (WARNING above)", value=THRESH["temp_heat"])
        THRESH["temp_extreme"]= st.number_input("Extreme Heat (CRITICAL above)", value=THRESH["temp_extreme"])

        st.markdown("#### 💧 Humidity Alerts (%)")
        THRESH["hum_dry"]  = st.number_input("Too Dry (WARNING below)", value=THRESH["hum_dry"])
        THRESH["hum_mold"] = st.number_input("Mold Risk (WARNING above)", value=THRESH["hum_mold"])

    with c2:
        st.markdown("#### ❄️ Cold Storage Alerts (°F)")
        THRESH["cold_too_cold"]  = st.number_input("Too Cold (CRITICAL below)", value=THRESH["cold_too_cold"])
        THRESH["cold_warm_warn"] = st.number_input("Warming Up (WARNING above)", value=THRESH["cold_warm_warn"])
        THRESH["cold_too_warm"]  = st.number_input("Too Warm (CRITICAL above)", value=THRESH["cold_too_warm"])

        st.markdown("#### 🌾 Feed Bin Alerts (%)")
        THRESH["bin_low"]      = st.number_input("Running Low (WARNING below)", value=THRESH["bin_low"])
        THRESH["bin_critical"] = st.number_input("Refill Now (CRITICAL below)", value=THRESH["bin_critical"])

        st.markdown("#### 💧 Water Leak")
        st.info("Binary detection — any water triggers CRITICAL. No threshold to set.")

    if st.button("💾 Save Changes", type="primary"):
        st.success("Thresholds updated for this session.")
    if st.button("↩️ Reset to Defaults"):
        st.rerun()

# ════════════════════════════════════════════════════════════════════════════════
elif page == "🤖 AI Chat":
    st.title("🤖 AI Chat")
    st.caption("Ask questions about your sensor data — temperature, humidity, water leaks, cold storage, feed bin, and more.")

    # Quick-start prompts
    st.markdown("**Quick questions:**")
    qc1, qc2, qc3, qc4 = st.columns(4)
    quick = None
    if qc1.button("Sensor Status"):  quick = "What is the current status of all sensors?"
    if qc2.button("Active Alerts"):  quick = "Are there any active alerts right now?"
    if qc3.button("Temperatures"):   quick = "What are the current temperature readings?"
    if qc4.button("Feed Bin"):       quick = "What is the feed bin level and should I be concerned?"

    # Build context summary for the AI
    context_summary = f"""
You are an AI assistant for a farm sensor monitoring dashboard. Here is the current sensor data:

Temperature sensors (°F): CBT1={last['CBT1_temp']:.1f}, CBT2={last['CBT2_temp']:.1f}, CBT3A={last['CBT3A_temp']:.1f}, CBT3B={last['CBT3B_temp']:.1f}
Humidity sensors (%): CBT1={last['CBT1_humidity']:.1f}, CBT2={last['CBT2_humidity']:.1f}, CBT3A={last['CBT3A_humidity']:.1f}, CBT3B={last['CBT3B_humidity']:.1f}
Cold storage temperature: {last['cold_storage_temp']:.1f}°F
Feed bin level: {last['feed_bin_level']:.1f}%
Water leak detected: {'Yes' if last['water_leak'] else 'No'}
Active alerts: {alerts if alerts else 'None'}

Alert thresholds: {THRESH}

Answer questions helpfully and concisely based on this data. If asked something outside farm sensor monitoring, politely redirect.
"""

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Input
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
                        # Include recent history
                        for h in st.session_state.chat_history[-6:-1]:
                            messages.append({"role": h["role"], "content": h["content"]})
                        messages.append({"role": "user", "content": user_input})

                    resp = requests.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={"Content-Type": "application/json"},
                        json={
                            "model": "claude-sonnet-4-20250514",
                            "max_tokens": 1000,
                            "messages": messages,
                        },
                        timeout=30,
                    )
                    reply = resp.json()["content"][0]["text"]
                except Exception as e:
                    reply = f"Sorry, I couldn't connect to the AI service. ({e})"

                st.write(reply)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})

# ── CSV Export (always visible at bottom) ───────────────────────────────────────
st.markdown("---")
with st.expander("📥 Export Data"):
    c1, c2 = st.columns(2)
    start = c1.date_input("Start Date", value=(datetime.now() - timedelta(days=7)).date())
    end   = c2.date_input("End Date",   value=datetime.now().date())
    df_export = df[(df["timestamp"].dt.date >= start) & (df["timestamp"].dt.date <= end)]
    csv = df_export.to_csv(index=False).encode()
    st.download_button("⬇️ Download CSV", csv, "farmsense_export.csv", "text/csv")
