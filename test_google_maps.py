"""
Test Google Maps API integration
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
BACKEND_URL = "http://localhost:8000"

print("=" * 70)
print("Testing Google Maps Integration")
print("=" * 70)

# Check if API key is set
if not GOOGLE_API_KEY or GOOGLE_API_KEY == "YOUR_GOOGLE_API_KEY_HERE":
    print("\n❌ Google API Key not configured!")
    print("\nTo fix this:")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Enable these APIs:")
    print("   - Geolocation API")
    print("   - Geocoding API")
    print("   - Directions API")
    print("   - Maps JavaScript API")
    print("3. Create an API key")
    print("4. Add to .env file:")
    print("   GOOGLE_API_KEY=your_actual_key_here")
    print("\n" + "=" * 70)
    exit()

print(f"\n✅ Google API Key found: {GOOGLE_API_KEY[:20]}...")

# Test 1: Backend health check
print("\n1. Testing backend health...")
try:
    response = requests.get(f"{BACKEND_URL}/health", timeout=5)
    if response.status_code == 200:
        health = response.json()
        print(f"✅ Backend: {health['status']}")
        print(f"✅ Google Maps: {health.get('google_maps', 'unknown')}")
    else:
        print(f"❌ Backend error: {response.status_code}")
except Exception as e:
    print(f"❌ Backend not reachable: {e}")
    print("Make sure backend is running: uvicorn backend.main:app --reload")

# Test 2: Geocoding API
print("\n2. Testing Geocoding API...")
try:
    response = requests.get(f"{BACKEND_URL}/geocode?address=Mumbai, India", timeout=10)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Geocoding works!")
        print(f"   Address: {result['formatted_address']}")
        print(f"   Coordinates: ({result['lat']}, {result['lng']})")
    else:
        print(f"❌ Geocoding failed: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Directions API
print("\n3. Testing Directions API...")
try:
    response = requests.get(f"{BACKEND_URL}/route?origin=Chennai&destination=Bengaluru", timeout=10)
    if response.status_code == 200:
        result = response.json()
        if result["status"] == "success" and result["route"].get("routes"):
            leg = result["route"]["routes"][0]["legs"][0]
            print(f"✅ Directions API works!")
            print(f"   Distance: {leg['distance']['text']}")
            print(f"   Duration: {leg['duration']['text']}")
        else:
            print(f"⚠️ No routes found")
    else:
        print(f"❌ Directions failed: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Send test IoT data with Auto-Detected location
print("\n4. Testing Auto-Detected location processing...")
try:
    test_data = {
        "batch_id": "TEST-BATCH-001",
        "temperature": 25.5,
        "humidity": 50.0,
        "location": "Auto-Detected",
        "sensor_id": "TEST-SENSOR",
        "timestamp": "2025-11-07T00:00:00Z"
    }
    
    response = requests.post(f"{BACKEND_URL}/iot/data", json=test_data, timeout=10)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ IoT data processed!")
        if result.get("data"):
            processed_location = result["data"].get("location", "Unknown")
            print(f"   Original: Auto-Detected")
            print(f"   Processed: {processed_location}")
            
            if processed_location != "Auto-Detected":
                print(f"   ✅ Location was auto-detected successfully!")
            else:
                print(f"   ⚠️ Location still shows 'Auto-Detected' - check API key")
    else:
        print(f"❌ Failed: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)
print("Summary:")
print("If all tests pass, Google Maps integration is working!")
print("If location still shows 'Auto-Detected', check:")
print("  1. Google API key is correct")
print("  2. All 4 APIs are enabled in Google Cloud Console")
print("  3. Backend has been restarted after adding API key")
print("=" * 70)
