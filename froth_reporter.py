import requests
from datetime import datetime
import config

def generate_report():
    station_id = config.STATION_ID
    # Fetching the 'realtime2' text file (Raw observations)
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
            # line 0 = Header, line 1 = Units, line 2 = Latest Data
            latest_row = lines[2].split()
            
            # Log the raw row to GitHub Actions console for debugging
            print(f"RAW_DATA_ROW: {latest_row}")

            # Mapping based on NOAA standard realtime2 format:
            # Index 5: WDIR, Index 6: WSPD, Index 8: WVHT, Index 9: DPD (Dominant Period)
            
            def clean_val(val, multiplier=1.0):
                if val.upper() in ["MM", "N/A", "99.00", "999"]:
                    return "N/A"
                try:
                    num = float(val)
                    return round(num * multiplier, 1)
                except:
                    return "N/A"

            # WVHT is in meters, converting to feet
            data["wvht"] = clean_val(latest_row[8], 3.28)
            data["swp"] = clean_val(latest_row[9])
            data["wdir"] = clean_val(latest_row[5])
            data["wspd"] = clean_val(latest_row[6], 1.94) # m/s to Knots

        print(f"PARSED_DATA: {data}")
            
    except Exception as e:
        print(f"ENGINE_ERROR: {e}")

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
        <div class="row"><span>WIND_COND:</span><span>{data['wdir']}@ {data['wspd']} KTS</span></div>
        <div class="row"><span>TIMESTAMP:</span><span>{data['time']}</span></div>
        <div class="legal">
            WARNING: SURFING IS DANGEROUS. INTERPRETIVE DATA ONLY. 
            USER ASSUMES ALL RISK. VISUAL CHECK REQUIRED.
        </div>
    </div>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    generate_report()
