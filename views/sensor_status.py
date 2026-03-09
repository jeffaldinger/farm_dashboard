import streamlit as st
import pandas as pd


def render(df, last, alerts, THRESH):
    st.title("⚙️ Sensor Status & Diagnostics")

    st.dataframe(pd.DataFrame([
        ("CBT1",     "Temperature/Humidity", "Online",  "2 min ago",  "100%"),
        ("CBT2",     "Temperature/Humidity", "Online",  "4 min ago",  "100%"),
        ("CBT3A",    "Temperature/Humidity", "Online",  "1 min ago",  "100%"),
        ("CBT3B",    "Temperature/Humidity", "Online",  "6 min ago",  "100%"),
        ("CBW1",     "Water Leak",           "Offline", "3 days ago", "--"),
        ("CBW2",     "Water Leak",           "Offline", "3 days ago", "--"),
        ("CBW6",     "Water Leak",           "Offline", "3 days ago", "--"),
        ("CBW8",     "Water Leak",           "Offline", "3 days ago", "--"),
        ("Cold1",    "Cold Storage",         "Online",  "1 min ago",  "100%"),
        ("FeedBin1", "Feed Bin Level",       "Online",  "8 min ago",  "100%"),
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