import requests
import random
import time
from datetime import datetime

BACKEND_URL = "http://localhost:8000"

BATCH_IDS = ["BATCH-2025-001", "BATCH-2025-002", "BATCH-2025-003", "BATCH-2025-004"]
SENSOR_IDS = ["SENSOR-001", "SENSOR-002", "SENSOR-003", "SENSOR-004", "SENSOR-005"]

def generate_sensor_reading():
    normal_temp_range = (4.0, 6.0)
    
    if random.random() < 0.15:
        temperature = round(random.uniform(-2.0, 12.0), 2)
    else:
        temperature = round(random.uniform(*normal_temp_range), 2)
    
    humidity = round(random.uniform(30.0, 70.0), 2)
    
    data = {
        "batch_id": random.choice(BATCH_IDS),
        "temperature": temperature,
        "humidity": humidity,
        "location": "Auto-Detected",  # Backend will fetch real location using Google Geolocation API
        "sensor_id": random.choice(SENSOR_IDS),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return data

def send_iot_data():
    try:
        data = generate_sensor_reading()
        
        response = requests.post(f"{BACKEND_URL}/iot/data", json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            alert_status = "⚠️ ALERT" if result.get("alert_generated") else "✓ Normal"
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {alert_status} | Batch: {data['batch_id']} | Temp: {data['temperature']}°C | Humidity: {data['humidity']}% | Location: {data['location']}")
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
    
    except requests.exceptions.RequestException as e:
        print(f"Connection Error: {e}")
        return False
    except Exception as e:
        print(f"Error sending data: {e}")
        return False

def main():
    print("=" * 80)
    print("PharmaChain IoT Data Simulator Started")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Monitoring Batches: {', '.join(BATCH_IDS)}")
    print(f"Safe Temperature Range: 2°C - 8°C")
    print("=" * 80)
    print()
    
    iteration = 0
    while True:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---")
        send_iot_data()
        
        interval = random.uniform(3, 7)
        print(f"Next reading in {interval:.1f} seconds...")
        time.sleep(interval)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSimulator stopped by user.")
