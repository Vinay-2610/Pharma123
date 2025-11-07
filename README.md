# 🏥 PharmaChain - IoT + Blockchain + Google Maps Integrated Supply Chain System

A full-stack AI-powered **IoT, Blockchain, and Geolocation-based Pharmaceutical Supply Chain Monitoring System** with real-time temperature tracking, route visualization, offline data resilience, and FDA-compliant approval workflows.

---

## 🎯 Project Overview
PharmaChain ensures **end-to-end visibility and authenticity** of pharmaceutical products from manufacturing to delivery using:
- 🌡️ IoT sensors (ESP32 + DHT11) for real-time environmental tracking  
- 🌍 Google Maps APIs for live location, route mapping, and navigation tracking  
- 🔗 Blockchain-style ledger for immutable event records  
- 🧾 FDA workflow compliance with digital approvals and audit logs  
- ⚙️ SPIFFS-based offline data storage ensuring zero data loss  

---

## ✨ Key Features

### 1️⃣ 🔗 Blockchain Ledger
- Tamper-proof supply chain records using SHA-256 hash chaining  
- Ledger stored in Supabase (`ledger` table) for full transparency  
- Verification endpoints ensure data authenticity (`/verify`, `/ledger/verify/all`)  
- Public blockchain explorer to audit every transaction  

---

### 2️⃣ 🌡️ IoT Monitoring + SPIFFS Offline Support
- **ESP32 + DHT11 Sensor** records temperature and humidity every 5 minutes  
- Readings are POSTed to FastAPI backend (`/iot/data`)  
- If Wi-Fi disconnects:
  - Data is cached locally in **SPIFFS** (`/failed_data.json`)  
  - When Wi-Fi reconnects, ESP32 auto-uploads all unsent data:  
    ```
    ✅ SPIFFS mounted successfully  
    📤 Uploading stored offline data...  
    ✅ Uploaded offline record, code 200  
    🧹 Cleared offline data after upload.
    ```
- Guarantees **100% data persistence**, even in unstable networks  

---

### 3️⃣ 🗺️ Google Maps Integration (Real-Time Location)
- Uses the following Google APIs:
  - **Geolocation API** → Detects current coordinates of ESP32  
  - **Geocoding API** → Converts coordinates into readable addresses  
  - **Directions API** → Calculates optimized route between locations  
  - **Maps JavaScript API** → Displays interactive live route maps in dashboard  
- Automatically updates **location**, **latitude**, and **longitude** in Supabase  
- Every user dashboard (Manufacturer, Distributor, FDA, Pharmacy) displays:  
  - Real-time **temperature + location**  
  - Route visualization (“From” → “To”) updated every 5 minutes  
  - Delivery navigation panel under “Product Navigation” section  

---

### 4️⃣ 👥 Multi-Role Dashboards
| Role | Responsibilities |
|------|------------------|
| 🏭 **Manufacturer** | Creates batches, views temperature & route updates |
| 🧪 **FDA** | Approves/rejects batches, validates blockchain integrity |
| 🚚 **Distributor** | Updates shipment routes and monitors IoT conditions |
| 💊 **Pharmacy** | Verifies final product condition and authenticity |

Each dashboard auto-fetches:
- Latest temperature readings  
- Live GPS location and route updates  
- Alerts if temperature exceeds safe range (20°C–30°C)  

---

### 5️⃣ ✅ FDA Compliance Workflow
- Digital approval system with remarks & timestamps  
- Secure hash references for FDA signatures  
- Audit log maintained in `audit_logs` table  
- Automated ledger entries for all FDA actions  

---

### 6️⃣ ⚠️ Real-Time Alerts & Tamper Detection
- Temperature range monitored between **20°C–30°C**  
- Alerts generated for deviations (`is_alert = true`)  
- Severity classification:
  - High (below 15°C or above 35°C)  
  - Medium (16–34°C)  
- Alerts displayed in Streamlit UI and Supabase in real-time  
- Automatic blockchain integrity check for each record  

---

