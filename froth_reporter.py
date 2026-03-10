import requests
from datetime import datetime, timedelta
import config

def get_nws_wind():
    """Fetches latest wind from Venice Municipal Airport (KVNC) with unit safety."""
    url = "https://api.weather.gov/stations/KVNC/observations/latest"
    # User-Agent is required by NWS API to avoid 403 Forbidden errors
    headers = {'User-Agent': '(frothing-engine, contact@example.com)'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        obs = r.json()['properties']
        
        raw_speed = obs['windSpeed']['value']
        unit_code = obs['windSpeed']['unitCode']
        direction = obs['windDirection']['value']
        
        if raw_speed is None:
            return None, None

        # Unit Conversion Logic (m/s vs km/h)
        if "m_s" in unit_code:
            speed_mph = raw_speed * 2.23694
        elif "km_h" in unit_code:
            speed_mph = raw_speed * 0.621371
        else:
            speed_mph = raw_speed 
            
        return direction, speed_mph
    except Exception as e:
        print(f"NWS_ERROR: {e}")
        return None, None

def get_cardinal(d):
    """Converts degrees to human-readable cardinal directions."""
    if d is None: return "N/A"
    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
            'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    ix = round(d / (360. / len(dirs)))
    return dirs[ix % len(dirs)]

def generate_report():
    station_id = config.STATION_ID
    buoy_url = f"https://www.ndbc.noaa.gov/data/realtime2/{station_id}.txt"
    
    # Time Setup: EST Offset
    utc_now = datetime.utcnow()
    est_now = utc_now - timedelta(hours=5)
    local_time_str = est_now.strftime("%Y-%m-%d %H:%M")

    nws_dir, nws_mph = get_nws_wind()
    
    data = {
        "wvht": 0.0, "swp": 0.0, "apd": 0.0, "atmp_val": 0.0, "wtmp_val": 0.0, 
        "time": local_time_str, "status_color": "#EEE", "surface_state": "UNKNOWN",
        "wind_display": "OFFLINE", "water_kit": "CHECK_LOCAL", 
        "beach_kit": "STAY_WARM", "beverage": "POUR OVER", "equipment": "LONGBOARD",
        "ascii_chart": "", "gauge_label": "", "recommendation": "NO SURF: GO SKATEBOARDING"
    }

    try:
        r = requests.get(buoy_url, timeout=15)
        r.raise_for_status()
        lines = r.text.splitlines()
        
        if len(lines) >= 3:
            row = lines[2].split()
            
            def get_val(idx, mult=1.0, offset=0.0):
                if idx >= len(row) or row[idx].upper() in ["MM", "N/A"]: return None
                return round((float(row[idx]) * mult) + offset, 1)

            data["wvht"] = get_val(8, 3.28) or 0.0
            data["swp"] = get_val(9) or 0.0
            data["apd"] = get_val(10) or 0.0
            data["atmp_val"] = get_val(13, 1.8, 32) or 0.0
            data["wtmp_val"] = get_val(14, 1.8, 32) or 0.0

            # 1. WIND & SURFACE STATE
            if nws_dir is not None:
                cardinal = get_cardinal(nws_dir)
                is_offshore = 20 <= nws_dir <= 140
                dir_label = "OFFSHORE" if is_offshore else "ONSHORE"
                data["wind_display"] = f"{cardinal} {int(round(nws_mph))} MPH ({dir_label})"
                
                if nws_mph < 6: 
                    data["surface_state"] = "GLASSY"
                elif is_offshore: 
                    data["surface_state"] = "CLEAN / LINES"
                else: 
                    data["surface_state"] = "CHOPPY / BLOWN OUT"
            else:
                data["wind_display"] = "KVNC_OFFLINE"

            # 2. GAUGE LOGIC
            threshold = config.MIN_RIDEABLE_HEIGHT
            bars = max(1, min(5, int((data["wvht"] / threshold) * 1.5))) if data["wvht"] > 0 else 0
            data["ascii_chart"] = ("█" * bars) + ("░" * (5 - bars))
            labels = ["FLAT/MICRO", "SMALL/LOG", "FUN/ACTIVE", "STRONG/SOLID", "HEAVY/FROTH"]
            data["gauge_label"] = labels[bars-1] if bars > 0 else "FLAT"

            # 3. ACTION RECOMMENDATION (Pastel Palette)
            if data["wvht"] >= threshold:
                if data["swp"] >= config.LONG_PERIOD_THRESHOLD:
                    data["recommendation"] = "SURF: FROTHING"
                    data["status_color"] = "#B7E4C7" # Pastel Green
                else:
                    data["recommendation"] = "MAYBE: BRING THE LOG"
                    data["status_color"] = "#FFD8A8" # Pastel Orange
            else:
                data["recommendation"] = "NO SURF: GO SKATEBOARDING"
                data["
