# PharmaChain Quick Start Guide

Your PharmaChain system is almost ready! Follow these simple steps to complete the setup.

## Current Status ✅

- ✅ Backend API running on port 8000
- ✅ Streamlit dashboard running on port 5000  
- ✅ Supabase credentials configured
- ⏳ Database tables need to be created

## Step 1: Create Database Tables (Required)

You need to create two simple tables in your Supabase database. This takes about 2 minutes.

### Instructions:

1. **Open Supabase Dashboard**
   - Go to https://supabase.com
   - Log in to your account
   - Select your PharmaChain project

2. **Open SQL Editor**
   - Click **SQL Editor** in the left sidebar
   - Click **New query**

3. **Run This SQL Code**
   - Copy and paste the code below
   - Click **Run** (or press Ctrl/Cmd + Enter)

```sql
-- Create IoT Data Table
CREATE TABLE iot_data (
    id BIGSERIAL PRIMARY KEY,
    batch_id TEXT NOT NULL,
    temperature DECIMAL(5,2) NOT NULL,
    humidity DECIMAL(5,2) NOT NULL,
    location TEXT NOT NULL,
    sensor_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    blockchain_hash TEXT NOT NULL,
    is_alert BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create Alerts Table
CREATE TABLE alerts (
    id BIGSERIAL PRIMARY KEY,
    batch_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    temperature DECIMAL(5,2),
    location TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create User Profiles Table (for secure role-based access control)
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('Manufacturer', 'FDA', 'Distributor', 'Pharmacy')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security on user_profiles
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Users can only read their own profile
CREATE POLICY "Users can view own profile"
    ON user_profiles FOR SELECT
    USING (auth.uid() = id);

-- Users can insert their own profile during signup
CREATE POLICY "Users can insert own profile"
    ON user_profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

-- Create Indexes for Better Performance
CREATE INDEX idx_iot_batch_id ON iot_data(batch_id);
CREATE INDEX idx_iot_timestamp ON iot_data(timestamp DESC);
CREATE INDEX idx_alerts_batch_id ON alerts(batch_id);
CREATE INDEX idx_alerts_timestamp ON alerts(timestamp DESC);
```

4. **Verify Tables Were Created**
   - Click **Table Editor** in the left sidebar
   - You should see `iot_data` and `alerts` tables

## Step 2: Configure Authentication (Optional but Recommended)

1. In Supabase, click **Authentication** → **Providers**
2. Make sure **Email** is enabled
3. For testing, you can disable **Confirm email** to make signup easier
4. Click **Save**

## Step 3: Start Using PharmaChain

Once the database tables are created:

### A. Open the Dashboard
- Your Streamlit dashboard is already running
- Click the webview to open it

### B. Create Your Account
1. Click the **Sign Up** tab
2. Enter your email and password (minimum 6 characters)
3. Select your role: Manufacturer, FDA, Distributor, or Pharmacy
4. Click **Create Account**

### C. Log In
1. Use your credentials to log in
2. Select the same role you registered with
3. You'll see your role-specific dashboard

### D. Generate Test Data
To populate the system with IoT sensor data, run the simulator:

**In a new Shell tab:**
```bash
python simulator/send_data.py
```

The simulator will:
- Send temperature and humidity readings every 3-7 seconds
- Monitor 4 pharmaceutical batches
- Generate alerts when temperature is outside 2-8°C range
- Run continuously until you stop it (Ctrl+C)

## What You'll See

### Manufacturer Dashboard
- Real-time temperature and humidity charts
- All IoT data in tables
- Batch monitoring across locations

### FDA Dashboard  
- Active temperature alerts
- Blockchain verification tool
- Compliance monitoring

### Distributor Dashboard
- Active shipments tracking
- Batch location monitoring
- Temperature history for each shipment

### Pharmacy Dashboard
- Batch quality verification
- Compliance rate checking
- Batch journey visualization

## Testing the Blockchain Verification

1. Log in as FDA role
2. Go to "Blockchain Verification" tab
3. Enter any Record ID (starts from 1)
4. Click "Verify Blockchain Hash"
5. See the SHA-256 verification result

## Troubleshooting

**"Error fetching data"**
- Database tables not created → Follow Step 1
- Backend not running → It should be running automatically

**"Login failed"**
- Email confirmation might be enabled → Disable it in Supabase Auth settings
- Wrong credentials → Try signing up again

**"No IoT data available"**
- Run the simulator: `python simulator/send_data.py`
- Wait a few seconds for data to appear
- Refresh the dashboard

## Safe Temperature Range

Pharmaceutical products must stay between **2°C and 8°C**:
- ✅ Normal: 2-8°C
- ⚠️ Medium Alert: 0-2°C or 8-10°C  
- 🔴 High Alert: <0°C or >10°C

## Need Help?

Check these files for more details:
- `README.md` - Complete documentation
- `DATABASE_SETUP.md` - Detailed database setup guide
- `.env.example` - Environment variable template

## System Architecture

```
IoT Simulator → FastAPI Backend → Supabase Database
                      ↓
              Streamlit Dashboard
                (Role-Based Views)
```

Enjoy your PharmaChain system! 🚀💊
