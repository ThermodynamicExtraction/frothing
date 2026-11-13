# config.py

# Buoys in the dropdown. The first one is what the page shows by default.
BUOYS = [
    {"id": "42098", "label": "LBK, FL",    "wind_station": "KVNC"},
    {"id": "45027", "label": "DULUTH, MN", "wind_station": "KDLH",
     "seasonal": True, "LONG_PERIOD_THRESHOLD": 6.0},
]

# Station 42098 - Egmont Channel Entrance
STATION_ID = "42098"

# The "Frothing" Thresholds
MIN_RIDEABLE_HEIGHT = 1.0   # ft
LONG_PERIOD_THRESHOLD = 8.0 # sec
WIND_CHOP_MAX_PERIOD = 4.0  # sec

# Personality Settings
STYLE = "salty_surfer_v3"
