# Artemis II Launch Times

Small utility to compute the Moon's position for launch windows and to load launch windows from CSV.

## Features

- `moon_position(datetime, latitude=KSC_LAT, longitude=KSC_LON)` — compute basic Moon position values (azimuth, altitude, distance, RA/Dec).
- `load_launch_windows_from_csv(path)` — load CSV files with `window_start_utc` and `duration_mins`.
- `calculate_moon_positions_for_launch_windows(csv_path, latitude, longitude, local_tz)` — combine CSV windows with computed moon positions.

## Requirements

- Python 3.8+
- `pytest` (for running tests)

## Installation

1. Create a virtual environment:
    
    python -m venv .venv
    source .venv/bin/activate

2. Install dev/test dependencies:

    python -m pip install -U pip
    python -m pip install pytest

## CSV format

Expected CSV header:

- `window_start_utc` — ISO 8601 datetime in UTC (e.g. `2025-01-01T12:00:00`)
- `duration_mins` — integer duration in minutes (e.g. `60`)

Example CSV rows:

    window_start_utc,duration_mins
    2025-01-01T12:00:00,60
    2025-06-01T03:30:00,90

## Usage

Import and call functions from `artemis_II_launch_times`:

    from datetime import datetime, timezone
    from artemis_II_launch_times import moon_position, load_launch_windows_from_csv

    dt = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    mp = moon_position(dt)
    print(mp)

    rows = load_launch_windows_from_csv('windows.csv')
    print(rows)

## Running tests

Run the test suite with `pytest`:

    python -m pytest -q

## Project layout

- `artemis_II_launch_times.py` — main module
- `tests/test_artemisIIlaunchtimes.py` — unit tests
- `tests/test_load_launch_windows.py` — additional CSV parsing tests
- `artemis_ii_mission_availability.csv` — example CSV (if present)

## License

Choose and add a license file if required.tee