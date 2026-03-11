import streamlit as st
import requests
import os


def render(df, last, alerts, THRESH):
    st.title("🤖 AI Chat")
    st.caption("Ask questions about your sensor data — temperature, humidity, water leaks, cold storage, feed bin, and more.")

    api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        st.warning("⚠️ ANTHROPIC_API_KEY is not set. AI Chat is unavailable.")
        return

    st.markdown("**Quick questions:**")
    qc1, qc2, qc3, qc4 = st.columns(4)
    quick = None
    if qc1.button("Sensor Status"): quick = "What is the current status of all sensors?"
    if qc2.button("Active Alerts"): quick = "Are there any active alerts right now?"
    if qc3.button("Temperatures"):  quick = "What are the current temperature readings?"
    if qc4.button("Feed Bin"):      quick = "What is the feed bin level and should I be concerned?"

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
                        headers={
                            "Content-Type": "application/json",
                            "x-api-key": api_key,
                            "anthropic-version": "2023-06-01",
                        },
                        json={"model": "claude-sonnet-4-20250514", "max_tokens": 1000, "messages": messages},
                        timeout=30,
                    )
                    resp_json = resp.json()
                    if "content" in resp_json:
                        reply = resp_json["content"][0]["text"]
                    else:
                        reply = f"Sorry, the AI service returned an error: {resp_json.get('error', {}).get('message', resp_json)}"
                except Exception as e:
                    reply = f"Sorry, I couldn't connect to the AI service. ({e})"
                st.write(reply)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})