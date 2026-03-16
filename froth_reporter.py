import requests
from datetime import datetime, timedelta
import config

def get_nws_wind():
    """Fetches wind from KVNC with improved reliability using observation list."""
    url = "https://api.weather.gov/stations/KVNC/observations?limit=1"
    headers = {'User-Agent': '(frothing-engine, contact@example.com)'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        obs = data['features'][0]['properties']
        
        raw_speed = obs['windSpeed']['value']
        unit_code = obs['windSpeed']['unitCode']
        direction = obs['windDirection']['value']
        
        if raw_speed is None:
            if direction is None: return None, None
            raw_speed = 0.0 # Calm

        speed_mph = raw_speed * 2.23694 if "m_s" in unit_code else (raw_speed * 0.621371 if "km_h" in unit_code else raw_speed)
        return direction, speed_mph
    except Exception as e:
        print(f"NWS_ERROR: {e}")
        return None, None

def get_cardinal(d):
    if d is None: return "N/A"
    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    return dirs[round(d / (360. / len(dirs))) % len(dirs)]

def generate_report():
    station_id = config.STATION_ID
    buoy_url = f"https://www.ndbc.noaa.gov/data/realtime2/{station_id}.txt"
    
    utc_now = datetime.utcnow()
    est_now = utc_now - timedelta(hours=5)
    local_time_str = est_now.strftime("%Y-%m-%d %H:%M")
    pulse_time = est_now.strftime("%H:%M:%S")

    nws_dir, nws_mph = get_nws_wind()
    data = {
        "wvht": 0.0, "swp": 0.0, "time": local_time_str, "status_color": "#EEE", 
        "surface_state": "CHECK_CAM", "wind_display": "OFFLINE", 
        "equipment": "LONGBOARD", "recommendation": "NO SURF: GO SKATEBOARDING"
    }

    try:
        r = requests.get(buoy_url, timeout=15)
        r.raise_for_status()
        row = r.text.splitlines()[2].split()
        data["wvht"] = round(float(row[8]) * 3.28, 1) if row[8] != "MM" else 0.0
        data["swp"] = float(row[9]) if row[9] != "MM" else 0.0
        data["atmp_val"] = round(float(row[13]) * 1.8 + 32, 1) if row[13] != "MM" else 0.0
        data["wtmp_val"] = round(float(row[14]) * 1.8 + 32, 1) if row[14] != "MM" else 0.0

        if nws_dir is not None:
            cardinal = get_cardinal(nws_dir)
            is_offshore = 20 <= nws_dir <= 140
            data["wind_display"] = f"{cardinal} {int(round(nws_mph))} MPH ({'OFFSHORE' if is_offshore else 'ONSHORE'})"
            if nws_mph < 6: data["surface_state"] = "GLASSY"
            elif is_offshore: data["surface_state"] = "CLEAN / LINES"
            else: data["surface_state"] = "CHOPPY / BLOWN OUT"

        threshold = config.MIN_RIDEABLE_HEIGHT
        if data["wvht"] >= threshold:
            if data["swp"] >= config.LONG_PERIOD_THRESHOLD:
                data["recommendation"] = "SURF: FROTHING"; data["status_color"] = "#B7E4C7"
            else:
                data["recommendation"] = "MAYBE: BRING THE LOG"; data["status_color"] = "#FFD8A8"
        else:
            data["recommendation"] = "NO SURF: GO SKATEBOARDING"; data["status_color"] = "#FFADAD"
        
        data["equipment"] = "SKATEBOARD" if "SKATEBOARDING" in data["recommendation"] else ("SHORTBOARD" if data["wvht"] >= 5 else "LONGBOARD")

    except Exception as e: print(f"ENGINE_ERROR: {e}")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta http-equiv="refresh" content="1800">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <title>FROTHING // {station_id}</title>
    <style>
        :root {{ --bg: #F9F9F7; --white: #ffffff; --black: #000000; }}
        * {{ box-sizing: border-box; }}
        body {{ background-color: var(--bg); color: var(--black); font-family: monospace; margin: 0; padding: 20px; }}
        .main-container {{ display: flex; gap: 20px; justify-content: center; align-items: flex-start; max-width: 1000px; margin: 0 auto; }}
        
        .inventory, .creator-box {{ 
            border: 2px solid var(--black); padding: 20px; background: var(--white); 
            box-shadow: 8px 8px 0px var(--black); width: 100%;
        }}
        .inventory {{ max-width: 450px; }}
        .creator-box {{ max-width: 400px; text-align: center; }}
        
        .header {{ font-weight: bold; border-bottom: 2px solid var(--black); padding-bottom: 10px; margin-bottom: 10px; }}
        .row {{ display: flex; justify-content: space-between; border-bottom: 1px solid var(--black); padding: 8px 0; font-size: 0.85rem; }}
        .rec-box {{ margin-top: 12px; border: 2px solid var(--black); text-align: center; font-weight: bold; }}
        .rec-label {{ font-size: 0.75rem; border-bottom: 1px solid var(--black); padding: 4px; background: #eee; }}
        .rec-val {{ padding: 12px; font-size: 1rem; text-transform: uppercase; }}

        /* CHARACTER SYSTEM */
        .stage {{ height: 320px; margin-bottom: 20px; position: relative; background: #f0f0f0; border: 1px solid #000; overflow: hidden; }}
        .avatar-part {{ position: absolute; left: 50%; transform: translateX(-50%); transition: all 0.2s; }}
        
        #display-head {{ top: 30px; width: 50px; height: 50px; border-radius: 50%; border: 2px solid #000; z-index: 4; }}
        #display-torso {{ top: 80px; width: 70px; height: 80px; border: 2px solid #000; z-index: 3; border-radius: 5px; }}
        #display-bottom {{ top: 160px; width: 70px; height: 60px; border: 2px solid #000; z-index: 2; }}
        #display-board {{ top: 40px; left: 75%; width: 40px; height: 240px; border: 2px solid #000; border-radius: 50% 50% 20% 20%; z-index: 1; }}

        .control-row {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border: 1px solid #000; padding: 4px; }}
        .nav-btn {{ background: #000; color: #fff; border: none; padding: 5px 12px; cursor: pointer; font-weight: bold; }}
        .part-label {{ font-size: 0.7rem; text-transform: uppercase; font-weight: bold; }}
        .selection-name {{ font-size: 0.75rem; color: #555; }}

        @media (max-width: 850px) {{ .main-container {{ flex-direction: column; align-items: center; }} }}
    </style>
</head>
<body>
    <div class="main-container">
        <div class="inventory">
            <div class="header">FROTHING // {station_id}</div>
            <div class="row"><span>WAVE_HEIGHT:</span><span>{data['wvht']} FT</span></div>
            <div class="row"><span>SWELL_PERIOD:</span><span>{data['swp']} SEC</span></div>
            <div class="row"><span>SURFACE:</span><span>{data['surface_state']}</span></div>
            <div class="row"><span>WIND:</span><span>{data['wind_display']}</span></div>
            <div class="row" style="border-bottom: 2px solid var(--black);"><span>PULSE (EST):</span><span>{pulse_time}</span></div>
            
            <div class="rec-box"><div class="rec-label">RECOMMENDATION</div><div class="rec-val" style="background: {data['status_color']};">{data['recommendation']}</div></div>
            <div class="rec-box"><div class="rec-label">EQUIPMENT</div><div class="rec-val">{data['equipment']}</div></div>
        </div>

        <div class="creator-box">
            <div class="header">SURFER_CONSTRUCTOR</div>
            <div class="stage">
                <div id="display-board" class="avatar-part"></div>
                <div id="display-head" class="avatar-part"></div>
                <div id="display-torso" class="avatar-part"></div>
                <div id="display-bottom" class="avatar-part"></div>
            </div>
            <div id="controls"></div>
        </div>
    </div>

    <script>
        const config = {{
            head: [
                {{ name: "MALE_A", color: "#FFDBAC" }}, {{ name: "MALE_B", color: "#8D5524" }},
                {{ name: "FEMALE_A", color: "#F1C27D" }}, {{ name: "FEMALE_B", color: "#C68642" }}
            ],
            torso: [
                {{ name: "VINTAGE_TEE", color: "#FFADAD" }}, {{ name: "WETSUIT_32", color: "#222" }},
                {{ name: "RASH_GUARD", color: "#A0C4FF" }}, {{ name: "HOODIE", color: "#9BF6FF" }}
            ],
            bottom: [
                {{ name: "BOARDSHORTS", color: "#CAFFBF" }}, {{ name: "WETSUIT_LEG", color: "#222" }},
                {{ name: "SPEEDO", color: "#FDFFB6" }}, {{ name: "LEGGINGS", color: "#FFD6A5" }}
            ],
            board: [
                {{ name: "FISH", color: "#FFC6FF", h: "180px" }}, {{ name: "SHORT", color: "#FFFFFC", h: "210px" }},
                {{ name: "FUN", color: "#BDB2FF", h: "250px" }}, {{ name: "LONG", color: "#99E2B4", h: "300px" }}
            ]
        }};

        let selection = {{ head: 0, torso: 0, bottom: 0, board: 0 }};

        function update() {{
            for (let type in selection) {{
                const el = document.getElementById(`display-${{type}}`);
                const item = config[type][selection[type]];
                el.style.backgroundColor = item.color;
                if(item.h) el.style.height = item.h;
                document.getElementById(`label-${{type}}`).innerText = item.name;
            }}
        }}

        function cycle(type, dir) {{
            selection[type] = (selection[type] + dir + 4) % 4;
            update();
        }}

        const ctrl = document.getElementById('controls');
        for (let type in config) {{
            const row = document.createElement('div');
            row.className = 'control-row';
            row.innerHTML = `<button class="nav-btn" onclick="cycle('${{type}}',-1)"><</button>
                             <div style="display:flex; flex-direction:column;">
                                <span class="part-label">${{type}}</span>
                                <span class="selection-name" id="label-${{type}}"></span>
                             </div>
                             <button class="nav-btn" onclick="cycle('${{type}}',1)">></button>`;
            ctrl.appendChild(row);
        }}
        update();
    </script>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    generate_report()
