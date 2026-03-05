import requests
from datetime import datetime

def generate_report():
    station_id = "42098"
    url = f"https://www.ndbc.noaa.gov/station_page.php?station={station_id}"
    
    # 1. Setup Defaults
    data = {
        "wvht": "N/A", "swp": "N/A", "wdir": "N/A", "wspd": "N/A",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    # 2. Scrape Data
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        text = response.text

        if "Wave Height (WVHT):" in text:
            data["wvht"] = text.split("Wave Height (WVHT):")[1].split('class="data">')[1].split(' ft')[0].strip()
        
        if "Dominant Wave Period (DPD):" in text:
            data["swp"] = text.split("Dominant Wave Period (DPD):")[1].split('class="data">')[1].split(' sec')[0].strip()
            
        if "Wind Direction (WDIR):" in text:
            data["wdir"] = text.split("Wind Direction (WDIR):")[1].split('class="data">')[1].split(' (')[0].strip()

        if "Wind Speed (WSPD):" in text:
            data["wspd"] = text.split("Wind Speed (WSPD):")[1].split('class="data">')[1].split(' kts')[0].strip()
            
        print(f"SCRAPE_SUCCESS: {data['wvht']}ft @ {data['swp']}s")
            
    except Exception as e:
        print(f"SCRAPE_FAILED: {e}")

    # 3. Generate the Minitel HTML
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
            USER ASSUMES ALL RISK. VISUAL CHECK REQUIRED.
        </div>
    </div>
</body>
</html>"""

    # 4. Write to File
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("SUCCESS: index.html updated.")

if __name__ == "__main__":
    generate_report()
