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

        # Improved Regex: Looks for the numeric value following common NOAA labels
        # wvht: Significant Wave Height (ft)
        wvht = re.search(r'Wave Height \(WVHT\):</td><td class="data">([\d.]+) ft', text)
        # swp: Dominant Wave Period (sec)
        swp = re.search(r'Dominant Wave Period \(DPD\):</td><td class="data">([\d.]+) sec', text)
        # wind: Wind Direction and Speed
        wind = re.search(r'Wind Direction \(WDIR\):</td><td class="data">(\w+) \(.*\)</td>', text)
        speed = re.search(r'Wind Speed \(WSPD\):</td><td class="data">([\d.]+) kts', text)

        if wvht: data["wvht"] = wvht.group(1)
        if swp: data["swp"] = swp.group(1)
        if wind: data["wdir"] = wind.group(1)
        if speed: data["wspd"] = speed.group(1)
            
    except Exception as e:
        print(f"FETCH_ERROR: {e}")

    # ... [Keep your existing HTML generation code here] ...
