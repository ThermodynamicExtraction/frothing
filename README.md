# 🌊 Frothing
**The No-Nonsense AI Surf Reporter**

Frothing is an AI-powered agent designed to rescue surfers from the "data fatigue" of staring at raw NOAA buoy outputs. Instead of 0.7ft @ 2.6s, Frothing tells you to "Stay in bed and go skateboarding."

## 🚀 The Vision
Frothing wraps raw oceanographic data into a human-readable, salty, and honest recommendation. 
- **Current Focus:** Station 42098 - Egmont Channel Entrance, FL.
- **Tech Stack:** Python, Requests (Scraping), and Heuristic Analysis (Moving to LLM soon).

## 📊 How it works
Frothing analyzes the relationship between:
- **WVHT (Significant Wave Height):** The raw size.
- **APD (Average Period):** The energy. Anything under 4s is usually wind-slop.
- **SwD (Swell Direction):** For Florida's West Coast, direction is everything.

## Logic Engine
Groundswell detection: (Period > 8s)
Wind: (Detection of E/NE/SE offshore winds)
The 'Skateboard' Fallback: (Automatic alert when the Gulf is flat)
