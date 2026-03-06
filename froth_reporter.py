import requests
from datetime import datetime
import config

def generate_report():
    station_id = config.STATION_ID
    url = f"https://www.ndbc.noaa.gov/data/realtime2/{station_id}.txt"
    
    data = {
        "wvht": 0.0, "swp": 0.0, "apd": 0.0, "wdir": "N/A", "wspd": "N/A",
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
            
            def clean(val, mult=1.0, offset=0.0):
                if val.upper() in ["MM", "N/A", "99.00", "99.0", "999"]: return None
                try: 
                    num = float(val)
                    return round((num * mult) + offset, 1)
                except: return None

            # Wave & Wind Data
            data["wvht"] = clean(latest_row[8], 3.28) or 0.0
            data["swp"] = clean(latest_row[9]) or 0.0
            data["apd"] = clean(latest_row[10]) or 0.0
            
            w_dir = clean(latest_row[5])
            w_spd = clean(latest_row[6], 1.94)
            data["wind_display"] = f"{int(w_dir)}° @ {w_spd} KTS" if w_dir and w_spd else "OFFLINE"

            # Temperature Data (Celsius to Fahrenheit: (C * 9/5) + 32)
            data["atmp"] = clean(latest_row[14], 1.8, 32) or "N/A"
            data["wtmp"] = clean(latest_row[15], 1.8, 32) or "N/A"

            # RECOMMENDATION ENGINE
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

    # Generate the Minitel HTML with updated Inventory
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>FROTHING // ST_{station_id}</title>
    <style>
        body {{ background-color: #F9F9F7; color: #000; font-family: monospace; margin: 0; padding: 40px; }}
        .inventory {{ border: 2px solid #000; padding: 20px; max-width: 450px; background: #fff; }}
        .header {{ font-weight: bold; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 10px; font-size: 1.2em; }}
        .row {{ display: flex; justify-content: space-between; border-bottom: 1px solid #eee; padding: 6px 0; }}
        .temp-row {{ display: flex; gap: 20px; justify-content: space-between; margin-top: 5px; border-bottom: 1px solid #eee; padding: 6px 0; }}
        .rec {{ margin-top: 20px; padding: 15px; border: 2px solid #000; text-align: center; font-weight: bold; font-size: 1.1em; }}
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
        
        <div class="temp-row">
            <span>AIR_TEMP: {data['atmp']}°F</span>
            <span>WATER_TEMP: {data['wtmp']}°F</span>
        </div>

        <div class="row"><span>TIMESTAMP:</span><span>{data['time']}</span></div>
        
        <div class="rec" style="background: {data['status_color']}; color: #000;">
            {data['recommendation']}
        </div>

        <div class="legal">
            WARNING: DATA IS INTERPRETIVE. SURFING CARRIES INHERENT RISK. 
            CHECK LOCAL CONDITIONS VISUALLY.
        </div>
    </div>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    generate_report()
