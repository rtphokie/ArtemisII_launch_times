# python
import math
import zoneinfo
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
import skyfield.almanac as almanac_module

from artemis_II_launch_times import (
    KSC_LAT,
    KSC_LON,
    calculate_moon_positions_for_launch_windows,
    load_launch_windows_from_csv,
    moon_position,
    moonrise_for_date,
)


def test_load_launch_windows_from_csv(tmp_path):
    import csv

    data = [
        {"window_start_utc": "2025-01-01T12:00:00", "duration_mins": "60"},
        {"window_start_utc": "2025-06-01T03:30:00", "duration_mins": "90"},
    ]

    csv_file = tmp_path / "windows.csv"
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["window_start_utc", "duration_mins"])
        writer.writeheader()
        writer.writerows(data)

    rows = load_launch_windows_from_csv(str(csv_file))

    assert isinstance(rows, list)
    assert len(rows) == 2

    expected0 = datetime.fromisoformat(data[0]["window_start_utc"]).replace(
        tzinfo=timezone.utc
    )
    assert rows[0]["window_start_utc"] == expected0
    assert rows[0]["duration_mins"] == 60

    expected1 = datetime.fromisoformat(data[1]["window_start_utc"]).replace(
        tzinfo=timezone.utc
    )
    assert rows[1]["window_start_utc"] == expected1
    assert rows[1]["duration_mins"] == 90


def test_moon_position_structure_and_types():
    dt = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    res = moon_position(dt)

    expected_keys = {
        "datetime_utc",
        "latitude",
        "longitude",
        "azimuth_deg",
        "altitude_deg",
        "distance_km",
        "ra_hours",
        "dec_deg",
    }
    assert isinstance(res, dict)
    assert set(res.keys()) == expected_keys

    assert res["latitude"] == pytest.approx(KSC_LAT)
    assert res["longitude"] == pytest.approx(KSC_LON)

    for key in ("azimuth_deg", "altitude_deg", "distance_km", "ra_hours", "dec_deg"):
        assert isinstance(res[key], float)
        assert math.isfinite(res[key])


def test_naive_datetime_is_treated_as_utc():
    dt_naive = datetime(2025, 1, 1, 0, 0, 0)  # naive datetime
    res = moon_position(dt_naive)
    assert res["datetime_utc"].tzinfo is not None
    assert res["datetime_utc"].utcoffset() == timezone.utc.utcoffset(
        res["datetime_utc"]
    )


def test_custom_location_reflected_in_result():
    dt = datetime(2025, 6, 21, 0, 0, 0, tzinfo=timezone.utc)
    lat = 0.0
    lon = 0.0
    res = moon_position(dt, latitude=lat, longitude=lon)
    assert res["latitude"] == pytest.approx(lat)
    assert res["longitude"] == pytest.approx(lon)


def test_calculate_moon_positions_for_launch_windows():
    KSC_LAT = 28.57
    KSC_LON = -80.65
    KSC_TZ = "America/New_York"
    csv_path = Path(__file__).parent / "artemis_ii_mission_availability.csv"

    results = calculate_moon_positions_for_launch_windows(
        csv_path=csv_path, latitude=KSC_LAT, longitude=KSC_LON, local_tz=KSC_TZ
    )

    # Should return a non-empty list
    assert isinstance(results, list)
    assert len(results) > 0

    # Check structure of first result
    first = results[0]
    expected_keys = {
        "duration_mins",
        "moon_illumination",
        "moon_phase",
        "moon_position_end",
        "moon_position_start",
        "moonrise_local",
        "moonrise_utc",
        "window_end_local",
        "window_end_utc",
        "window_start_local",
        "window_start_utc",
    }
    assert set(first.keys()) == expected_keys

    # Verify datetime types and timezones
    for attr in ["start", "end"]:
        assert isinstance(first[f"window_{attr}_utc"], datetime)
        assert first[f"window_{attr}_utc"].tzinfo == timezone.utc
        assert first[f"window_{attr}_local"].tzinfo == zoneinfo.ZoneInfo(KSC_TZ)

    # Verify duration calculation
    duration_mins = first["duration_mins"]
    assert isinstance(duration_mins, int)
    assert duration_mins > 0
    calculated_duration = (
        first["window_end_utc"] - first["window_start_utc"]
    ).total_seconds() / 60
    assert calculated_duration == pytest.approx(duration_mins)

    # Verify moon_position structure
    for attr in ["start", "end"]:
        assert isinstance(first[f"moon_position_{attr}"], dict)
        assert "altitude_deg" in first[f"moon_position_{attr}"]
        assert "azimuth_deg" in first[f"moon_position_{attr}"]
        assert math.isfinite(first[f"moon_position_{attr}"]["altitude_deg"])
        assert math.isfinite(first[f"moon_position_{attr}"]["azimuth_deg"])


class _DummyTime:
    def __init__(self, dt: datetime):
        self._dt = dt

    def utc_datetime(self) -> datetime:
        return self._dt


def test_moonrise_found(monkeypatch):
    expected = datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc)

    def fake_find_discrete(t0, t1, f):
        return [_DummyTime(expected)], [1]

    monkeypatch.setattr(almanac_module, "find_discrete", fake_find_discrete)

    result = moonrise_for_date(date(2025, 1, 2))
    assert result == expected


def test_moonrise_not_found(monkeypatch):
    def fake_find_discrete_empty(t0, t1, f):
        return [], []

    monkeypatch.setattr(almanac_module, "find_discrete", fake_find_discrete_empty)

    result = moonrise_for_date(date(2025, 1, 2))
    assert result is None


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-vvv"]))
