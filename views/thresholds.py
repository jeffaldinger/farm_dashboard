import streamlit as st


def render(df, last, alerts, THRESH):
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
        st.markdown("#### 🚰 Water Leak")
        st.info("Binary detection — any water triggers CRITICAL. No threshold to set.")

    if st.button("💾 Save Changes", type="primary"):
        st.success("Thresholds updated for this session.")
    if st.button("↩️ Reset to Defaults"):
        st.rerun()