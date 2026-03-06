import requests
from datetime import datetime
import config

def generate_report():
    station_id = config.STATION_ID
    url = f"https://www.ndbc.noaa.gov/data/realtime2/{station_id}.txt"
    
    data = {
        "wvht": "N/A", "swp": "N/A", "wdir": "N/A", "wspd": "N/A",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        lines = response.text.splitlines()

        if len(lines) >= 3:
            latest_row = lines[2].split()
            
            def clean_val(val, multiplier=1.0):
                if val.upper() in ["MM", "N/A", "99.00", "999"]:
                    return None # Return None for missing data
                try:
                    num = float(val)
                    return round(num * multiplier, 1)
                except:
                    return None

            # Wave Data
            data["wvht"] = clean_val(latest_row[8], 3.28) or "N/A"
            data["swp"] = clean_val(latest_row[9]) or "N/A"
            
            # Wind Data - 42098 specific indices: 5 (Dir), 6 (Speed)
            wind_dir = clean_val(latest_row[5])
            wind_spd = clean_val(latest_row[6], 1.94) # m/s to Knots

            if wind_dir is not None and wind_spd is not None:
                data["wind_display"] = f"{int(wind_dir)}° @ {wind_spd} KTS"
            else:
                data["wind_display"] = "OFFLINE" # Cleaner than N/A@ N/A

        print(f"PARSED_DATA: {data}")
            
    except Exception as e:
        print(f"ENGINE_ERROR: {e}")
        data["wind_display"] = "ERROR"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>FROTHING // ST_{station_id}</title>
    <style>
        body {{ background-color: #F9F9F7; color: #000000; font-family: monospace; margin: 0; padding: 40px; }}
        .inventory {{ border: 1px solid #000; padding: 20px; max-width: 450px; }}
        .row {{ display: flex; justify-content: space-between; border-bottom: 1px solid #000; padding: 5px 0; }}
        .header {{ font-weight: bold; border-bottom: 2px solid #000; margin-bottom: 10px; }}
        .legal {{ font-size: 10px; margin-top: 20px; opacity: 0.7; }}
    </style>
</head>
<body>
    <div class="inventory">
        <div class="header">FROTHING_STATION_REPORT // {station_id}</div>
        <div class="row"><span>WAVE_HEIGHT:</span><span>{data['wvht']} FT</span></div>
        <div class="row"><span>SWELL_PERIOD:</span><span>{data['swp']} SEC</span></div>
        <div class="row"><span>WIND_COND:</span><span>{data['wind_display']}</span></div>
        <div class="row"><span>TIMESTAMP:</span><span>{data['time']}</span></div>
        <div class="legal">
            WARNING: SURFING IS DANGEROUS. INTERPRETIVE DATA ONLY. 
            USER ACCUMES ALL RISK. VISUAL CHECK REQUIRED.
        </div>
    </div>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    generate_report()
