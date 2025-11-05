# PharmaChain - AI-Powered IoT + Blockchain Pharmaceutical Supply Chain System

A full-stack pharmaceutical supply chain monitoring system using IoT sensors, blockchain verification, and role-based dashboards.

## Features

- **Real-time IoT Monitoring**: Track temperature and humidity of medicine batches
- **Blockchain Verification**: SHA-256 hash-based tamper-proof data integrity
- **Role-Based Dashboards**: Customized views for Manufacturer, FDA, Distributor, and Pharmacy
- **Automated Alerts**: Instant notifications for out-of-range conditions
- **Supabase Integration**: Secure authentication and data storage
- **Interactive Visualizations**: Plotly charts for data analysis

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Streamlit
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth
- **Blockchain**: SHA-256 hashing simulation
- **Visualization**: Plotly, Pandas

## Setup Instructions

### 1. Supabase Setup

1. Create a free account at [Supabase](https://supabase.com)
2. Create a new project
3. Go to Project Settings > API to get your credentials:
   - `SUPABASE_URL`: Your project URL
   - `SUPABASE_KEY`: Your anon/public key

### 2. Create Database Tables

Run these SQL commands in your Supabase SQL Editor:

```sql
-- Create iot_data table
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

-- Create alerts table
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

-- Create indexes for better performance
CREATE INDEX idx_iot_batch_id ON iot_data(batch_id);
CREATE INDEX idx_iot_timestamp ON iot_data(timestamp DESC);
CREATE INDEX idx_alerts_batch_id ON alerts(batch_id);
CREATE INDEX idx_alerts_timestamp ON alerts(timestamp DESC);
```

### 3. Environment Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Supabase credentials:
   ```
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_anon_key
   ```

3. The same credentials will be used by both the backend and frontend

### 4. Running the System

The system has three components that run simultaneously:

#### Option 1: Using Replit (Recommended)
- The workflows will start automatically
- Backend runs on port 8000
- Streamlit dashboard runs on port 5000

#### Option 2: Manual Start

**Terminal 1 - FastAPI Backend:**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Streamlit Dashboard:**
```bash
streamlit run app.py --server.port 5000
```

**Terminal 3 - IoT Simulator:**
```bash
python simulator/send_data.py
```

## Usage Guide

### 1. Create Account
- Open the Streamlit dashboard
- Go to "Sign Up" tab
- Create an account with your email and password
- Select your role (Manufacturer, FDA, Distributor, or Pharmacy)

### 2. Login
- Use your credentials to log in
- You'll be directed to your role-specific dashboard

### 3. Start IoT Simulator
- Run the IoT simulator to generate fake sensor data
- It will send readings every 3-7 seconds
- 15% of readings will be out of safe range to trigger alerts

### 4. Explore Dashboards

**Manufacturer Dashboard:**
- View all IoT data and batches
- Interactive temperature and humidity charts
- Real-time monitoring

**FDA Dashboard:**
- Monitor compliance alerts
- Verify blockchain data integrity
- Check temperature violations

**Distributor Dashboard:**
- Track active shipments
- Monitor batches in transit
- View temperature history

**Pharmacy Dashboard:**
- Verify received batches
- Check quality compliance
- View batch journey

## API Endpoints

- `GET /` - API information
- `POST /iot/data` - Submit IoT sensor data
- `GET /iot/data` - Get all IoT data (limit parameter)
- `GET /iot/data/{batch_id}` - Get data for specific batch
- `GET /alerts` - Get all alerts
- `POST /verify` - Verify blockchain hash integrity
- `GET /batches` - Get all active batches
- `GET /health` - Health check

## Safe Temperature Range

Pharmaceutical products must be stored between **2°C and 8°C**.
- Alerts are automatically generated when temperature is outside this range
- High severity: < 0°C or > 10°C
- Medium severity: 0-2°C or 8-10°C

## Blockchain Verification

Each IoT record is hashed using SHA-256:
1. Record data is serialized to JSON
2. SHA-256 hash is calculated and stored
3. To verify: recalculate hash and compare with stored hash
4. Any tampering will result in hash mismatch

## Project Structure

```
pharmachain/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   └── supabase_config.py   # Supabase client setup
├── simulator/
│   ├── __init__.py
│   └── send_data.py         # IoT data simulator
├── app.py                   # Streamlit dashboard
├── .env                     # Environment variables
├── .env.example             # Environment template
└── README.md                # This file
```

## Troubleshooting

**Backend connection error:**
- Ensure FastAPI backend is running on port 8000
- Check `.env` file has correct Supabase credentials

**Authentication fails:**
- Verify Supabase credentials are correct
- Check Supabase project is active
- Ensure email confirmation is disabled in Supabase Auth settings

**No data showing:**
- Start the IoT simulator to generate data
- Verify backend is connected to Supabase
- Check Supabase tables exist

## Security Notes

### For Development/Demo Use

This MVP implementation is designed for development, testing, and educational purposes. Key security features:

- ✅ Supabase authentication with email/password
- ✅ User roles stored in dedicated `user_profiles` table with Row Level Security
- ✅ Users cannot modify their own roles after signup
- ✅ SHA-256 blockchain verification for data integrity
- ⚠️ Users self-select roles during signup (acceptable for demos, not for production)

### Production Deployment

⚠️ **Important:** Before deploying to production, especially for pharmaceutical or healthcare use:

1. **Read `SECURITY.md`** - Comprehensive security guide with:
   - Admin approval workflow implementation
   - Invitation-based signup system
   - Compliance guidelines (HIPAA, FDA 21 CFR Part 11, GDPR)
   - API security and rate limiting
   - Audit logging implementation

2. **Implement Role Approval:** Users should not self-assign roles in production. See SECURITY.md for four different approaches.

3. **Compliance Requirements:** Pharmaceutical systems require:
   - FDA 21 CFR Part 11 compliance for electronic records
   - HIPAA compliance if handling patient data
   - Regular security audits and validation
   - Audit trails and digital signatures

### Basic Security Practices

- Never commit `.env` file to version control
- Keep Supabase credentials secure
- Use environment variables for all secrets
- Rotate API keys regularly
- Use HTTPS only in production
- Implement rate limiting on public APIs
- Regular security assessments

## License

MIT License - Built for educational and demonstration purposes.
