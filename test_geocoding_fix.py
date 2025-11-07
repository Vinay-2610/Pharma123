"""
Test script to verify Geocoding API is working
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

def get_coordinates():
    """Fetch approximate coordinates using Google Geolocation API"""
    if not GOOGLE_API_KEY:
        return None, None
    try:
        res = requests.post(
            f"https://www.googleapis.com/geolocation/v1/geolocate?key={GOOGLE_API_KEY}",
            timeout=5
        )
        data = res.json()
        if "location" in data:
            return data["location"]["lat"], data["location"]["lng"]
        return None, None
    except:
        return None, None

def get_place_name(lat, lng):
    """Convert coordinates into a readable address using Geocoding API"""
    if not GOOGLE_API_KEY:
        return f"Location ({lat:.4f}, {lng:.4f})"
    try:
        res = requests.get(
            f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={GOOGLE_API_KEY}",
            timeout=5
        )
        data = res.json()
        
        print(f"API Response Status: {data.get('status')}")
        
        # Check for API errors
        if data.get("status") == "REQUEST_DENIED":
            print(f"❌ Geocoding API Error: {data.get('error_message', 'API not enabled')}")
            return f"Location ({lat:.4f}, {lng:.4f}) - Enable Geocoding API"
        
        if data.get("results"):
            address = data["results"][0]["formatted_address"]
            print(f"✅ Geocoding API Success!")
            return address
        
        # Fallback with coordinates
        return f"Location ({lat:.4f}, {lng:.4f})"
    except Exception as e:
        print(f"❌ Geocoding error: {str(e)}")
        return f"Location ({lat:.4f}, {lng:.4f})"

print("=" * 70)
print("Testing Geocoding API Fix")
print("=" * 70)

print("\n1. Testing Geolocation API (get coordinates)...")
lat, lng = get_coordinates()
if lat and lng:
    print(f"✅ Got coordinates: ({lat:.4f}, {lng:.4f})")
else:
    print("❌ Failed to get coordinates")
    lat, lng = 9.5793, 77.6658  # Use fallback

print(f"\n2. Testing Geocoding API (convert to address)...")
address = get_place_name(lat, lng)
print(f"Result: {address}")

print("\n3. Testing complete location string...")
if "(" not in address:
    location = f"{address} ({lat:.4f}, {lng:.4f})"
else:
    location = address
print(f"Final Location: {location}")

print("\n" + "=" * 70)
if "Enable Geocoding API" in location:
    print("❌ GEOCODING API IS NOT ENABLED")
    print("   Please enable it in Google Cloud Console:")
    print("   https://console.cloud.google.com/apis/library/geocoding-backend.googleapis.com")
elif "Location (" in location and ")" in location and "," not in location.split("(")[0]:
    print("⚠️  GEOCODING API MIGHT NOT BE WORKING")
    print("   Check if it's enabled and restart the backend")
else:
    print("✅ GEOCODING API IS WORKING!")
    print("   Restart your backend to apply the fix")
print("=" * 70)
