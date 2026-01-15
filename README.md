# Artemis II Launch Times

Small utility to compute the Moon's position for launch windows and to load launch windows from CSV.

## Results

### Artemis II launch windows
* start 2026-02-06 21:41 EST moonrise 22:58 EST  ( 77 min into window, 73% illuminated) end 23:41 EST 
* start 2026-02-07 22:46 EST moonrise 23:54 EST  ( 68 min into window, 63% illuminated) end 00:46 EST 
* start 2026-02-08 23:20 EST moonrise 00:50 EST  ( 91 min into window, 53% illuminated) end 01:20 EST 
* start 2026-02-10 00:06 EST moonrise 01:47 EST  (101 min into window, 44% illuminated) end 02:06 EST 
* start 2026-02-11 01:05 EST moonrise 02:43 EST  ( 99 min into window, 34% illuminated) end 03:05 EST 
* start 2026-03-06 20:29 EST moonrise 21:41 EST  ( 73 min into window, 87% illuminated) end 22:29 EST 
* start 2026-03-07 20:57 EST moonrise 22:38 EST  (102 min into window, 80% illuminated) end 22:57 EST 
* start 2026-03-08 22:56 EDT moonrise 00:35 EDT  (100 min into window, 71% illuminated) end 00:56 EDT 
* start 2026-03-09 23:52 EDT moonrise 01:32 EDT  (101 min into window, 62% illuminated) end 01:52 EDT 
* start 2026-03-11 00:48 EDT moonrise 02:27 EDT  (100 min into window, 52% illuminated) end 02:43 EDT 
* start 2026-04-01 18:24 EDT moonrise 19:33 EDT  ( 70 min into window,100% illuminated) end 20:24 EDT 
* start 2026-04-03 20:00 EDT moonrise 21:27 EDT  ( 87 min into window, 96% illuminated) end 22:00 EDT 
* start 2026-04-04 20:53 EDT moonrise 22:24 EDT  ( 91 min into window, 92% illuminated) end 22:53 EDT 
* start 2026-04-05 21:40 EDT moonrise 23:21 EDT  (102 min into window, 85% illuminated) end 23:40 EDT 
* start 2026-04-06 22:36 EDT moonrise 00:17 EDT  (102 min into window, 78% illuminated) end 00:36 EDT 
* start 2026-04-30 18:06 EDT moonrise 19:18 EDT  ( 73 min into window, 99% illuminated) end 20:06 EDT 

### Apollo missions
* Apollo 11 start 1969-07-16 09:32 EDT moonrise 08:16 EDT  ( 76 min before window,   4% illuminated) end 14:02 EDT 
* Apollo 12 start 1969-11-14 11:22 EST moonrise 11:45 EST  ( 24 min into window,  28% illuminated) end 14:22 EST 

Process finished with exit code 0


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