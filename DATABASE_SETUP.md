# Supabase Database Setup Guide

This guide will help you set up the required database tables in Supabase for PharmaChain.

## Step 1: Create Supabase Account

1. Go to [https://supabase.com](https://supabase.com)
2. Click "Start your project"
3. Sign up with GitHub, Google, or email
4. Create a new organization (free tier is sufficient)

## Step 2: Create a New Project

1. Click "New Project"
2. Enter project details:
   - **Name**: PharmaChain (or any name you prefer)
   - **Database Password**: Create a strong password (save this!)
   - **Region**: Choose closest to your location
   - **Pricing Plan**: Free tier is fine for testing
3. Click "Create new project"
4. Wait 2-3 minutes for project setup to complete

## Step 3: Get Your API Credentials

1. Go to **Project Settings** (gear icon in sidebar)
2. Click on **API** in the left menu
3. Copy these values (you'll need them for `.env` file):
   - **Project URL**: This is your `SUPABASE_URL`
   - **anon/public key**: This is your `SUPABASE_KEY`

## Step 4: Create Database Tables

1. In your Supabase dashboard, click **SQL Editor** in the left sidebar
2. Click **New query**
3. Copy and paste the following SQL code:

```sql
-- =====================================================
-- PharmaChain Database Schema
-- =====================================================

-- Table 1: IoT Sensor Data
-- Stores all temperature and humidity readings from sensors
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

-- Table 2: Alerts
-- Stores alerts generated when temperature is out of safe range
CREATE TABLE alerts (
    id BIGSERIAL PRIMARY KEY,
    batch_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high')),
    message TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    temperature DECIMAL(5,2),
    location TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table 3: User Profiles
-- Stores user roles with Row Level Security for secure role-based access control
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('Manufacturer', 'FDA', 'Distributor', 'Pharmacy')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security on user_profiles
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Users can only read their own profile (cannot update or delete)
CREATE POLICY "Users can view own profile"
    ON user_profiles
    FOR SELECT
    USING (auth.uid() = id);

-- Only authenticated users can insert their own profile (once during signup)
CREATE POLICY "Users can insert own profile"
    ON user_profiles
    FOR INSERT
    WITH CHECK (auth.uid() = id);

-- Function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at on user_profiles
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Indexes for Better Performance
-- =====================================================

-- Index on batch_id for faster batch lookups
CREATE INDEX idx_iot_batch_id ON iot_data(batch_id);

-- Index on timestamp for faster time-based queries
CREATE INDEX idx_iot_timestamp ON iot_data(timestamp DESC);

-- Index for alert queries
CREATE INDEX idx_iot_is_alert ON iot_data(is_alert) WHERE is_alert = TRUE;

-- Index on alerts batch_id
CREATE INDEX idx_alerts_batch_id ON alerts(batch_id);

-- Index on alerts timestamp
CREATE INDEX idx_alerts_timestamp ON alerts(timestamp DESC);

-- Index on alerts severity
CREATE INDEX idx_alerts_severity ON alerts(severity);

-- =====================================================
-- Comments for Documentation
-- =====================================================

COMMENT ON TABLE iot_data IS 'Stores IoT sensor readings for pharmaceutical batches';
COMMENT ON TABLE alerts IS 'Stores temperature violation alerts';

COMMENT ON COLUMN iot_data.batch_id IS 'Unique identifier for pharmaceutical batch';
COMMENT ON COLUMN iot_data.temperature IS 'Temperature in Celsius';
COMMENT ON COLUMN iot_data.humidity IS 'Relative humidity percentage';
COMMENT ON COLUMN iot_data.blockchain_hash IS 'SHA-256 hash for data integrity verification';
COMMENT ON COLUMN iot_data.is_alert IS 'Whether this reading triggered an alert';

COMMENT ON COLUMN alerts.severity IS 'Alert severity: low, medium, or high';
COMMENT ON COLUMN alerts.resolved IS 'Whether the alert has been addressed';
```

4. Click **Run** (or press Ctrl/Cmd + Enter)
5. You should see "Success. No rows returned"

## Step 5: Verify Tables Were Created

1. In the left sidebar, click **Table Editor**
2. You should see two tables:
   - `iot_data`
   - `alerts`
3. Click each table to verify the columns exist

## Step 6: Configure Authentication

1. In the left sidebar, click **Authentication**
2. Click **Providers**
3. Ensure **Email** is enabled
4. Click **Email** to configure:
   - **Enable Email provider**: ON
   - **Confirm email**: OFF (for easier testing)
   - **Secure email change**: ON (recommended)
5. Click **Save**

## Step 7: Set Up Environment Variables

1. In your Replit project, go to **Secrets** (lock icon in left sidebar)
2. Add two secrets:
   - Key: `SUPABASE_URL`, Value: Your Project URL from Step 3
   - Key: `SUPABASE_KEY`, Value: Your anon/public key from Step 3

Alternatively, create a `.env` file:

```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
```

## Step 8: Test the Connection

Run this Python script to test your connection:

```python
from supabase import create_client
import os

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

# Test query
result = supabase.table("iot_data").select("*").limit(1).execute()
print("Connection successful!")
print(f"Current records: {len(result.data)}")
```

## Database Schema Reference

### iot_data Table

| Column | Type | Description |
|--------|------|-------------|
| id | BIGSERIAL | Auto-incrementing primary key |
| batch_id | TEXT | Pharmaceutical batch identifier |
| temperature | DECIMAL(5,2) | Temperature in °C |
| humidity | DECIMAL(5,2) | Humidity percentage |
| location | TEXT | Current location of batch |
| sensor_id | TEXT | IoT sensor identifier |
| timestamp | TIMESTAMPTZ | When reading was taken |
| blockchain_hash | TEXT | SHA-256 hash for verification |
| is_alert | BOOLEAN | Whether reading triggered alert |
| created_at | TIMESTAMPTZ | When record was created |

### alerts Table

| Column | Type | Description |
|--------|------|-------------|
| id | BIGSERIAL | Auto-incrementing primary key |
| batch_id | TEXT | Related batch identifier |
| alert_type | TEXT | Type of alert |
| severity | TEXT | low/medium/high |
| message | TEXT | Alert description |
| timestamp | TIMESTAMPTZ | When alert was triggered |
| temperature | DECIMAL(5,2) | Temperature that caused alert |
| location | TEXT | Where alert occurred |
| resolved | BOOLEAN | Alert resolution status |
| created_at | TIMESTAMPTZ | When alert was created |

## Troubleshooting

**Error: "relation 'iot_data' does not exist"**
- Tables weren't created properly
- Re-run the SQL script in SQL Editor
- Check for any error messages

**Error: "Invalid API key"**
- Wrong SUPABASE_KEY in .env file
- Use the "anon/public" key, not the "service_role" key
- Verify key is copied correctly without extra spaces

**Error: "Failed to fetch"**
- Wrong SUPABASE_URL in .env file
- Check project URL in Supabase dashboard
- Ensure project is not paused (free tier limitation)

**Authentication not working**
- Disable email confirmation in Auth settings
- Check email provider is enabled
- Verify network connection

## Next Steps

Once your database is set up:
1. Start the FastAPI backend
2. Run the IoT simulator to generate test data
3. Open the Streamlit dashboard
4. Create a user account and log in
5. View real-time data in your role-specific dashboard

## Security Best Practices

- Never share your `service_role` key publicly
- Use Row Level Security (RLS) for production
- Enable email confirmation for production deployments
- Regularly rotate API keys
- Monitor usage in Supabase dashboard

## Support

For Supabase-specific issues, visit:
- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Discord](https://discord.supabase.com)
- [Supabase GitHub](https://github.com/supabase/supabase)
