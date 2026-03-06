import requests
from datetime import datetime
import config

def generate_report():
    station_id = config.STATION_ID
    url = f"https://www.ndbc.noaa.gov/data/realtime2/{station_id}.txt"
    
    data = {
        "wvht": 0.0, "swp": 0.0, "apd": 0.0, "wdir": "N/A", "wspd": 0.0,
        "atmp": "N/A", "wtmp": 0.0, "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "recommendation": "NO_SURF", "status_color": "#000",
        "surface_state": "UNKNOWN", "kit": "CHECK_LOCAL"
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
                try: return round((float(val) * mult) + offset, 1)
                except: return None

            # 1. CORE SPECS
            data["wvht"] = get_val(8, 3.28) or 0.0
            data["swp"] = get_val(9) or 0.0
            data["apd"] = get_val(10) or 0.0
            w_dir = get_val(5)
            data["wspd"] = get_val(6, 1.94) or 0.0 # Knots
            data["wind_display"] = f"{int(w_dir)}° @ {data['wspd']} KTS" if w_dir else "CALM"

            # 2. TEMPERATURES
            raw_atmp = get_val(13, 1.8, 32) or get_val(14, 1.8, 32)
            raw_wtmp = get_val(14, 1.8, 32) or get_val(15, 1.8, 32)
            data["atmp"] = f"{raw_atmp}°F" if raw_atmp else "N/A"
            data["wtmp_val"] = raw_wtmp # Keep as float for logic

            # 3. SURFACE STATE LOGIC
            if data["wspd"] < 5:
                data["surface_state"] = "GLASSY"
            elif data["swp"] > (data["apd"] + 2):
                data["surface_state"] = "CLEAN / LINES"
            elif data["wspd"] > 12:
                data["surface_state"] = "CHOPPY / BLOWN OUT"
            else:
                data["surface_state"] = "TEXTURED"

            # 4. WETSUIT LOGIC (KIT)
            t = data["wtmp_val"]
            if t:
                if t >= 78: data["kit"] = "SKIN / BOARDSHORTS"
                elif t >= 72: data["kit"] = "1MM TOP / SPRINGSUIT"
                elif t >= 67: data["kit"] = "3/2 FULLSUIT"
                elif t >= 62: data["kit"] = "4/3 FULLSUIT"
                else: data["kit"] = "4/3 + BOOTIES"
            else:
                data["kit"] = "DATA_OFFLINE"

            # 5. SURF RECOMMENDATION
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

    # BRUTALIST MINITEL OUTPUT
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
        .rec-box {{ margin-top: 15px; border: 2px solid #000; text-align: center; font-weight: bold; overflow: hidden; }}
        .rec-label {{ font-size: 0.8em; border-bottom: 1px solid #000; padding: 2px; background: #eee; }}
        .rec-val {{ padding: 10px; font-size: 1.1em; text-transform: uppercase; }}
        .legal {{ font-size: 9px; margin-top: 20px; opacity: 0.6; text-transform: uppercase; }}
    </style>
</head>
<body>
    <div class="inventory">
        <div class="header">FROTHING_STATION_REPORT // {station_id}</div>
        
        <div class="row"><span>WAVE_HEIGHT:</span><span>{data['wvht']} FT</span></div>
        <div class="row"><span>SWELL_PERIOD:</span><span>{data['swp']} SEC</span></div>
        <div class="row"><span>SURFACE_STATE:</span><span>{data['surface_state']}</span></div>
        <div class="row"><span>WIND_COND:</span><span>{data['wind_display']}</span></div>
        <div class="row"><span>WATER_TEMP:</span><span>{data['wtmp_val'] if data['wtmp_val'] else 'N/A'}°F</span></div>
        <div class="row" style="border-bottom: 2px solid #000;"><span>TIMESTAMP:</span><span>{data['time']}</span></div>
        
        <div class="rec-box">
            <div class="rec-label">ACTION_RECOMMENDATION</div>
            <div class="rec-val" style="background: {data['status_color']};">{data['recommendation']}</div>
        </div>

        <div class="rec-box">
            <div class="rec-label">SUGGESTED_KIT</div>
            <div class="rec-val" style="background: #fff;">{data['kit']}</div>
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
