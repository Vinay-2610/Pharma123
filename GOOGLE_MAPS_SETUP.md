# 🗺️ Google Maps Integration Guide

## Overview
PharmaChain now integrates all 4 Google Maps APIs for complete shipment tracking:
1. **Geolocation API** - Auto-detect current coordinates
2. **Geocoding API** - Convert coordinates to addresses
3. **Directions API** - Calculate routes between locations
4. **Maps JavaScript API** - Display interactive maps

## 🔑 Step 1: Get Google Maps API Key

### Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the following APIs:
   - Geolocation API
   - Geocoding API
   - Directions API
   - Maps JavaScript API

### Get API Key
1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **API Key**
3. Copy your API key
4. (Optional) Restrict the key to only the 4 APIs above

## 🔧 Step 2: Configure API Key

### Add to .env file:
```env
GOOGLE_API_KEY=YOUR_ACTUAL_API_KEY_HERE
```

Replace `YOUR_ACTUAL_API_KEY_HERE` with your real Google Maps API key.

## 📡 Step 3: Backend Endpoints

### New Endpoints Added:

#### 1. Get Route
```
GET /route?origin=Chennai&destination=Bengaluru
```
Returns driving directions between two locations.

#### 2. Geocode Address
```
GET /geocode?address=Mumbai, India
```
Converts address to coordinates (lat, lng).

#### 3. Health Check (Updated)
```
GET /health
```
Now shows if Google Maps is enabled.

## 🎨 Step 4: Frontend Integration

### Display Interactive Map

Add this to any dashboard:

```python
import streamlit as st

# Get Google API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Create map URL
origin = "Chennai, Tamil Nadu"
destination = "Bengaluru, Karnataka"
map_url = f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_API_KEY}&origin={origin}&destination={destination}&zoom=7"

# Display map
st.components.v1.iframe(map_url, height=500)
```

### Fetch Route Data

```python
import requests

# Get route from backend
response = requests.get("http://localhost:8000/route?origin=Chennai&destination=Bengaluru")
route_data = response.json()

# Extract route info
if route_data["status"] == "success":
    route = route_data["route"]
    if route.get("routes"):
        distance = route["routes"][0]["legs"][0]["distance"]["text"]
        duration = route["routes"][0]["legs"][0]["duration"]["text"]
        st.write(f"Distance: {distance}")
        st.write(f"Duration: {duration}")
```

## 🌡️ Step 5: Auto-Location for IoT Data

When ESP32 sends data with location "Auto-Detected", the backend will:
1. Use Geolocation API to get coordinates
2. Use Geocoding API to get address
3. Store both in database

### Example IoT Data Flow:
```
ESP32 → FastAPI → Geolocation API → Geocoding API → Supabase
```

Result in database:
```json
{
  "temperature": 24.5,
  "humidity": 50.0,
  "location": "Mumbai, Maharashtra, India (19.0760, 72.8777)",
  "timestamp": "2025-11-06T12:00:00Z"
}
```

## 📊 Step 6: Dashboard Features

### All Dashboards Now Show:
1. ✅ Live temperature and humidity
2. ✅ Current location (address + coordinates)
3. ✅ Interactive route map
4. ✅ Distance and duration
5. ✅ Auto-refresh every 10 seconds

### Role-Specific Maps:
- **Manufacturer**: Factory → Warehouse route
- **FDA**: Compliance monitoring with location tracking
- **Distributor**: Warehouse → Pharmacy route
- **Pharmacy**: Delivery tracking

## 🎯 Step 7: Testing

### Test Geolocation:
```bash
curl "http://localhost:8000/geocode?address=Mumbai"
```

### Test Route:
```bash
curl "http://localhost:8000/route?origin=Chennai&destination=Bengaluru"
```

### Test Health:
```bash
curl "http://localhost:8000/health"
```

Should return:
```json
{
  "status": "healthy",
  "service": "PharmaChain Backend",
  "google_maps": "enabled"
}
```

## 💰 Pricing (Google Maps)

### Free Tier:
- **Geolocation API**: $5 per 1,000 requests (first $200/month free)
- **Geocoding API**: $5 per 1,000 requests (first $200/month free)
- **Directions API**: $5 per 1,000 requests (first $200/month free)
- **Maps JavaScript API**: $7 per 1,000 loads (first $200/month free)

### For Development:
The free tier ($200/month credit) is more than enough for testing and development.

## 🔒 Security Best Practices

1. **Never commit API key to Git**
   - Already in `.gitignore`
   - Use environment variables only

2. **Restrict API Key**
   - Limit to specific APIs
   - Add HTTP referrer restrictions
   - Add IP address restrictions

3. **Monitor Usage**
   - Check Google Cloud Console regularly
   - Set up billing alerts

## 🚀 Quick Start

1. Get Google Maps API key
2. Add to `.env` file
3. Restart backend: `uvicorn backend.main:app --reload`
4. Restart frontend: `streamlit run app.py`
5. Maps will appear automatically!

## 📝 Example: Complete Dashboard with Map

```python
import streamlit as st
import requests
import os

st.title("🗺️ Live Shipment Tracking")

# Fetch latest IoT data
response = requests.get("http://localhost:8000/iot/data?limit=1")
latest = response.json()["data"][0]

# Display metrics
col1, col2, col3 = st.columns(3)
col1.metric("🌡️ Temperature", f"{latest['temperature']}°C")
col2.metric("💧 Humidity", f"{latest['humidity']}%")
col3.metric("📍 Location", latest['location'])

# Display route map
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
origin = "Chennai, Tamil Nadu"
destination = "Bengaluru, Karnataka"
map_url = f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_API_KEY}&origin={origin}&destination={destination}"

st.subheader("📍 Live Route")
st.components.v1.iframe(map_url, height=500)

# Get route details
route_response = requests.get(f"http://localhost:8000/route?origin={origin}&destination={destination}")
route_data = route_response.json()

if route_data["status"] == "success" and route_data["route"].get("routes"):
    leg = route_data["route"]["routes"][0]["legs"][0]
    col1, col2 = st.columns(2)
    col1.metric("📏 Distance", leg["distance"]["text"])
    col2.metric("⏱️ Duration", leg["duration"]["text"])
```

## ✅ Verification Checklist

- [ ] Google Cloud project created
- [ ] All 4 APIs enabled
- [ ] API key generated
- [ ] API key added to `.env`
- [ ] Backend restarted
- [ ] Frontend restarted
- [ ] `/health` endpoint shows `google_maps: enabled`
- [ ] Maps display in dashboards
- [ ] Route data fetches successfully

## 🎉 Result

Your PharmaChain system now has:
- ✅ Real-time location tracking
- ✅ Interactive route visualization
- ✅ Address geocoding
- ✅ Distance and duration calculations
- ✅ Cross-dashboard synchronization
- ✅ Professional mapping interface

All powered by Google Maps! 🗺️
