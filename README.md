# 🏥 PharmaChain - IoT + Blockchain Pharmaceutical Supply Chain System

A full-stack AI-powered IoT and Blockchain-based pharmaceutical supply chain monitoring system with real-time tracking, FDA compliance workflows, and tamper detection.

## 🎯 Project Overview

PharmaChain is an end-to-end pharmaceutical supply chain traceability system that combines:
- **IoT Sensors** for real-time temperature and humidity monitoring
- **Blockchain-style Ledger** for immutable audit trails
- **FDA Compliance Workflows** with digital approval processes
- **Multi-stakeholder Dashboards** for complete transparency
- **Tamper Detection** using cryptographic hashing

## ✨ Key Features

### 1. 🔗 Blockchain Ledger
- Complete chain of custody tracking
- SHA-256 hash chaining for immutability
- Tamper detection and verification
- Public blockchain explorer
- 41+ blockchain entries auto-created

### 2. 🌡️ IoT Monitoring
- Real-time temperature and humidity tracking
- 1,252+ sensor readings collected
- Location-based monitoring
- Automatic alert generation
- Safe range: 2-8°C for pharmaceuticals

### 3. 👥 Multi-Role Dashboards
- **Manufacturer**: Create batches, view analytics
- **FDA**: Approve/reject batches, verify blockchain
- **Distributor**: Track shipments, update status
- **Pharmacy**: Verify batch quality, check compliance

### 4. ✅ FDA Compliance
- Digital approval/rejection workflow
- Mandatory FDA review before distribution
- Remarks and timestamp tracking
- Complete audit trail
- Multi-party verification

### 5. ⚠️ Tamper Detection & Alerts
- 113+ temperature alerts generated
- Blockchain hash verification
- Severity levels (High/Medium/Low)
- Real-time alert system
- Alert acknowledgment tracking

## 🏗️ Architecture

```
┌─────────────────┐
│   Streamlit     │  ← Frontend (Multi-role dashboards)
│   Dashboard     │
└────────┬────────┘
         │
┌────────▼────────┐
│    FastAPI      │  ← Backend (REST API + WebSocket)
│    Backend      │
└────────┬────────┘
         │
┌────────▼────────┐
│   Supabase      │  ← Database + Auth + Realtime
│   PostgreSQL    │
└─────────────────┘
         ▲
         │
┌────────┴────────┐
│  IoT Simulator  │  ← Sends sensor data every 5-6 seconds
└─────────────────┘
```

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.13)
- **Frontend**: Streamlit
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth
- **Visualization**: Plotly, Pandas
- **Blockchain**: SHA-256 hashing
- **IoT**: Python simulator (ESP32 compatible)

## 📦 Installation

### Prerequisites
- Python 3.13+
- Supabase account
- Git

### Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd Pharma123
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Supabase**
- Create a Supabase project at https://supabase.com
- Run the SQL scripts in order:
  - `enhanced_schema.sql` (creates all tables)
- Copy your credentials

4. **Set environment variables**
Create a `.env` file:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

5. **Create database tables**
Run the SQL scripts in Supabase SQL Editor:
- `enhanced_schema.sql`
- `create_batches_table.sql`

## 🚀 Running the Application

