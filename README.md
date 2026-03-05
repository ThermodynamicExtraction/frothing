# Frothing
**The No-Nonsense AI Surf Reporter**

Frothing is an AI-powered agent designed to rescue surfers from the "data fatigue" of staring at raw NOAA buoy outputs. Instead of 0.7ft @ 2.6s, Frothing tells you to "Stay in bed and go skateboarding."

## The Vision
Frothing wraps raw oceanographic data into a human-readable, salty, and honest recommendation. 
- **Current Focus:** Station 42098 - Egmont Channel Entrance, FL.
- **Tech Stack:** Python, Requests (Scraping), and Heuristic Analysis (Moving to LLM soon).

## How it works
Frothing analyzes the relationship between:
- **WVHT (Significant Wave Height):** The raw size.
- **APD (Average Period):** The energy. Anything under 4s is usually wind-slop.
- **SwD (Swell Direction):** For Florida's West Coast, direction is everything.

## Logic Engine
Groundswell detection: (Period > 8s)
Wind: (Detection of E/NE/SE offshore winds)
The 'Skateboard' Fallback: (Automatic alert when the Gulf is flat)

---

## LEGAL_DISCLAIMER

**NOTICE:** Surfing and all ocean-related activities are inherently dangerous. The information provided by the **Frothing** system is a purely mathematical interpretation of raw NOAA buoy data (Station 42098). 

1. **Interpretive Data:** "Frothing" status reports are for informational purposes only. They do not account for local hazards, tides, currents, water quality (red tide/bacteria), or shifting sandbars.
2. **User Responsibility:** The user is solely responsible for their own safety. Always perform a visual "beach check" before entering the water. 
3. **No Liability:** The creators and contributors of this project are not liable for any injury, loss, or gear damage resulting from the use of this data or the decision to enter the ocean.


**KNOW YOUR LIMITS. WHEN IN DOUBT, DON'T GO OUT.**
