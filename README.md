# FarmSense Dashboard

A Streamlit-based farm sensor monitoring dashboard demo with fake data.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app:**
   ```bash
   streamlit run app.py
   ```

3. Open your browser to `http://localhost:8501`

## Features

- 📊 **Overview** — KPI cards, trend charts, gauge widgets
- 🌡️ **Temperature** — Per-sensor readings, stats, 24h/3d/7d history
- 💧 **Humidity** — Per-sensor readings, stats, history
- 🚰 **Water Leak** — Event history, current status
- ❄️ **Cold Storage** — Temperature gauge, thresholds
- 🌾 **Feed Bin** — Fill level gauge, history
- ⚠️ **Alerts** — Active alerts + threshold reference table
- ⚙️ **Sensor Status** — Diagnostics table, pipeline status
- 🎚️ **Thresholds** — Adjustable alert thresholds
- 🤖 **AI Chat** — Claude-powered assistant with live sensor context
- 📥 **CSV Export** — Download filtered sensor data

## AI Chat

The AI Chat tab calls the Anthropic API. Make sure the API key is configured
in your environment or the app's hosting environment.

## Notes

- All sensor data is procedurally generated fake data (seeded for consistency)
- Data refreshes every 60 seconds (cached)
