import pytest
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils import get_range, line_chart, sensor_card


# ── get_range ──────────────────────────────────────────────────────────────────

def test_get_range_returns_correct_window():
    now = datetime.now()
    df = pd.DataFrame({"timestamp": [
        now - timedelta(days=10),
        now - timedelta(days=3),
        now - timedelta(days=1),
        now - timedelta(hours=1),
    ]})
    result = get_range(df, 7)
    assert len(result) == 3  # last 7 days: 3d, 1d, 1h ago


def test_get_range_empty_when_all_old():
    now = datetime.now()
    df = pd.DataFrame({"timestamp": [
        now - timedelta(days=30),
        now - timedelta(days=20),
    ]})
    result = get_range(df, 7)
    assert len(result) == 0


def test_get_range_returns_all_when_within_window():
    now = datetime.now()
    df = pd.DataFrame({"timestamp": [
        now - timedelta(hours=6),
        now - timedelta(hours=12),
    ]})
    result = get_range(df, 1)
    assert len(result) == 2


# ── line_chart ─────────────────────────────────────────────────────────────────

def test_line_chart_returns_figure():
    df = pd.DataFrame({
        "timestamp": pd.date_range("2025-01-01", periods=5, freq="h"),
        "col_a": [1, 2, 3, 4, 5],
        "col_b": [5, 4, 3, 2, 1],
    })
    fig = line_chart(df, ["col_a", "col_b"], ["A", "B"], "Test Chart", "°F")
    assert isinstance(fig, go.Figure)


def test_line_chart_has_correct_trace_count():
    df = pd.DataFrame({
        "timestamp": pd.date_range("2025-01-01", periods=3, freq="h"),
        "col_a": [1, 2, 3],
        "col_b": [4, 5, 6],
        "col_c": [7, 8, 9],
    })
    fig = line_chart(df, ["col_a", "col_b", "col_c"], ["A", "B", "C"], "Test", "%")
    assert len(fig.data) == 3


def test_line_chart_trace_names():
    df = pd.DataFrame({
        "timestamp": pd.date_range("2025-01-01", periods=3, freq="h"),
        "temp": [55, 56, 57],
    })
    fig = line_chart(df, ["temp"], ["CBT1"], "Temps", "°F")
    assert fig.data[0].name == "CBT1"


# ── sensor_card ────────────────────────────────────────────────────────────────

THRESH = {
    "temp_freeze": 32, "temp_frost": 36, "temp_heat": 85, "temp_extreme": 95,
    "hum_dry": 40, "hum_mold": 85,
}


def test_sensor_card_contains_label():
    html = sensor_card("CBT1", 58.0, 65.0, 100, THRESH)
    assert "CBT1" in html


def test_sensor_card_contains_temp_value():
    html = sensor_card("CBT1", 58.0, 65.0, 100, THRESH)
    assert "58.0°F" in html


def test_sensor_card_contains_humidity_value():
    html = sensor_card("CBT1", 58.0, 65.0, 100, THRESH)
    assert "65%" in html


def test_sensor_card_normal_has_no_warning_class():
    html = sensor_card("CBT1", 58.0, 65.0, 100, THRESH)
    assert "sensor-card warning" not in html
    assert "sensor-card critical" not in html


def test_sensor_card_freezing_temp_is_critical():
    html = sensor_card("CBT1", 28.0, 65.0, 100, THRESH)
    assert "sensor-card critical" in html


def test_sensor_card_high_humidity_is_warning():
    html = sensor_card("CBT1", 58.0, 90.0, 100, THRESH)
    assert "sensor-card warning" in html