import requests
from datetime import datetime

def generate_report():
    station_id = "42098"
    # The 'Real-Time' text page is much easier for a bot to read than the flashy dashboard
    url = f"https://www.ndbc.noaa.gov/data/realtime2/{station_id}.txt"
    
    data = {
        "wvht": "N/A", "swp": "N/A", "wdir": "N/A", "wspd": "N/A",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    try:
        # We fetch the raw data file directly. It looks like a spreadsheet.
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        lines = response.readlines()

        # The second line is the header, the third line is the most recent data
        if len(lines) >= 3:
            latest_data = lines[2].decode('utf-8').split()
            # Column mapping for NOAA .txt files:
            # 5: WDIR, 6: WSPD, 8: WVHT, 9: DPD (Period)
            data["wvht"] = latest_data[8]
            data["swp"] = latest_data[9]
            data["wdir"] = latest_data[5]
            data["wspd"] = latest_data[6]
            
        print(f"SCRAPE_SUCCESS: {data['wvht']}ft @ {data['swp']}s")
            
    except Exception as e:
        print(f"SCRAPE_FAILED: {e}")

    # Generate the Minitel HTML
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
        <div class="row"><span>WAVE_HEIGHT:</span><span>{data['wvht']} M</span></div>
        <div class="row"><span>SWELL_PERIOD:</span><span>{data['swp']} SEC</span></div>
        <div class="row"><span>WIND_COND:</span><span>{data['wdir']} @ {data['wspd']} KTS</span></div>
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