## 🏗️ System Architecture

                  ┌────────────────────────────────────────────┐
                  │           Streamlit Frontend               │
                  │────────────────────────────────────────────│
                  │  🏭 Manufacturer UI                        │
                  │  🚚 Distributor UI                         │
                  │  🧪 FDA UI                                 │
                  │  💊 Pharmacy UI                            │
                  │────────────────────────────────────────────│
                  │  - Real-time IoT Data Visualization        │
                  │  - Blockchain Ledger Explorer              │
                  │  - FDA Approval Workflows                  │
                  │  - Product Navigation (Google Maps)        │
                  └───────────────┬────────────────────────────┘
                                  │
                                  ▼
                  ┌────────────────────────────────────────────┐
                  │               FastAPI Backend              │
                  │────────────────────────────────────────────│
                  │  - IoT Data Receiver (/iot/data)           │
                  │  - Blockchain Hashing (SHA-256)            │
                  │  - FDA Workflow Logic                      │
                  │  - Google Maps API Integration             │
                  │  - SPIFFS Offline Data Handling            │
                  │  - REST + WebSocket Endpoints              │
                  └───────────────┬────────────────────────────┘
                                  │
                                  ▼
                  ┌────────────────────────────────────────────┐
                  │                Supabase DB                 │
                  │────────────────────────────────────────────│
                  │  Tables:                                   │
                  │   • iot_data → IoT Sensor Readings         │
                  │   • batches → Batch & Approval Info        │
                  │   • alerts → Temperature Alerts            │
                  │   • ledger → Blockchain Ledger Entries     │
                  │   • shipment_routes → Route Data (Maps)    │
                  │   • audit_logs → Action History            │
                  │   • user_profiles → Role-based Accounts    │
                  └───────────────┬────────────────────────────┘
                                  │
                                  ▼
                  ┌────────────────────────────────────────────┐
                  │           ESP32 + DHT11 Sensor             │
                  │────────────────────────────────────────────│
                  │  - Temperature & Humidity Sensing          │
                  │  - SPIFFS Offline Data Storage             │
                  │  - Auto Wi-Fi Reconnection Logic           │
                  │  - Google API Geolocation Detection        │
                  │  - Sends Data to FastAPI Every 5 Minutes   │
                  └────────────────────────────────────────────┘

yaml
Copy code

---

## 🛠️ Tech Stack

| Component | Technology |
|------------|-------------|
| **Backend** | FastAPI (Python 3.13) |
| **Frontend** | Streamlit |
| **Database** | Supabase (PostgreSQL) |
| **IoT Device** | ESP32 + DHT11 |
| **Offline Storage** | SPIFFS (ESP32 internal flash) |
| **Mapping APIs** | Google Maps: Directions, Geocoding, Geolocation, Maps JS |
| **Visualization** | Plotly, Pandas |
| **Blockchain** | SHA-256 Hash Chaining |

---

## ⚙️ Installation

### Prerequisites
- Python 3.13+  
- Supabase Account  
- Google Cloud API Key (enable Geocoding, Geolocation, Directions, Maps JavaScript APIs)  
- ESP32 Board + DHT11 Sensor  

### Steps

```bash
# Clone repository
git clone <your-repo-url>
cd PharmaChain

# Install dependencies
pip install -r requirements.txt
Configure Supabase
Create a Supabase project and run SQL scripts:

sql
Copy code
-- Example: Create IoT Data Table
CREATE TABLE iot_data (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id TEXT,
  temperature FLOAT,
  humidity FLOAT,
  location TEXT,
  latitude FLOAT,
  longitude FLOAT,
  sensor_id TEXT,
  timestamp TIMESTAMPTZ DEFAULT NOW()
);
Add Google Maps API Key
In your .env file:

ini
Copy code
GOOGLE_MAPS_API_KEY=your_api_key_here
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
🚀 Running the Application
Terminal 1: Backend

bash
Copy code
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
Terminal 2: Frontend

bash
Copy code
streamlit run app.py --server.port 5000
Terminal 3: IoT Device

Upload Arduino code to ESP32

Verify serial monitor shows:

yaml
Copy code
✅ Connected to WiFi!
🌡 Temperature: 26.40 °C | 💧 Humidity: 62.00 %
POSTing to: http://<your_ip>:8000/iot/data
✅ Data sent successfully!
📡 Data Flow
ESP32 reads temperature & humidity (every 5 mins)

Offline data stored in SPIFFS if Wi-Fi lost

On reconnect, all cached readings auto-uploaded

FastAPI validates data and logs to Supabase

Streamlit dashboard visualizes IoT data & live map route

FDA, Distributor, and Pharmacy dashboards show synced values

🗺️ Product Navigation Workflow
Manufacturer enters “From” and “To” addresses (auto or manual)

Distributor can update live route if shipment rerouted

FDA and Pharmacy dashboards show real-time navigation and temperature sync

Map auto-refreshes every 5 minutes with updated coordinates

📊 Database Tables
iot_data → Sensor readings

batches → Batch information & status

ledger → Blockchain event records

alerts → Temperature alerts

shipment_routes → Route info (from, to, distance, ETA)

audit_logs → User action logs

user_profiles → Account roles

🔒 Security & Reliability
SHA-256 Blockchain Hashing

Role-Based Access Control

FDA Signature Verification

SPIFFS Offline Data Backup

Real-Time Alerting

📈 Metrics
Blockchain Entries: 40+

IoT Readings: 1200+

Alerts Generated: 100+

Batches Tracked: 5+

Dashboards: 4 Roles

API Endpoints: 20+

🧑‍💻 Author
Vinay
IoT + Blockchain + AI Research Enthusiast
PharmaChain - November 2025, Version 1.0.0

📜 License
Licensed under the MIT License.

🙏 Acknowledgments
Supabase → Database + Authentication

FastAPI → High-performance backend

Streamlit → Interactive dashboarding

Google Cloud → Maps and Geolocation APIs

ESP32 → Reliable IoT edge device

