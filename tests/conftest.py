import sys
import os
import pytest
import pandas as pd

# Make sure the project root is on the path so utils imports cleanly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils import DEFAULT_THRESH

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


@pytest.fixture
def thresh():
    return DEFAULT_THRESH.copy()


@pytest.fixture
def normal_row():
    """A sensor row with all values well within normal ranges."""
    return {
        "CBT1_temp": 58.0, "CBT2_temp": 57.0, "CBT3A_temp": 59.0, "CBT3B_temp": 56.0,
        "CBT1_humidity": 65.0, "CBT2_humidity": 64.0, "CBT3A_humidity": 66.0, "CBT3B_humidity": 63.0,
        "cold_storage_temp": 37.0,
        "cold_storage_humidity": 55.0,
        "feed_bin_level": 70.0,
        "feed_bin_distance": 18.0,
        "water_leak": 0,
    }


@pytest.fixture
def sensors_df():
    path = os.path.join(DATA_DIR, "sensors.csv")
    return pd.read_csv(path, parse_dates=["timestamp"])


@pytest.fixture
def latest_row():
    path = os.path.join(DATA_DIR, "latest.csv")
    return pd.read_csv(path, parse_dates=["timestamp"]).iloc[0]