import streamlit as st


def render(df, last, alerts, THRESH):
    st.title("🚰 Water Leak Detection")

    cols = st.columns(4)
    for col, name in zip(cols, ["CBW1", "CBW2", "CBW6", "CBW8"]):
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
                <div class="reading-label" style="text-align:center; margin-top:10px;">Offline — No recent data</div>
            </div>
            """, unsafe_allow_html=True)