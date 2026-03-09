import streamlit as st
import pandas as pd


def render(df, last, alerts, THRESH):
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