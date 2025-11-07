# Fix "Unknown Location" Issue

## Problem
The IoT dashboard shows "Unknown Location" or coordinates instead of readable addresses.

## Root Cause
The **Geocoding API** is not enabled in your Google Cloud Console. While the Geolocation API is working (getting coordinates), the Geocoding API (converting coordinates to addresses) needs to be enabled separately.

## Solution

### Step 1: Enable Geocoding API in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create one if you haven't)
3. Navigate to **APIs & Services** → **Library**
4. Search for **"Geocoding API"**
5. Click on it and press **"Enable"**

### Step 2: Verify All Required APIs are Enabled

Make sure these 4 APIs are enabled:
- ✅ **Geolocation API** (for getting coordinates)
- ⚠️ **Geocoding API** (for converting coordinates to addresses) - **THIS IS THE MISSING ONE**
- ✅ **Directions API** (for route planning)
- ✅ **Maps JavaScript API** (for map visualization)

### Step 3: Restart the Backend

After enabling the Geocoding API:

```bash
# Stop the backend (Ctrl+C in the terminal running it)
# Then restart it:
cd Pharma123
uvicorn backend.main:app --reload
```

### Step 4: Restart the IoT Simulator

```bash
# Stop the simulator (Ctrl+C)
# Then restart it:
cd Pharma123
python simulator/send_data.py
```

### Step 5: Verify the Fix

Run the test script to verify:

```bash
python Pharma123/test_google_maps.py
```

You should see:
- ✅ Geocoding API works!
- ✅ Location shows readable address instead of "Unknown Location"

## What Changed

### IoT Simulator (`simulator/send_data.py`)
- Now sends `"Auto-Detected"` as location
- Backend automatically fetches real location using Google APIs

### Backend (`backend/main.py`)
- Improved error handling for Geocoding API failures
- Shows helpful error messages when API is not enabled
- Falls back to coordinates when address lookup fails

## Current Status

Your Google API Key is configured: `AIzaSyCd4Y7cQse-JJjA...`

**Next Step:** Enable the Geocoding API in Google Cloud Console (see Step 1 above)

## Testing

After enabling the API, you should see locations like:
- "Bengaluru, Karnataka, India (12.9716, 77.5946)"
- "Chennai, Tamil Nadu, India (13.0827, 80.2707)"

Instead of:
- "Unknown Location"
- "Location (9.5793, 77.6658)"

## Need Help?

If you still see "Unknown Location" after enabling the API:
1. Check that the API key has no restrictions blocking the Geocoding API
2. Wait 1-2 minutes for the API enablement to propagate
3. Restart both backend and simulator
4. Check the backend logs for error messages
