import requests
import re
from datetime import datetime

class FrothingAgent:
    def __init__(self, station_id="42098"):
        self.url = f"https://www.ndbc.noaa.gov/mobile/station.php?station={station_id}"
        self.station_id = station_id

    def fetch_data(self):
        try:
            res = requests.get(self.url)
            res.raise_for_status()
            return res.text
        except: return ""

    def parse(self, html):
        # Extract metrics using regex
        h = re.search(r'Seas: ([\d.]+) ft', html)
        p = re.search(r'Period: ([\d.]+) sec', html)
        sp = re.search(r'Swell Period: ([\d.]+) sec', html)
        wd = re.search(r'Wind: (\w+) at', html)
        ws = re.search(r'at ([\d.]+) kts', html)
        
        return {
            "wvht": h.group(1) if h else "0.0",
            "apd": p.group(1) if p else "0.0",
            "swp": sp.group(1) if sp else "0.0",
            "wdir": wd.group(1) if wd else "N/A",
            "wspd": ws.group(1) if ws else "0.0",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def get_rec(self, d):
        h, p = float(d["wvht"]), float(d["swp"] if d["swp"] != "0.0" else d["apd"])
        offshore = any(x in d["wdir"] for x in ["E", "NE", "SE"])
        
        if h < 1.0 and p < 8.0: return "STATUS: SKATEBOARD_ONLY // LAKE_EFFECT"
        if offshore and p >= 7.0: return "STATUS: ABSOLUTE_FROTH // GO_NOW"
        if offshore: return "STATUS: CLEAN_BUT_SMALL // LOG_IT"
        if p >= 8.0: return "STATUS: SNEAKY_GROUNDSWELL // CHECK_BARS"
        return "STATUS: NOT_GREAT // SKIP_IT"

    def generate_html(self, d):
        recommendation = self.get_rec(d)
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>FROTHING // ST_{self.station_id}</title>
    <style>
        body {{ background-color: #F9F9F7; color: #000000; font-family: 'Space Mono', monospace; margin: 0; padding: 20px; display: flex; justify-content: center; }}
        .container {{ width: 100%; max-width: 500px; border: 1px solid #000000; padding: 20px; }}
        header {{ border-bottom: 1px solid #000000; margin-bottom: 20px; padding-bottom: 10px; font-weight: bold; }}
        .status-box {{ border: 1px solid #000000; padding: 15px; margin-bottom: 20px; background: #FFFFFF; font-weight: bold; }}
        .data-row {{ display: flex; justify-content: space-between; border-bottom: 1px solid #000000; padding: 8px 0; font-size: 0.9rem; }}
        .label {{ text-transform: uppercase; }}
        footer {{ margin-top: 20px; font-size: 0.7rem; text-transform: uppercase; }}
    </style>
</head>
<body>
    <div class="container">
        <header>FROTHING_SYSTEM_v1.0 // ST_{self.station_id}</header>
        <div class="status-box">{recommendation}</div>
        <div class="data-row"><span class="label">Height:</span><span>{d['wvht']} FT</span></div>
        <div class="data-row"><span class="label">Period:</span><span>{d['swp'] if d['swp'] != "0.0" else d['apd']} SEC</span></div>
        <div class="data-row"><span class="label">Wind:</span><span>{d['wdir']} @ {d['wspd']} KTS</span></div>
        <footer>UPDATED: {d['time']} // SOURCE: NOAA_NDBC</footer>
    </div>
</body>
</html>"""
        with open("index.html", "w") as f:
            f.write(html_content)

    def run(self):
        raw = self.fetch_data()
        data = self.parse(raw)
        self.generate_html(data)
        print("Inventory Updated: index.html generated.")

if __name__ == "__main__":
    FrothingAgent().run()
