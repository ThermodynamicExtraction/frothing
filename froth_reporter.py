import requests
import re

class FrothingAgent:
    def __init__(self, station_id="42098"):
        self.url = f"https://www.ndbc.noaa.gov/mobile/station.php?station={station_id}"
        self.station_id = station_id

    def fetch_data(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            return f"Error: {e}"

    def parse_metrics(self, raw_html):
        data = {"wvht": 0.0, "swp": 0.0, "apd": 0.0, "wdir": "N/A", "wspd": 0.0}
        
        # Regex for Wind and Waves
        height = re.search(r'Seas: ([\d.]+) ft', raw_html)
        sw_period = re.search(r'Swell Period: ([\d.]+) sec', raw_html)
        avg_period = re.search(r'Period: ([\d.]+) sec', raw_html)
        wind_dir = re.search(r'Wind: (\w+) at', raw_html)
        wind_speed = re.search(r'at ([\d.]+) kts', raw_html)

        if height: data["wvht"] = float(height.group(1))
        if sw_period: data["swp"] = float(sw_period.group(1))
        if avg_period: data["apd"] = float(avg_period.group(1))
        if wind_dir: data["wdir"] = wind_dir.group(1)
        if wind_speed: data["wspd"] = float(wind_speed.group(1))
        
        return data

    def analyze_surf(self, d):
        height = d["wvht"]
        period = d["swp"] if d["swp"] > 0 else d["apd"]
        wdir = d["wdir"]
        wspd = d["wspd"]

        # 🌬️ WIND LOGIC (Specific to Egmont/FL West Coast)
        # Offshore (E, NE, SE) = Clean/Groomed
        # Onshore (W, NW, SW) = Choppy/Blown out
        is_offshore = any(dir in wdir for dir in ["E", "NE", "SE"])
        is_howling = wspd > 15

        status = ""
        
        if height < 1.0:
            status = "🛹 SKATEBOARD WEATHER. It's a lake. Hit the concrete."
        elif is_offshore and period >= 6.0:
            status = "💎 TOTAL FROTH: Clean groundswell with offshore winds. Go now!"
        elif is_offshore and period < 6.0:
            status = "🌊 CLEAN BUT SMALL: The wind is grooming it, but there's not much size."
        elif not is_offshore and is_howling:
            status = "🌪️ BLOWN OUT: Too much onshore wind. It's just a washing machine out there."
        else:
            status = "🤔 SEMI-CLEAN: It's rideable, but don't quit your day job."

        return f"{status}\n[Wind: {wdir} @ {wspd} kts]"

    def run(self):
        print(f"--- 🌊 Frothing Report: Station {self.station_id} ---")
        raw = self.fetch_data()
        metrics = self.parse_metrics(raw)
        print(f"Height: {metrics['wvht']}ft | Period: {max(metrics['swp'], metrics['apd'])}s")
        print("-" * 40)
        print(self.analyze_surf(metrics))

if __name__ == "__main__":
    FrothingAgent().run()
