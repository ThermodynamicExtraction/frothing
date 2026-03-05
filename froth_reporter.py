import requests
import re
from datetime import datetime
import os

def generate_report():
    station_id = "42098"
    url = f"https://www.ndbc.noaa.gov/mobile/station.php?station={station_id}"
    
    # Default "Safety" Data
    data = {
        "wvht": "N/A",
        "swp": "N/A",
        "wdir": "N/A",
        "wspd": "N/A",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    print(f"FETCHING_STATION: {station_id}...")
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        text = response.text

        # Using Regex to find values (More stable for Minitel-style scrapers)
        wvht_match = re.search(r'Seas: ([\d.]+) ft', text)
        swp_match = re.search(r'Period: ([\d.]+) sec', text)
        wind_match = re.search(r'Wind: (\w+) at ([\d.]+) kts', text)

        if wvht_match: data["wvht"] = wvht_match.group(1)
        if swp_match: data["swp"] = swp_match.group(1)
        if wind_match:
            data["wdir"] = wind_match.group(1)
            data["wspd"] = wind_match.group(2)
            
    except Exception as e:
        print(f"WARNING: Fetch failed ({e}). Generating report with fallback data.")

    # Minitel Light Aesthetic HTML
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
        <div class="row"><span>WIND_COND:</span><span>{data['wdir']} @ {data['wspd']} KTS</span></div>
        <div class="row"><span>TIMESTAMP:</span><span>{data['time']}</span></div>
        <div class="legal">
            WARNING: SURFING IS DANGEROUS. INTERPRETIVE DATA ONLY. 
            USER ACCUMES ALL RISK. VISUAL CHECK REQUIRED.
        </div>
    </div>
</body>
</html>"""

    # Ensure we write to the current directory
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("SUCCESS: index.html has been written to disk.")

if __name__ == "__main__":
    generate_report()
