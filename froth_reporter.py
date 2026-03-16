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
        unit_code = obs['windSpeed']['unitCode']
        direction = obs['windDirection']['value']
        
        if raw_speed is None:
            return None, None

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
    
    # Time Calculations
    utc_now = datetime.utcnow()
    est_now = utc_now - timedelta(hours=5)
    local_time_str = est_now.strftime("%Y-%m-%d %H:%M")
    pulse_time = est_now.strftime("%H:%M:%S")

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

            # 3. ACTION REC (Pastel Palette)
            if data["wvht"] >= threshold:
                if data["swp"] >= config.LONG_PERIOD_THRESHOLD:
                    data["recommendation"] = "SURF: FROTHING"
                    data["status_color"] = "#B7E4C7" # Pastel Green
                else:
                    data["recommendation"] = "MAYBE: BRING THE LOG"
                    data["status_color"] = "#FFD8A8" # Pastel Orange
            else:
                data["recommendation"] = "NO SURF: GO SKATEBOARDING"
                data["status_color"] = "#FFADAD" # Pastel Red

            # 4. EQUIPMENT LOGIC
            if data["recommendation"] == "NO SURF: GO SKATEBOARDING":
                data["equipment"] = "SKATEBOARD"
            elif data["wvht"] >= 5 and (data["swp"] >= 8 or "CLEAN" in data["surface_state"]):
                data["equipment"] = "SHORTBOARD"
            else:
                data["equipment"] = "LONGBOARD"

            # 5. KITS & BEVERAGE
            if data["atmp_val"] > 70: data["beverage"] = "COLD BREW"
            elif data["atmp_val"] >= 60: data["beverage"] = "FLASH CHILL / ICED V60"
            else: data["beverage"] = "POUR OVER / V60"

            chill_factor = max(0, (nws_mph - 10) // 5) if (nws_mph and nws_mph > 10) else 0
            feels_like = data["atmp_val"] - chill_factor
            if feels_like >= 75: data["beach_kit"] = "SHIRT / SHORTS"
            elif feels_like >= 65: data["beach_kit"] = "LIGHT HOODIE"
            elif feels_like >= 55: data["beach_kit"] = "WINDBREAKER / PANTS"
            else: data["beach_kit"] = "HEAVY PARKA / BEANIE"

            t = data["wtmp_val"]
            if t >= 78: data["water_kit"] = "SKIN / BOARDSHORTS"
            elif t >= 72: data["water_kit"] = "1MM TOP / SPRINGSUIT"
            elif t >= 67: data["water_kit"] = "3/2 FULLSUIT"
            else: data["water_kit"] = "4/3 FULLSUIT"

    except Exception as e:
        print(f"ENGINE_ERROR: {e}")

# UI ARCHITECTURE
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta http-equiv="refresh" content="1800">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <title>FROTHING // {station_id}</title>
    <style>
        :root {{ --bg: #F9F9F7; --white: #ffffff; --black: #000000; --pastel: #e0e0e0; }}
        * {{ box-sizing: border-box; }}
        body {{ background-color: var(--bg); color: var(--black); font-family: monospace; margin: 0; padding: 20px; }}
        
        .main-container {{ 
            display: flex; gap: 20px; justify-content: center; align-items: flex-start; max-width: 1100px; margin: 0 auto; 
        }}

        /* REPORT SIDE */
        .inventory {{ 
            border: 2px solid var(--black); padding: 20px; width: 100%; max-width: 450px; 
            background: var(--white); box-shadow: 8px 8px 0px var(--black); 
        }}
        .header {{ font-weight: bold; border-bottom: 2px solid var(--black); padding-bottom: 10px; margin-bottom: 10px; }}
        .row {{ display: flex; justify-content: space-between; border-bottom: 1px solid var(--black); padding: 8px 0; font-size: 0.85rem; }}
        .rec-box {{ margin-top: 12px; border: 2px solid var(--black); text-align: center; font-weight: bold; }}
        .rec-label {{ font-size: 0.75rem; border-bottom: 1px solid var(--black); padding: 4px; background: #eee; }}
        .rec-val {{ padding: 12px; font-size: 1rem; text-transform: uppercase; }}

        /* CHARACTER CREATOR SIDE */
        .creator-box {{
            border: 2px solid var(--black); padding: 20px; width: 100%; max-width: 400px;
            background: var(--white); box-shadow: 8px 8px 0px var(--black); text-align: center;
        }}
        .stage {{ 
            height: 300px; border: 1px solid #ddd; margin-bottom: 20px; position: relative;
            background: #f0f0f0; display: flex; flex-direction: column; align-items: center; justify-content: center;
        }}
        .part-layer {{ font-weight: bold; font-size: 1.2rem; margin: 5px; padding: 10px; border: 1px dashed #aaa; width: 80%; background: white; }}
        
        .control-row {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; background: #f9f9f9; padding: 5px; border: 1px solid #000; }}
        .nav-btn {{ background: #000; color: #fff; border: none; padding: 5px 15px; cursor: pointer; font-family: monospace; font-weight: bold; }}
        .nav-btn:active {{ background: #444; }}
        .part-label {{ font-size: 0.8rem; text-transform: uppercase; font-weight: bold; }}

        @media (max-width: 900px) {{
            .main-container {{ flex-direction: column; align-items: center; }}
            .inventory, .creator-box {{ max-width: 100%; }}
        }}
    </style>
</head>
<body>
    <div class="main-container">
        <div class="inventory">
            <div class="header">FROTHING // STATION {station_id}</div>
            <div class="row"><span>WAVE_HEIGHT:</span><span>{data['wvht']} FT</span></div>
            <div class="row"><span>SWELL_PERIOD:</span><span>{data['swp']} SEC</span></div>
            <div class="row"><span>WIND:</span><span>{data['wind_display']}</span></div>
            <div class="row" style="border-bottom: 2px solid var(--black);"><span>TIMESTAMP:</span><span>{data['time']}</span></div>
            
            <div class="rec-box">
                <div class="rec-label">ACTION_RECOMMENDATION</div>
                <div class="rec-val" style="background: {data['status_color']};">{data['recommendation']}</div>
            </div>
            <div class="rec-box"><div class="rec-label">SUGGESTED_EQUIPMENT</div><div class="rec-val">{data['equipment']}</div></div>
            
            <div class="row" style="border: none; font-size: 0.7rem; opacity: 0.4; justify-content: center; margin-top: 15px;">
                <span>ENGINE_PULSE: {pulse_time} EST</span>
            </div>
        </div>

        <div class="creator-box">
            <div class="header">SURFER_CONSTRUCTOR_V1</div>
            
            <div class="stage" id="surfer-stage">
                <div id="display-head" class="part-layer">HEAD</div>
                <div id="display-torso" class="part-layer">TORSO</div>
                <div id="display-bottom" class="part-layer">BOTTOM</div>
                <div id="display-board" class="part-layer">BOARD</div>
            </div>

            <div id="controls"></div>
        </div>
    </div>

    <script>
        const parts = {{
            head: ["MALE_A", "MALE_B", "FEMALE_A", "FEMALE_B"],
            torso: ["WETSUIT_32", "RASH_GUARD", "BARE_CHEST", "HOODIE"],
            bottom: ["BOARDSHORTS", "WETSUIT_PANTS", "SPEEDO", "LEGGINGS"],
            board: ["FISH", "SHORTBOARD", "FUNBOARD", "LONGBOARD"]
        }};

        let selection = {{ head: 0, torso: 0, bottom: 0, board: 0 }};

        function updateDisplay() {{
            for (let type in selection) {{
                document.getElementById(`display-${{type}}`).innerText = parts[type][selection[type]];
            }}
        }}

        function cycle(type, direction) {{
            selection[type] = (selection[type] + direction + 4) % 4;
            updateDisplay();
        }}

        function createControls() {{
            const container = document.getElementById('controls');
            for (let type in parts) {{
                const row = document.createElement('div');
                row.className = 'control-row';
                row.innerHTML = `
                    <button class="nav-btn" onclick="cycle('${{type}}', -1)"><</button>
                    <span class="part-label">${{type}}</span>
                    <button class="nav-btn" onclick="cycle('${{type}}', 1)">></button>
                `;
                container.appendChild(row);
            }}
        }}

        createControls();
        updateDisplay();
    </script>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    generate_report()