### Terminal 1: Backend
```bash
cd Pharma123
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2: Frontend
```bash
cd Pharma123
streamlit run app.py --server.port 5000
```

### Terminal 3: IoT Simulator
```bash
cd Pharma123
python simulator/send_data.py
```

### Access the Application
- **Frontend**: http://localhost:5000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 👤 User Roles & Login

### Manufacturer
- **Email**: fda@pharmachain.com
- **Password**: 123456
- **Features**: Create batches, view IoT analytics

### FDA
- **Email**: babu@pharmachain.com
- **Password**: 123456
- **Features**: Approve/reject batches, blockchain explorer, audit logs

### Distributor
- Create new account with role "Distributor"
- **Features**: Track shipments, update status

### Pharmacy
- Create new account with role "Pharmacy"
- **Features**: Verify batches, check quality

## 📊 Database Schema

### Core Tables
- `iot_data` - IoT sensor readings (1,252+ records)
- `batches` - Batch information and FDA approval status
- `alerts` - Temperature violation alerts (113+ records)
- `user_profiles` - User accounts with roles

### Blockchain & Audit
- `ledger` - Blockchain-style event log (41+ blocks)
- `alerts_log` - Real-time alert tracking
- `audit_logs` - Complete user action history
- `signatures` - Multi-party verification

### Optional
- `shipments` - Enhanced shipment tracking
- `vehicle_telemetry` - Vehicle health monitoring

## 🔐 Security Features

1. **Blockchain Immutability**: Hash chaining prevents tampering
2. **Audit Trail**: Every action logged with timestamps
3. **Role-Based Access**: Different permissions per role
4. **Digital Signatures**: FDA approval tracking
5. **Tamper Detection**: Automatic hash verification

## 📈 API Endpoints

### IoT Data
- `POST /iot/data` - Receive sensor data
- `GET /iot/data` - Get all readings
- `GET /iot/data/{batch_id}` - Get batch readings

### Batch Management
- `POST /batch/create` - Create new batch
- `GET /batch/pending` - Get pending approvals
- `POST /batch/approve` - Approve/reject batch
- `GET /batch/all` - Get all batches

### Blockchain
- `POST /ledger/add` - Add ledger entry
- `GET /ledger/{batch_id}` - Get batch ledger
- `GET /ledger/verify/all` - Public blockchain explorer

### Audit & Alerts
- `POST /audit/log` - Create audit log
- `GET /audit/logs` - Get audit trail
- `GET /alerts/realtime` - Get active alerts
- `POST /alerts/acknowledge/{id}` - Acknowledge alert

## 🎯 Project Objectives (All Implemented ✅)

1. ✅ **Digital Ledger** - End-to-end drug traceability
2. ✅ **IoT Integration** - Environmental condition monitoring
3. ✅ **Traceability Dashboard** - All stakeholder visibility
4. ✅ **FDA Compliance** - Digital approval workflows
5. ✅ **Tamper Detection** - IoT log-based alerts

## 📝 Documentation

- `WORKFLOW_GUIDE.md` - Complete workflow documentation
- `REALTIME_FEATURES.md` - Real-time features guide
- `AUDIT_LOGGING_GUIDE.md` - Audit logging documentation
- `OBJECTIVES_STATUS.md` - Project objectives status

## 🧪 Testing

### Verify Tables
```bash
python verify_tables.py
```

### Test Audit Logging
```bash
python test_audit_logging.py
```

### Test Database Connection
```bash
python test_connection.py
```

## 📊 Current Metrics

- **Blockchain Entries**: 41+ blocks
- **IoT Readings**: 1,252+ records
- **Alerts Generated**: 113+ alerts
- **Batches Tracked**: 4+ batches
- **Registered Users**: 11 users
- **API Endpoints**: 20+ endpoints
- **Database Tables**: 10 tables

## 🔄 Workflow Example

```
1. Manufacturer creates batch
   ↓
2. Batch status: PENDING
   ↓
3. FDA reviews batch details
   ↓
4. FDA approves with remarks
   ↓
5. Batch status: APPROVED
   ↓
6. Distributor picks up batch
   ↓
7. IoT sensors monitor during transit
   ↓
8. Temperature alerts if out of range
   ↓
9. Pharmacy receives and verifies
   ↓
10. Complete blockchain audit trail
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👨‍💻 Author

Created as part of an IoT + Blockchain pharmaceutical supply chain project.

## 🙏 Acknowledgments

- Supabase for database and authentication
- Streamlit for rapid dashboard development
- FastAPI for high-performance backend
- Plotly for interactive visualizations

## 📞 Support

For issues or questions:
1. Check the documentation files
2. Review API docs at `/docs`
3. Check audit logs for errors
4. Verify database tables exist

---

**Status**: Production Ready ✅  
**Last Updated**: November 2025  
**Version**: 1.0.0
