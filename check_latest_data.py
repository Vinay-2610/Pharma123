"""
Check the latest data in Supabase to see ESP32 readings
"""
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 70)
print("Latest 10 IoT Data Records from Supabase")
print("=" * 70)

try:
    result = supabase.table("iot_data").select("*").order("timestamp", desc=True).limit(10).execute()
    
    if result.data:
        print(f"\nFound {len(result.data)} records\n")
        for idx, record in enumerate(result.data, 1):
            print(f"{idx}. ID: {record['id']}")
            print(f"   Batch: {record['batch_id']}")
            print(f"   Sensor: {record['sensor_id']}")
            print(f"   Temperature: {record['temperature']}°C")
            print(f"   Humidity: {record['humidity']}%")
            print(f"   Location: {record['location']}")
            print(f"   Timestamp: {record['timestamp']}")
            print(f"   Alert: {record.get('is_alert', False)}")
            print("-" * 70)
    else:
        print("No data found")
        
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 70)
print("Looking for ESP32 data specifically...")
print("=" * 70)

try:
    esp_result = supabase.table("iot_data").select("*").eq("sensor_id", "ESP32_SENSOR_01").order("timestamp", desc=True).limit(5).execute()
    
    if esp_result.data:
        print(f"\nFound {len(esp_result.data)} ESP32 records\n")
        for idx, record in enumerate(esp_result.data, 1):
            print(f"{idx}. Temperature: {record['temperature']}°C | Humidity: {record['humidity']}% | Time: {record['timestamp']}")
    else:
        print("No ESP32 data found")
        
except Exception as e:
    print(f"Error: {e}")
