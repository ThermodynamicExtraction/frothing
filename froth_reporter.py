import requests
from datetime import datetime, timedelta
import config

def get_nws_wind():
    """Fetches latest wind from Venice Municipal Airport (KVNC) with unit safety."""
    url = "https://api.weather.gov/stations/KVNC/observations/latest"
    headers = {'User-Agent': '(frothing-engine, contact@example.com)'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        obs = r.json()['properties']
        
        raw_speed = obs['windSpeed']['value']
        unit_code = obs['windSpeed']['unitCode'] # e.g., "wmoUnit:m_s-1"
        direction = obs['windDirection']['value']
        
        if raw_speed is None:
            return None, None

        # Unit Conversion Logic to prevent inflated values
        if "m_s" in unit_code:
            speed_mph = raw_speed * 2.23694
        elif "km_h" in unit_code:
            speed_mph = raw_speed * 0.621371
        else:
            speed_mph = raw_speed # Fallback
            
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
    
    # Time Setup: EST Offset (-5)
    utc_now = datetime.utcnow()
    est_now = utc_now - timedelta(hours=5)
    local_time_str = est_now.strftime("%Y-%m-%d %H:%M")

    # Fetch Data
    nws_dir, nws_mph = get_nws_wind()
    
    data = {
        "wvht": 0.0, "swp": 0.0, "apd": 0.0, "atmp_val": 0.0, "wtmp_val": 0.0, 
        "time": local_time_str, "status_color": "#000", "surface_state": "UNKNOWN",
        "wind_display": "OFFLINE", "water_kit": "CHECK_LOCAL", 
        "beach_kit": "STAY_WARM", "beverage": "POUR OVER",
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

            # 1. CONTEXTUAL WIND LOGIC
            if nws_dir is not None:
                cardinal = get_cardinal(nws_dir)
                # Twin Piers Offshore: 20° to 140° (NE to SE)
                is_offshore = 20 <= nws_dir <= 140
                dir_label = "OFFSHORE" if is_offshore else "ONSHORE"
                
                data["wind_display"] = f"{cardinal} {int(round(nws_mph))} MPH ({dir_label})"
                
                # SURFACE STATE LOGIC
                if nws_mph < 6: data["surface_state"] = "GLASSY"
                elif is_offshore: data["surface_state"] = "CLEAN / LINES"
                else: data["surface_state"] = "CHOPPY / BLOWN OUT"
            else:
                data["wind_display"] = "KVNC_OFFLINE"

            # 2. GAUGE LOGIC
            threshold = config.MIN_RIDEABLE_HEIGHT
            bars = max(1, min(5, int((data["wvht"] / threshold) * 1.5))) if data["wvht"] > 0 else 0
            data["ascii_chart"] = ("█" * bars) + ("░" * (5 - bars))
            labels = ["FLAT/MICRO", "SMALL/LOG", "FUN/ACTIVE", "STRONG/SOLID", "HEAVY/FROTH"]
            data["gauge_label"] = labels[bars-1] if bars > 0 else "FLAT"

            # 3. KITS & BEVERAGE
            if data["atmp_val"] > 70: data["beverage"] = "COLD BREW"
            elif data["atmp_val"] >= 60: data["beverage"] = "FLASH CHILL / ICED V60"
            else: data["beverage"] = "POUR OVER / V60"

            # BEACH KIT LOGIC (WIND CHILL)
            chill_factor = max(0, (nws_mph - 10) // 5) if nws_mph and nws_mph > 10 else 0
            feels_like = data["atmp_val"] - chill_factor
            if feels_like >= 75: data["beach_kit"] = "SHIRT / SHORTS"
            elif feels_like >= 65: data["beach_kit"] = "LIGHT HOODIE"
            elif feels_like >= 55: data["beach_kit"] = "WINDBREAKER / PANTS"
            else: data["beach_kit"] = "HEAVY PARKA / BEANIE"

            # WATER KIT LOGIC
            t = data["wtmp_val"]
            if t >= 78: data["water_kit"] = "SKIN / BOARDSHORTS"
            elif t >= 72: data["water_kit"] = "1MM TOP / SPRINGSUIT"
            elif t >= 67: data["water_kit"] = "3/2 FULLSUIT"
            else: data["water_kit"] = "4/3 FULLSUIT"

            # 4. ACTION RECOMMENDATION
            if data["wvht"] >= threshold:
                if data["swp"] >= config.LONG_PERIOD_THRESHOLD:
                    data["recommendation"] = "SURF: FROTHING"; data["status_color"] = "#00FF00"
                else:
                    data["recommendation"] = "MAYBE: BRING THE LOG"; data["status_color"] = "#FFA500"
            else:
                data["recommendation"] = "NO SURF: GO SKATEBOARDING"; data["status_color"] = "#FF0000"

    except Exception as e:
        print(f"ENGINE_ERROR: {e}")

    # UI ARCHITECTURE
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>FROTHING // {station_id}</title>
    <style>
        body {{ background-color: #F9F9F7; color: #000; font-family: monospace; margin: 0; padding: 40px; line-height: 1.4; }}
        .inventory {{ border: 2px solid #000; padding: 20px; max-width: 550px; background: #fff; box-shadow: 10px 10px 0px #000; }}
        .header {{ font-weight: bold; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 10px; font-size: 1.1em; }}
        .row {{ display: flex; justify-content: space-between; border-bottom: 1px solid #000; padding: 6px 0; }}
        .chart-box {{ border-bottom: 2px solid #000; padding: 10px 0; }}
        .chart-row {{ display: flex; justify-content: space-between; align-items: center; }}
        .ascii {{ font-size: 1.5em; letter-spacing: 2px; }}
        .gauge-legend {{ font-size: 0.75em; text-align: right; color: #666; margin-top: -2px; }}
        .rec-box {{ margin-top: 15px; border: 2px solid #000; text-align: center; font-weight: bold; }}
        .rec-label {{ font-size: 0.8em; border-bottom: 1px solid #000; padding: 2px; background: #eee; }}
        .rec-val {{ padding: 10px; font-size: 1.1em; text-transform: uppercase; }}
        .legal {{ font-size: 9px; margin-top: 20px; opacity: 0.6; text-transform: uppercase; }}
    </style>
</head>
<body>
    <div class="inventory">
        <div class="header">FROTHING REPORT // STATION {station_id} // TWIN PIERS, LBK, FL</div>
        
        <div class="row"><span>WAVE_HEIGHT:</span><span>{data['wvht']} FT</span><span>SWELL_PERIOD:</span><span>{data['swp']} SEC</span></div>
        
        <div class="chart-box">
            <div class="chart-row">
                <span>WAVE_ENERGY_GAUGE:</span>
                <span class="ascii">{data['ascii_chart']}</span>
            </div>
            <div class="gauge-legend">POWER_LEVEL: {data['gauge_label']}</div>
        </div>

        <div class="row"><span>SURFACE_STATE:</span><span>{data['surface_state']}</span></div>
        <div class="row"><span>WIND_COND:</span><span>{data['wind_display']}</span></div>
        <div class="row"><span>AIR_TEMP:</span><span>{data['atmp_val']}°F</span></div>
        <div class="row"><span>WATER_TEMP:</span><span>{data['wtmp_val']}°F</span></div>
        <div class="row" style="border-bottom: 2px solid #000;"><span>TIMESTAMP (EST):</span><span>{data['time']}</span></div>
        
        <div class="rec-box">
            <div class="rec-label">ACTION_RECOMMENDATION</div>
            <div class="rec-val" style="background: {data['status_color']};">{data['recommendation']}</div>
        </div>

        <div class="rec-box">
            <div class="rec-label">SUGGESTED_WATER_KIT</div>
            <div class="rec-val">{data['water_kit']}</div>
        </div>

        <div class="rec-box">
            <div class="rec-label">SUGGESTED_BEACH_KIT</div>
            <div class="rec-val">{data['beach_kit']}</div>
        </div>

        <div class="rec-box">
            <div class="rec-label">SUGGESTED_BEVERAGE</div>
            <div class="rec-val">{data['beverage']}</div>
        </div>

        <div class="legal">
            WARNING: DATA IS INTERPRETIVE. SURFING CARRIES RISK. 
            CHECK LOCAL CONDITIONS VISUALLY BEFORE ENTRY.
        </div>
    </div>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    generate_report()
