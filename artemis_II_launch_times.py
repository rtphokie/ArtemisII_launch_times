# python
# file: `artemis_II_launch_times.py`
import csv
import zoneinfo
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from skyfield.api import Loader, Topos
except Exception as exc:
    raise ImportError("Requires 'skyfield' and 'jplephem'. Install with: pip install skyfield jplephem") from exc

_loader = Loader('~/.skyfield-data')
_ts = _loader.timescale()
_eph = _loader('de421.bsp')

KSC_LAT = 28.57
KSC_LON = -80.65
KSC_TZ = "America/New_York"

def moon_position(dt: datetime, latitude: float = KSC_LAT, longitude: float = KSC_LON):
    """
    Compute the Moon's position for UTC datetime `dt` at (latitude, longitude).

    Parameters:
    - dt: datetime (naive treated as UTC; aware datetimes converted to UTC)
    - latitude: degrees north (default Kennedy Space Center)
    - longitude: degrees east (use negative for west; default Kennedy Space Center)

    Returns: dict with keys:
    - datetime_utc: UTC datetime
    - latitude, longitude
    - azimuth_deg: degrees (0 = North, increases clockwise)
    - altitude_deg: degrees above horizon
    - distance_km: geocentric distance to Moon in kilometers
    - ra_hours: right ascension in hours
    - dec_deg: declination in degrees
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    t = _ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond / 1e6)
    earth = _eph['earth']
    moon = _eph['moon']
    observer = earth + Topos(latitude_degrees=latitude, longitude_degrees=longitude)

    astrometric = observer.at(t).observe(moon)
    apparent = astrometric.apparent()

    alt, az, distance = apparent.altaz()
    ra, dec, _ = apparent.radec()

    return {
        'datetime_utc': dt,
        'latitude': latitude,
        'longitude': longitude,
        'azimuth_deg': az.degrees,
        'altitude_deg': alt.degrees,
        'distance_km': distance.km,
        'ra_hours': ra.hours,
        'dec_deg': dec.degrees,
    }

def load_launch_windows_from_csv(csv_path: str):
    """
    Load launch windows from CSV file.

    Parameters:
    - csv_path: path to CSV file

    Returns: list of dicts with keys:
    - window_start_utc: datetime of window start (UTC)
    - duration_mins: duration of launch window in minutes
    """
    windows = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt_start_utc = datetime.fromisoformat(row['window_start_utc']).replace(tzinfo=timezone.utc)
            duration = int(row['duration_mins'])
            windows.append({
                'window_start_utc': dt_start_utc,
                'duration_mins': duration
            })
    return windows

def calculate_moon_positions_for_launch_windows(csv_path: str = None, latitude= KSC_LAT, longitude= KSC_LON, local_tz: str = KSC_TZ):
    """
    Read launch windows from CSV and calculate moon position for each window start time.

    Parameters:
    - csv_path: path to CSV file (default: artemis_ii_mission_availability.csv in same directory)
    - local_tz: timezone name for local times (default: America/New_York)

    Returns: list of dicts, each containing:
    - window_start_utc: datetime of window start (UTC)
    - window_stop_utc: datetime of window stop (UTC)
    - window_start_local: datetime of window start (local timezone)
    - window_stop_local: datetime of window stop (local timezone)
    - duration_mins: duration of launch window in minutes
    - moon_position: dict from moon_position() function
    """
    if csv_path is None:
        csv_path = Path(__file__).parent / "artemis_ii_mission_availability.csv"

    rows = load_launch_windows_from_csv(csv_path)

    tz = zoneinfo.ZoneInfo(local_tz)
    results = []

    for row in rows:
        dt_start_utc = row['window_start_utc']
        duration = int(row['duration_mins'])
        dt_stop_utc = dt_start_utc + timedelta(minutes=duration)

        dt_start_local = dt_start_utc.astimezone(tz)
        dt_stop_local = dt_stop_utc.astimezone(tz)

        moon_pos = moon_position(dt_start_utc, latitude, longitude)

        results.append({
            'window_start_utc': dt_start_utc,
            'window_stop_utc': dt_stop_utc,
            'window_start_local': dt_start_local,
            'window_stop_local': dt_stop_local,
            'duration_mins': duration,
            'moon_position': moon_pos
        })

    return results

if __name__ == '__main__':
    # Quick example
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    print(moon_position(now))

    # Calculate moon positions for all launch windows
    print("\nMoon positions for Artemis II launch windows:")
    for window in calculate_moon_positions_for_launch_windows():
        print(f"\n{window['window_start_local'].strftime('%Y-%m-%d %H:%M %Z')} - "
              f"{window['window_stop_local'].strftime('%H:%M %Z')}: "
              f"Alt={window['moon_position']['altitude_deg']:.1f}°, "
              f"Az={window['moon_position']['azimuth_deg']:.1f}°")
