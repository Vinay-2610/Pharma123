# Quick Fix: Enable Geocoding API

## The Problem
Your dashboard shows: **"Location (9.5793, 77.6658) - Enable Geocoding API"**

## The Solution (2 minutes)

### Step 1: Enable the API
1. Open: https://console.cloud.google.com/apis/library/geocoding-backend.googleapis.com
2. Click **"Enable"**
3. Wait 30 seconds for it to activate

### Step 2: Restart Services
```bash
# Stop all running services (Ctrl+C in each terminal)

# Terminal 1: Backend
cd Pharma123
uvicorn backend.main:app --reload

# Terminal 2: IoT Simulator  
cd Pharma123
python simulator/send_data.py

# Terminal 3: Dashboard
cd Pharma123
streamlit run app.py
```

### Step 3: Verify
Open your dashboard and you should see:
- ✅ "Bengaluru, Karnataka, India (12.9716, 77.5946)"
- ✅ "Chennai, Tamil Nadu, India (13.0827, 80.2707)"

Instead of:
- ❌ "Unknown Location"
- ❌ "Location (9.5793, 77.6658) - Enable Geocoding API"

## That's It!

The code is already fixed. You just need to enable the Geocoding API in Google Cloud Console.

## What Was Fixed in the Code

1. **IoT Simulator** now sends "Auto-Detected" instead of hardcoded locations
2. **Backend** automatically fetches real location using Google APIs
3. **Error messages** now tell you exactly what's wrong

All changes are already saved and ready to use!
