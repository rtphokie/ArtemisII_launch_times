import csv
import zoneinfo
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Union

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


def moonrise_for_date(date_or_dt: Union[date, datetime],
                      latitude: float = KSC_LAT,
                      longitude: float = KSC_LON) -> Optional[datetime]:
    """
    Return the UTC datetime of the first moonrise on the given date at (latitude, longitude).
    - date_or_dt: datetime.date or datetime.datetime (time portion ignored)
    - returns: timezone-aware UTC datetime of moonrise, or None if no rise during that UTC day
    """
    from skyfield import almanac

    if isinstance(date_or_dt, datetime):
        d = date_or_dt.date()
    elif isinstance(date_or_dt, date):
        d = date_or_dt
    else:
        raise TypeError("date_or_dt must be a datetime.date or datetime.datetime")

    start_utc = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=timezone.utc)
    end_utc = start_utc + timedelta(days=1)

    t0 = _ts.utc(start_utc)
    t1 = _ts.utc(end_utc)

    topos = Topos(latitude_degrees=latitude, longitude_degrees=longitude)
    f = almanac.risings_and_settings(_eph, _eph['moon'], topos)

    times, events = almanac.find_discrete(t0, t1, f)

    # events: 1 indicates a rise event (return the first one)
    for ti, ev in zip(times, events):
        if ev == 1:
            return ti.utc_datetime()

    return None

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

def moon_illumination(dt: datetime) -> float:
    from skyfield.api import load
    from skyfield.framelib import ecliptic_frame

    ts = load.timescale()
    # t = ts.utc(2019, 12, 9, 15, 36)
    t = _ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond / 1e6)


    sun, moon, earth = _eph["sun"], _eph["moon"], _eph["earth"]

    e = earth.at(t)
    s = e.observe(sun).apparent()
    m = e.observe(moon).apparent()

    _, slon, _ = s.frame_latlon(ecliptic_frame)
    _, mlon, _ = m.frame_latlon(ecliptic_frame)
    phase = (mlon.degrees - slon.degrees) % 360.0

    percent = 100.0 * m.fraction_illuminated(sun)

    return phase, percent


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
    - moon_position_start: dict from moon_position() function
    - moon_position_end: dict from moon_position() function
    - moonrise_utc: datetime of moonrise (UTC)
    - moonrise_local: datetime of moonrise (local timezone)
    - moon_illumination_start: float, percentage of illumination at window start
    """
    if csv_path is None:
        csv_path = Path(__file__).parent / "artemis_ii_mission_availability.csv"

    rows = load_launch_windows_from_csv(csv_path)

    tz = zoneinfo.ZoneInfo(local_tz)
    results = []

    for row in rows:
        dt_start_utc = row['window_start_utc']
        duration = int(row['duration_mins'])
        dt_end_utc = dt_start_utc + timedelta(minutes=duration)

        dt_start_local = dt_start_utc.astimezone(tz)
        dt_end_local = dt_end_utc.astimezone(tz)

        moon_pos_start = moon_position(dt_start_utc, latitude, longitude)
        moon_pos_end = moon_position(dt_end_utc, latitude, longitude)
        moonrise = moonrise_for_date(dt_start_utc.date(), latitude, longitude)
        phase, illum = moon_illumination(dt_start_utc)

        results.append(
            {
                "window_start_utc": dt_start_utc,
                "window_end_utc": dt_end_utc,
                "window_start_local": dt_start_local,
                "window_end_local": dt_end_local,
                "duration_mins": duration,
                "moon_position_start": moon_pos_start,
                "moon_position_end": moon_pos_end,
                "moonrise_utc": moonrise,
                "moonrise_local": moonrise.astimezone(tz),
                "moon_illumination": illum,
                "moon_phase": phase,
            }
        )

    return results

if __name__ == '__main__':
    # Calculate moon positions for all launch windows
    print("\nMoon positions for Artemis II & Apollo launch windows:")
    for n, window in enumerate(calculate_moon_positions_for_launch_windows()):
        moonrisedelta = window['moonrise_local'] - window['window_start_local']
        print(f"{n+1:02d}: ", end='')
        print(f"start {window['window_start_local'].strftime('%Y-%m-%d %H:%M %Z')}", end=' ')
        print(f"moonrise {window['moonrise_local'].strftime('%H:%M %Z')}", end=' ')
        print(f" ({moonrisedelta.total_seconds()/60:3.0f} into window, {window['moon_illumination']:3.0f}% illuminated)", end=' ')
        print(f"end {window['window_end_local'].strftime('%H:%M %Z')}", end=' ')
        print()
        # f"start {window['window_start_local'].strftime('%Y-%m-%d %H:%M %Z')} "
            #   f"moonrise {window['moonrise_local'].strftime('%Y-%m-%d %H:%M %Z')} "
            #   f"end {window['window_start_local'].strftime('%Y-%m-%d %H:%M %Z')} "
            #   )
