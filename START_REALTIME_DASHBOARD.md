# 🚀 Start Real-Time IoT Dashboard

## Quick Start

### 1. Make sure backend is running:
```bash
cd Pharma123
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Start the IoT simulator (optional):
```bash
python simulator/send_data.py
```

### 3. Run the Real-Time Dashboard:
```bash
streamlit run realtime_iot_dashboard.py --server.port 5001
```

### 4. Access the dashboard:
Open your browser: **http://localhost:5001**

## Features

✅ **Live Temperature Graph** - Updates every 10 seconds  
✅ **Live Humidity Graph** - Real-time tracking  
✅ **Top Summary Metrics** - Latest readings and totals  
✅ **Active Alerts** - Color-coded by severity  
✅ **System Logs** - Activity tracking  
✅ **Auto-refresh** - No manual refresh needed  
✅ **Responsive Layout** - Clean and organized  

## What You'll See

### Summary Section
- Latest Temperature
- Latest Humidity  
- Total Records
- Current Location

### Live Graphs
- Temperature vs Time (with safe range lines)
- Humidity vs Time
- Multiple batches color-coded

### Alerts Panel
- 🔴 High severity alerts (temp < 0°C or > 10°C)
- 🟠 Medium severity alerts (temp 0-2°C or 8-10°C)
- ✅ "All normal" when no alerts

### System Logs
- New data fetched
- Offline data uploaded
- Alert detected
- System health status

### Data Table
- Last 20 IoT readings
- Timestamp, Batch ID, Temperature, Humidity, Location

## Troubleshooting

**Dashboard shows error?**
- Make sure backend is running on port 8000
- Check: http://localhost:8000/health

**No data showing?**
- Start the IoT simulator to generate data
- Or create batches in the main app

**Graphs not updating?**
- Dashboard auto-refreshes every 10 seconds
- Check browser console for errors

## Ports

- **Main App**: http://localhost:5000
- **Real-Time Dashboard**: http://localhost:5001
- **Backend API**: http://localhost:8000

Both dashboards can run simultaneously!
