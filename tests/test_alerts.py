import pytest
from utils import check_alerts


def test_no_alerts_when_all_normal(normal_row, thresh):
    assert check_alerts(normal_row, thresh) == []


def test_freezing_temp_is_critical(normal_row, thresh):
    normal_row["CBT1_temp"] = 28.0  # below temp_freeze (32)
    alerts = check_alerts(normal_row, thresh)
    severities = [a[0] for a in alerts]
    assert "CRITICAL" in severities
    assert any("Freezing" in a[1] for a in alerts)


def test_frost_temp_is_warning(normal_row, thresh):
    normal_row["CBT1_temp"] = 34.0  # between temp_freeze (32) and temp_frost (36)
    alerts = check_alerts(normal_row, thresh)
    assert any(a[0] == "WARNING" and "Frost" in a[1] for a in alerts)


def test_extreme_heat_is_critical(normal_row, thresh):
    normal_row["CBT1_temp"] = 100.0  # above temp_extreme (95)
    alerts = check_alerts(normal_row, thresh)
    assert any(a[0] == "CRITICAL" and "Extreme heat" in a[1] for a in alerts)


def test_heat_warning(normal_row, thresh):
    normal_row["CBT1_temp"] = 88.0  # between temp_heat (85) and temp_extreme (95)
    alerts = check_alerts(normal_row, thresh)
    assert any(a[0] == "WARNING" and "Heat warning" in a[1] for a in alerts)


def test_high_humidity_mold_warning(normal_row, thresh):
    normal_row["CBT1_humidity"] = 90.0  # above hum_mold (85)
    alerts = check_alerts(normal_row, thresh)
    assert any(a[0] == "WARNING" and "Mold risk" in a[1] for a in alerts)


def test_low_humidity_dry_warning(normal_row, thresh):
    normal_row["CBT1_humidity"] = 35.0  # below hum_dry (40)
    alerts = check_alerts(normal_row, thresh)
    assert any(a[0] == "WARNING" and "Too dry" in a[1] for a in alerts)


def test_water_leak_is_critical(normal_row, thresh):
    normal_row["water_leak"] = 1
    alerts = check_alerts(normal_row, thresh)
    assert any(a[0] == "CRITICAL" and "leak" in a[1].lower() for a in alerts)


def test_no_water_leak_alert_when_clear(normal_row, thresh):
    normal_row["water_leak"] = 0
    alerts = check_alerts(normal_row, thresh)
    assert not any("leak" in a[1].lower() for a in alerts)


def test_cold_storage_too_warm_critical(normal_row, thresh):
    normal_row["cold_storage_temp"] = 50.0  # above cold_too_warm (45)
    alerts = check_alerts(normal_row, thresh)
    assert any(a[0] == "CRITICAL" and "Cold Storage" in a[1] for a in alerts)


def test_cold_storage_warming_warning(normal_row, thresh):
    normal_row["cold_storage_temp"] = 42.0  # between cold_warm_warn (40) and cold_too_warm (45)
    alerts = check_alerts(normal_row, thresh)
    assert any(a[0] == "WARNING" and "Warming up" in a[1] for a in alerts)


def test_feed_bin_critical(normal_row, thresh):
    normal_row["feed_bin_level"] = 10.0  # below bin_critical (15)
    alerts = check_alerts(normal_row, thresh)
    assert any(a[0] == "CRITICAL" and "Feed Bin" in a[1] for a in alerts)


def test_feed_bin_low_warning(normal_row, thresh):
    normal_row["feed_bin_level"] = 20.0  # between bin_critical (15) and bin_low (25)
    alerts = check_alerts(normal_row, thresh)
    assert any(a[0] == "WARNING" and "Running low" in a[1] for a in alerts)


def test_multiple_alerts_returned(normal_row, thresh):
    normal_row["CBT1_temp"] = 28.0   # CRITICAL
    normal_row["water_leak"] = 1     # CRITICAL
    normal_row["feed_bin_level"] = 20.0  # WARNING
    alerts = check_alerts(normal_row, thresh)
    assert len(alerts) >= 3