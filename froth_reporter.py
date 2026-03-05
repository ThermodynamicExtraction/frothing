import requests
import re
from datetime import datetime

def generate_report():
    station_id = "42098"
    # Switching to the standard report page which is often more stable than 'mobile'
    url = f"https://www.ndbc.noaa.gov/station_page.php?station={station_id}"
    
    data = {
        "wvht": "N/A", "swp": "N/A", "wdir": "N/A", "wspd": "N/A",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        text = response.text

        # 42098 specific patterns - looking for the raw text in the table cells
        # We use [^<]+ to grab everything inside the <td> until the next tag
        wvht = re.search(r'Wave Height \(WVHT\):.*?<td class="data">([^<]+)</td>', text, re.S)
        swp = re.search(r'Dominant Wave Period \(DPD\):.*?<td class="data">([^<]+)</td>', text, re.S)
        wdir = re.search(r'Wind Direction \(WDIR\):.*?<td class="data">(\w+)', text, re.S)
        wspd = re.search(r'Wind Speed \(WSPD\):.*?<td class="data">([^<]+) kts', text, re.S)

        if wvht: data["wvht"] = wvht.group(1).strip()
        if swp: data["swp"] = swp.group(1).strip()
        if wdir: data["wdir"] = wdir.group(1).strip()
        if wspd: data["wspd"] = wspd.group(1).strip()
            
        print(f"SCRAPE_RESULT: {data['wvht']} ft @ {data['swp']} sec")
            
    except Exception as e:
        print(f"FETCH_ERROR: {e}")

    # ... [Keep your existing HTML generation code here] ...
