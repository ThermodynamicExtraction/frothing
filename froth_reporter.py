import requests
from datetime import datetime, timedelta
import config

def get_nws_wind():
    # Venice Municipal Airport (KVNC)
    url = "https://api.weather.gov/stations/KVNC/observations/latest"
    headers = {'User-Agent': '(frothing-engine, contact@example.com)'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        obs = r.json()['properties']
        direction = obs['windDirection']['value'] # Degrees
        speed = obs['windSpeed']['value'] # m/s
        return direction, (speed * 1.94384 if speed else 0)
    except:
        return None, None

def generate_report():
    station_id = config.STATION_ID
    buoy_url = f"https://www.ndbc.noaa.gov/data/realtime2/{station_id}.txt"
    
    # Time Setup
    utc_now = datetime.utcnow()
    est_now = utc_now - timedelta(hours=5)
    local_time_str = est_now.strftime("%Y-%m-%d %H:%M")

    # Fetch Data
    nws_dir, nws_spd = get_nws_wind()
    
    data = {
        "wvht": 0.0, "swp": 0.0, "apd": 0.0, "atmp_val": 0.0, "wtmp_val": 0.0, 
        "time": local_time_str, "status_color": "#000", "surface_state": "UNKNOWN",
        "wind_display": "OFFLINE"
    }

    try:
        r = requests.get(buoy_url, timeout=15)
        lines = r.text.splitlines()
        if len(lines) >= 3:
            row = lines[2].split()
            data["wvht"] = round(float(row[8]) * 3.28, 1) if row[8] != 'MM' else 0.0
            data["swp"] = float(row[9]) if row[9] != 'MM' else 0.0
            data["apd"] = float(row[10]) if row[10] != 'MM' else 0.0
            data["atmp_val"] = round(float(row[13]) * 1.8 + 32, 1) if row[13] != 'MM' else 0.0
            data["wtmp_val"] = round(float(row[14]) * 1.8 + 32, 1) if row[14] != 'MM' else 0.0

            # WIND INTELLIGENCE (Using NWS Venice Airport)
            if nws_dir:
                # Twin Piers Logic: Offshore is East (approx 90 deg)
                is_offshore = 45 <= nws_dir <= 135
                dir_label = "OFFSHORE" if is_offshore else "ONSHORE"
                data["wind_display"] = f"{int(nws_dir)}° @ {int(nws_spd)} KTS ({dir_label})"
                
                # SURFACE STATE LOGIC
                if nws_spd < 5: data["surface_state"] = "GLASSY"
                elif is_offshore: data["surface_state"] = "CLEAN / OFFSHORE"
                else: data["surface_state"] = "CHOPPY / ONSHORE"
            else:
                data["wind_display"] = "BUOY DATA ONLY"

            # (The rest of the Gauge, Kit, and Recommendation logic remains the same)
            # ... [Included in the final full script]

    except Exception as e: print(f"ERROR: {e}")

    # (UI remains the same Brutalist structure)
    # ...
