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
        # Default values
        data = {"wvht": 0.0, "swp": 0.0, "apd": 0.0}
        
        # NOAA Mobile Parsing
        height = re.search(r'Seas: ([\d.]+) ft', raw_html)
        sw_period = re.search(r'Swell Period: ([\d.]+) sec', raw_html)
        avg_period = re.search(r'Period: ([\d.]+) sec', raw_html)

        if height: data["wvht"] = float(height.group(1))
        if sw_period: data["swp"] = float(sw_period.group(1))
        if avg_period: data["apd"] = float(avg_period.group(1))
        
        return data

    def analyze_surf(self, d):
        # The 'Frothing' Logic: Weighting Period over Height
        # A 1ft wave at 10s has more energy than a 3ft wave at 3s.
        
        height = d["wvht"]
        # Use Swell Period if available, otherwise fallback to Average Period
        period = d["swp"] if d["swp"] > 0 else d["apd"]
        
        # Calculate a 'Froth Index' (Simplified Energy Metric)
        # Power is proportional to Period^2 * Height, but let's keep it simple:
        froth_score = height * period

        if period >= 9.0 and height >= 0.5:
            return "💎 DIAMOND IN THE ROUGH: Long period groundswell detected. It looks small on paper, but the lines will be clean. GO NOW."
        elif froth_score > 12:
            return "🔥 FROTHING: Solid combo of size and energy. Get out there."
        elif froth_score > 5:
            return "🛹 CHOPPY/LOGGABLE: Not great, but surfable on a longboard or a twin fin."
        elif height < 1.0 or period < 4.0:
            return "🛹 SKATEBOARD DAY: It's a lake. Hit the pavement instead."
        else:
            return "🤷 MUSH: Wait for the tide to change or just stay home."

    def run(self):
        print(f"--- 🌊 Frothing Report: Station {self.station_id} ---")
        raw = self.fetch_data()
        metrics = self.parse_metrics(raw)
        
        print(f"Height: {metrics['wvht']}ft | Period: {max(metrics['swp'], metrics['apd'])}s")
        print("-" * 40)
        print(self.analyze_surf(metrics))

if __name__ == "__main__":
    FrothingAgent().run()
