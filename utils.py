import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

COLORS = ["#2ecc71", "#3498db", "#e67e22", "#9b59b6"]


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