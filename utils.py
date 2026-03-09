import html
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

COLORS = ["#2ecc71", "#3498db", "#e67e22", "#9b59b6"]

TEMP_SENSORS = ["CBT1_temp",     "CBT2_temp",     "CBT3A_temp",    "CBT3B_temp"]
HUM_SENSORS  = ["CBT1_humidity", "CBT2_humidity", "CBT3A_humidity","CBT3B_humidity"]
TEMP_LABELS  = ["CBT1", "CBT2", "CBT3A", "CBT3B"]

DEFAULT_THRESH = {
    "temp_freeze": 32, "temp_frost": 36, "temp_heat": 85, "temp_extreme": 95,
    "hum_dry": 40, "hum_mold": 85,
    "cold_too_cold": 32, "cold_warm_warn": 40, "cold_too_warm": 45,
    "bin_low": 25, "bin_critical": 15,
}


def check_alerts(row, THRESH):
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


def get_range(df, days):
    cutoff = datetime.now() - timedelta(days=days)
    return df[df["timestamp"] >= cutoff]


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


def sensor_card(label, temp, humidity, battery, THRESH):
    safe_label = html.escape(str(label))
    if temp < THRESH["temp_freeze"] or temp > THRESH["temp_extreme"]:
        card_class = "sensor-card critical"
    elif temp < THRESH["temp_frost"] or temp > THRESH["temp_heat"] or humidity > THRESH["hum_mold"]:
        card_class = "sensor-card warning"
    else:
        card_class = "sensor-card"

    temp_cls = "crit" if (temp < THRESH["temp_freeze"] or temp > THRESH["temp_extreme"]) \
               else ("warn" if (temp < THRESH["temp_frost"] or temp > THRESH["temp_heat"]) else "")
    hum_cls  = "warn" if (humidity > THRESH["hum_mold"] or humidity < THRESH["hum_dry"]) else ""
    bat_pct  = int(battery)

    return f"""
    <div class="{card_class}">
        <div class="sensor-name">{safe_label} - Temp & Humidity</div>
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