import requests
from datetime import datetime, timedelta
import config

def generate_report():
    station_id = config.STATION_ID
    url = f"https://www.ndbc.noaa.gov/data/realtime2/{station_id}.txt"
    
    # OFFSET LOGIC: Convert UTC to EST (-5 Hours)
    utc_now = datetime.utcnow()
    est_now = utc_now - timedelta(hours=5)
    local_time_str = est_now.strftime("%Y-%m-%d %H:%M")

    data = {
        "wvht": 0.0, "swp": 0.0, "apd": 0.0, "wdir": "N/A", "wspd": 0.0,
        "atmp": "N/A", "wtmp": 0.0, "time": local_time_str,
        "recommendation": "NO SURF: GO SKATEBOARDING", "status_color": "#000",
        "surface_state": "UNKNOWN", "kit": "CHECK_LOCAL", "ascii_chart": "", "gauge_label": ""
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

            # DATA EXTRACTION
            data["wvht"] = get_val(8, 3.28) or 0.0
            data["swp"] = get_val(9) or 0.0
            data["apd"] = get_val(10) or 0.0
            w_dir = get_val(5)
            data["wspd"] = get_val(6, 1.94) or 0.0
            data["wind_display"] = f"{int(w_dir)}° @ {data['wspd']} KTS" if w_dir else "CALM"
            data["wtmp_val"] = get_val(14, 1.8, 32) or get_val(15, 1.8, 32)
            
            # ASCII CHART & LEGEND
            threshold = config.MIN_RIDEABLE_HEIGHT
            bars = 0
            if data["wvht"] > 0:
                bars = int((data["wvht"] / threshold) * 1.5)
                bars = max(1, min(5, bars))
            data["ascii_chart"] = ("█" * bars) + ("░" * (5 - bars))
            labels = ["FLAT/MICRO", "SMALL/LOG", "FUN/ACTIVE", "STRONG/SOLID", "HEAVY/FROTH"]
            data["gauge_label"] = labels[bars-1] if bars > 0 else "FLAT"

            # RECOMMENDATION LOGIC
            if data["wvht"] >= threshold:
                if data["swp"] >= config.LONG_PERIOD_THRESHOLD:
                    data["recommendation"] = "SURF: FROTHING"; data["status_color"] = "#00FF00"
                elif data["swp"] >= config.WIND_CHOP_MAX_PERIOD:
                    data["recommendation"] = "MAYBE: BRING THE LOG"; data["status_color"] = "#FFA500"
            else:
                data["recommendation"] = "NO SURF: GO SKATEBOARDING"; data["status_color"] = "#FF0000"

            # SURFACE STATE & KIT
            if data["wspd"] < 5: data["surface_state"] = "GLASSY"
            elif data["swp"] > (data["apd"] + 2): data["surface_state"] = "CLEAN / LINES"
            else: data["surface_state"] = "TEXTURED"

            t = data["wtmp_val"]
            if t:
                if t >= 78: data["kit"] = "SKIN / BOARDSHORTS"
                elif t >= 72: data["kit"] = "1MM TOP / SPRINGSUIT"
                elif t >= 67: data["kit"] = "3/2 FULLSUIT"
                else: data["kit"] = "4/3 FULLSUIT"

    except Exception as e:
        print(f"ERROR: {e}")

    # UI ARCHITECTURE
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>FROTHING // ST_{station_id}</title>
    <style>
        body {{ background-color: #F9F9F7; color: #000; font-family: monospace; margin: 0; padding: 40px; line-height: 1.4; }}
        .inventory {{ border: 2px solid #000; padding: 20px; max-width: 480px; background: #fff; box-shadow: 10px 10px 0px #000; }}
        .header {{ font-weight: bold; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 10px; font-size: 1.2em; }}
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
        <div class="header">FROTHING REPORT // STATION {station_id}</div>
        
        <div class="row"><span>WAVE_HEIGHT:</span><span>{data['wvht']} FT</span></div>
        <div class="row"><span>SWELL_PERIOD:</span><span>{data['swp']} SEC</span></div>
        
        <div class="chart-box">
            <div class="chart-row">
                <span>WAVE_ENERGY_GAUGE:</span>
                <span class="ascii">{data['ascii_chart']}</span>
            </div>
            <div class="gauge-legend">POWER_LEVEL: {data['gauge_label']}</div>
        </div>

        <div class="row"><span>SURFACE_STATE:</span><span>{data['surface_state']}</span></div>
        <div class="row"><span>WIND_COND:</span><span>{data['wind_display']}</span></div>
        <div class="row"><span>WATER_TEMP:</span><span>{data['wtmp_val'] if data['wtmp_val'] else 'N/A'}°F</span></div>
        <div class="row" style="border-bottom: 2px solid #000;"><span>TIMESTAMP (EST):</span><span>{data['time']}</span></div>
        
        <div class="rec-box">
            <div class="rec-label">ACTION_RECOMMENDATION</div>
            <div class="rec-val" style="background: {data['status_color']};">{data['recommendation']}</div>
        </div>

        <div class="rec-box">
            <div class="rec-label">SUGGESTED_KIT</div>
            <div class="rec-val">{data['kit']}</div>
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
