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
        footer {{ margin-top: 20px; font-size: 0.7rem; text-transform: uppercase; line-height: 1.4; }}
        .warning {{ margin-top: 15px; border-top: 1px dashed #000000; padding-top: 10px; font-size: 0.6rem; opacity: 0.7; }}
    </style>
</head>
<body>
    <div class="container">
        <header>FROTHING_SYSTEM_v1.0 // ST_{self.station_id}</header>
        <div class="status-box">{recommendation}</div>
        <div class="data-row"><span class="label">Height:</span><span>{d['wvht']} FT</span></div>
        <div class="data-row"><span class="label">Period:</span><span>{d['swp'] if d['swp'] != "0.0" else d['apd']} SEC</span></div>
        <div class="data-row"><span class="label">Wind:</span><span>{d['wdir']} @ {d['wspd']} KTS</span></div>
        
        <footer>
            UPDATED: {d['time']} // SOURCE: NOAA_NDBC
            <div class="warning">
                CRITICAL: SURFING IS DANGEROUS. DATA IS INTERPRETIVE ONLY. 
                USER ASSUMES ALL RISK. VISUAL BEACH CHECK REQUIRED.
            </div>
        </footer>
    </div>
</body>
</html>"""
        with open("index.html", "w") as f:
            f.write(html_content)
