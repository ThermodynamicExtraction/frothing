import requests
from datetime import datetime
import config

def generate_report():
    station_id = config.STATION_ID
    url = f"https://www.ndbc.noaa.gov/data/realtime2/{station_id}.txt"
    
    data = {
        "wvht": 0.0, "swh": 0.0, "swp": 0.0, "swd": "N/A",
        "apd": 0.0, "wdir": "N/A", "wspd": "N/A",
        "atmp": "N/A", "wtmp": "N/A",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "recommendation": "NO_SURF", "status_color": "#000"
    }

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        lines = response.text.splitlines()

        if len(lines) >= 3:
            latest_row = lines[2].split()
            
            def get_val(idx, mult=1.0, offset=0.0):
                if idx >= len(latest_row): return None
                val = latest_row[idx]
                if val.upper() in ["MM", "N/A", "99.00", "99.0", "999"]: return None
                try: 
                    return round((float(val) * mult) + offset, 1)
                except: return None

            # 1. WAVE SPECS
            data["wvht"] = get_val(8, 3.28) or 0.0  # Sig Wave Height
            data["swp"] = get_val(9) or 0.0         # Swell Period
            data["apd"] = get_val(10) or 0.0        # Average Period
            
            # 2. WIND SPECS (Indices 5 & 6)
            w_dir = get_val(5)
            w_spd = get_val(6, 1.94) # m/s to Kts
            data["wind_display"] = f"{int(w_dir)}° @ {w_spd} KTS" if w_dir and w_spd else "CALM"

            # 3. TEMPERATURE SPECS (Search logic for 42098)
            # Try standard indices first (14 & 15), then backup (13 & 14)
            data["atmp"] = get_val(13, 1.8, 32) or get_val(14, 1.8, 32) or "N/A"
            data["wtmp"] = get_val(14, 1.8, 32) or get_val(15, 1.8, 32) or "N/A"

            # 4. RECOMMENDATION ENGINE
            if data["wvht"] >= config.MIN_RIDEABLE_HEIGHT:
                if data["swp"] >= config.LONG_PERIOD_THRESHOLD:
                    data["recommendation"] = "SURF: FROTHING"
                    data["status_color"] = "#00FF00"
                elif data["swp"] >= config.WIND_CHOP_MAX_PERIOD:
                    data["recommendation"] = "MAYBE: BRING THE LOG"
                    data["status_color"] = "#FFA500"
            else:
                data["recommendation"] = "NO_SURF: STAY HOME"
                data["status_color"] = "#FF0000"

    except Exception as e:
        print(f"ENGINE_ERROR: {e}")

    # Minitel Design with All Specs
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>FROTHING // ST_{station_id}</title>
    <style>
        body {{ background-color: #F9F9F7; color: #000; font-family: monospace; margin: 0; padding: 40px; line-height: 1.4; }}
        .inventory {{ border: 2px solid #000; padding: 20px; max-width: 480px; background: #fff; box-shadow: 10px 10px 0px #000; }}
        .header {{ font-weight: bold; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 10px; font-size: 1.2em; }}
        .row {{ display: flex; justify-content: space-between; border-bottom: 1px solid #000; padding: 4px 0; }}
        .rec {{ margin-top: 20px; padding: 15px; border: 2px solid #000; text-align: center; font-weight: bold; font-size: 1.2em; text-transform: uppercase; }}
        .legal {{ font-size: 9px; margin-top: 20px; opacity: 0.6; text-transform: uppercase; }}
    </style>
</head>
<body>
    <div class="inventory">
        <div class="header">FROTHING_STATION_REPORT // {station_id}</div>
        
        <div class="row"><span>SIG_WAVE_HEIGHT:</span><span>{data['wvht']} FT</span></div>
        <div class="row"><span>SWELL_PERIOD:</span><span>{data['swp']} SEC</span></div>
        <div class="row"><span>AVG_PERIOD (APD):</span><span>{data['apd']} SEC</span></div>
        <div class="row"><span>WIND_COND:</span><span>{data['wind_display']}</span></div>
        
        <div class="row"><span>AIR_TEMP:</span><span>{data['atmp']}°F</span></div>
        <div class="row"><span>WATER_TEMP:</span><span>{data['wtmp']}°F</span></div>
        
        <div class="row" style="border-bottom: 2px solid #000;"><span>TIMESTAMP:</span><span>{data['time']}</span></div>
        
        <div class="rec" style="background: {data['status_color']};">
            {data['recommendation']}
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
