"""
generate.py — Generates fake sensor data CSVs for the FarmSense dashboard.

Usage:
    python data/generate.py           # generates 7 days of data (default)
    python data/generate.py --days 30 # generates 30 days of data

Output files (written to data/):
    sensors.csv       — time-series readings for all sensors (15-min intervals)
    latest.csv        — single row of the most recent readings
"""

import argparse
import os
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ── Output directory (same folder as this script) ──────────────────────────────
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def smooth(base, noise, n, seed_offset=0):
    np.random.seed(42 + seed_offset)
    raw = base + noise * np.random.randn(n)
    return pd.Series(raw).rolling(4, min_periods=1).mean().values


def generate(days=7):
    now = datetime.now().replace(second=0, microsecond=0)
    # Round down to nearest 15-min interval
    now = now - timedelta(minutes=now.minute % 15)

    n = days * 24 * 4  # 15-min intervals
    timestamps = [now - timedelta(minutes=15 * i) for i in range(n)]
    timestamps.reverse()

    # Water leak events — 2 random moments in the dataset
    random.seed(42)
    leak = np.zeros(n)
    for idx in random.sample(range(n), 2):
        leak[idx] = 1

    df = pd.DataFrame({
        "timestamp":         timestamps,
        # Temperature sensors (°F)
        "CBT1_temp":         smooth(58, 3,   n, 0),
        "CBT2_temp":         smooth(61, 2.5, n, 1),
        "CBT3A_temp":        smooth(55, 4,   n, 2),
        "CBT3B_temp":        smooth(57, 3.5, n, 3),
        # Humidity sensors (%)
        "CBT1_humidity":     smooth(62, 5, n, 4),
        "CBT2_humidity":     smooth(65, 4, n, 5),
        "CBT3A_humidity":    smooth(70, 6, n, 6),
        "CBT3B_humidity":    smooth(68, 5, n, 7),
        # Battery — always 100% (demo)
        "CBT1_battery":      100,
        "CBT2_battery":      100,
        "CBT3A_battery":     100,
        "CBT3B_battery":     100,
        # Cold storage temp (°F)
        "cold_storage_temp": smooth(36, 1.5, n, 8),
        # Feed bin fill level (%)
        "feed_bin_level":    np.clip(smooth(72, 2, n, 9), 10, 100),
        # Water leak (binary 0/1)
        "water_leak":        leak,
    })

    # Round floats for cleaner CSVs
    float_cols = [c for c in df.columns if c != "timestamp"]
    df[float_cols] = df[float_cols].round(2)

    # ── Write sensors.csv ───────────────────────────────────────────────────────
    sensors_path = os.path.join(OUT_DIR, "sensors.csv")
    df.to_csv(sensors_path, index=False)
    print(f"✅ Written: {sensors_path}  ({len(df)} rows)")

    # ── Write latest.csv ────────────────────────────────────────────────────────
    latest_path = os.path.join(OUT_DIR, "latest.csv")
    df.tail(1).to_csv(latest_path, index=False)
    print(f"✅ Written: {latest_path}  (1 row — most recent reading)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate FarmSense fake sensor data")
    parser.add_argument("--days", type=int, default=7, help="Number of days to generate (default: 7)")
    args = parser.parse_args()
    generate(days=args.days)
