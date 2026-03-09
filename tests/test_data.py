import os
import pytest
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

REQUIRED_COLUMNS = [
    "timestamp",
    "CBT1_temp", "CBT2_temp", "CBT3A_temp", "CBT3B_temp",
    "CBT1_humidity", "CBT2_humidity", "CBT3A_humidity", "CBT3B_humidity",
    "CBT1_battery", "CBT2_battery", "CBT3A_battery", "CBT3B_battery",
    "cold_storage_temp", "cold_storage_humidity",
    "feed_bin_level", "feed_bin_distance",
    "water_leak",
]

TEMP_COLS    = ["CBT1_temp", "CBT2_temp", "CBT3A_temp", "CBT3B_temp", "cold_storage_temp"]
HUM_COLS     = ["CBT1_humidity", "CBT2_humidity", "CBT3A_humidity", "CBT3B_humidity", "cold_storage_humidity"]
BATTERY_COLS = ["CBT1_battery", "CBT2_battery", "CBT3A_battery", "CBT3B_battery"]


# ── File existence ─────────────────────────────────────────────────────────────

def test_sensors_csv_exists():
    assert os.path.exists(os.path.join(DATA_DIR, "sensors.csv"))


def test_latest_csv_exists():
    assert os.path.exists(os.path.join(DATA_DIR, "latest.csv"))


# ── Schema ─────────────────────────────────────────────────────────────────────

def test_sensors_has_required_columns(sensors_df):
    for col in REQUIRED_COLUMNS:
        assert col in sensors_df.columns, f"Missing column: {col}"


def test_latest_has_required_columns(latest_row):
    for col in REQUIRED_COLUMNS:
        assert col in latest_row.index, f"Missing column: {col}"


def test_sensors_has_rows(sensors_df):
    assert len(sensors_df) > 0


def test_latest_has_exactly_one_row():
    path = os.path.join(DATA_DIR, "latest.csv")
    df = pd.read_csv(path)
    assert len(df) == 1


# ── No nulls in critical columns ───────────────────────────────────────────────

def test_no_nulls_in_temp_columns(sensors_df):
    for col in TEMP_COLS:
        assert sensors_df[col].isnull().sum() == 0, f"Nulls found in {col}"


def test_no_nulls_in_humidity_columns(sensors_df):
    for col in HUM_COLS:
        assert sensors_df[col].isnull().sum() == 0, f"Nulls found in {col}"


def test_no_nulls_in_timestamp(sensors_df):
    assert sensors_df["timestamp"].isnull().sum() == 0


# ── Plausible value ranges ─────────────────────────────────────────────────────

def test_temperatures_in_plausible_range(sensors_df):
    for col in TEMP_COLS:
        assert sensors_df[col].between(0, 120).all(), \
            f"{col} has values outside 0–120°F"


def test_humidity_in_valid_range(sensors_df):
    for col in HUM_COLS:
        assert sensors_df[col].between(0, 100).all(), \
            f"{col} has values outside 0–100%"


def test_feed_bin_level_in_valid_range(sensors_df):
    assert sensors_df["feed_bin_level"].between(0, 100).all()


def test_water_leak_is_binary(sensors_df):
    assert sensors_df["water_leak"].isin([0, 1]).all()


def test_timestamps_are_sorted(sensors_df):
    assert sensors_df["timestamp"].is_monotonic_increasing


def test_latest_row_is_most_recent(sensors_df, latest_row):
    assert latest_row["timestamp"] == sensors_df["timestamp"].max()