# PharmaChain - AI-Powered IoT + Blockchain Pharmaceutical Supply Chain System

## Overview

PharmaChain is a pharmaceutical supply chain monitoring system that tracks medicine batches throughout their lifecycle using simulated IoT sensors. The system provides real-time temperature and humidity monitoring with blockchain-style data integrity verification and role-based access control.

The application serves four distinct user roles (Manufacturer, FDA, Distributor, Pharmacy) with customized dashboards showing relevant supply chain data. It generates automated alerts when environmental conditions fall outside safe ranges and provides data visualization for analysis.

This is an MVP/demonstration system designed for educational purposes and prototyping, not production pharmaceutical use without significant security enhancements.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Structure

**Three-Component Architecture:**
- **Backend API** (FastAPI): REST API running on port 8000 for IoT data ingestion and querying
- **Frontend Dashboard** (Streamlit): Multi-page web interface on port 5000 with role-based views
- **IoT Simulator** (Python script): Generates fake sensor readings to simulate real hardware

This separation allows the backend to handle data processing independently while the frontend focuses on visualization and user interaction.

### Authentication & Authorization

**Supabase Auth Integration:**
- Email/password authentication through Supabase's built-in auth system
- User profiles stored in a dedicated `user_profiles` table with role assignment
- Row Level Security (RLS) policies prevent users from modifying their own roles
- Roles validated via database CHECK constraint (Manufacturer, FDA, Distributor, Pharmacy)

**Security Limitation (MVP):** Users self-select roles during signup, allowing privilege escalation. This is acceptable for demos/testing but requires admin approval workflow for production use. See SECURITY.md for production hardening steps.

### Data Storage Model

**Two-Table Schema in Supabase (PostgreSQL):**

1. **iot_data table**: Stores all sensor readings with columns for batch_id, temperature, humidity, location, sensor_id, timestamp, blockchain_hash, and is_alert flag
2. **alerts table**: Stores generated alerts when conditions exceed thresholds with batch_id, alert_type, severity, and description

**Design Decision:** Direct SQL table creation rather than ORM/migration system for simplicity in MVP. Tables created manually via Supabase SQL Editor. This approach prioritizes quick setup over schema versioning.

### Blockchain Simulation

**SHA-256 Hash-Based Integrity:**
- Each IoT data record generates a SHA-256 hash combining all sensor values
- Hash stored in blockchain_hash column alongside the data
- Provides tamper-detection capability (not a full blockchain with distributed ledger)
- Trade-off: Simplified implementation vs. true blockchain's decentralization and consensus

**Rationale:** Full blockchain infrastructure (nodes, mining, consensus) would be overkill for this use case. Hash-based verification provides data integrity verification sufficient for supply chain audit trails.

### Alert Generation

**Threshold-Based System:**
- Backend automatically evaluates temperature against safe range (2°C to 8°C)
- Generates alert records when readings fall outside bounds
- Sets is_alert boolean flag on IoT data records
- Separate alerts table allows detailed alert tracking

**Alternative Considered:** Real-time push notifications via webhooks. Rejected for MVP due to complexity; current approach uses polling for simplicity.

### Role-Based Dashboard Views

**Streamlit Multi-Page Architecture:**
- Single Streamlit app (app.py) with conditional rendering based on user role
- Session state management for authentication persistence
- Each role sees filtered data relevant to their responsibilities:
  - **Manufacturer**: Full IoT data access, batch creation, sensor charts
  - **FDA**: Alert monitoring, compliance verification, blockchain validation
  - **Distributor**: Shipment tracking, location-based monitoring
  - **Pharmacy**: Batch verification, incoming shipment validation

**Design Decision:** Single-app with conditional views vs. separate apps per role. Chosen approach reduces code duplication and simplifies deployment while maintaining clear role separation.

### Data Visualization

**Plotly + Pandas Integration:**
- Real-time temperature/humidity charts using Plotly Express
- DataFrame-based data manipulation with Pandas
- Interactive visualizations (zoom, hover, filter)

**Rationale:** Plotly chosen over simpler charting libraries (matplotlib) for interactivity. Trade-off: Larger bundle size vs. better user experience.

### IoT Data Simulation

**Randomized Sensor Readings:**
- Generates readings every few seconds with 85% in normal range, 15% anomalous
- Simulates multiple batches, sensors, and locations concurrently
- Uses Python requests library to POST to backend API

**Design Decision:** Standalone Python script vs. integrated backend task. Separate script chosen to simulate real-world external IoT devices making API calls.

## External Dependencies

### Supabase Platform
- **Purpose**: Backend-as-a-Service providing PostgreSQL database and authentication
- **Components Used**:
  - PostgreSQL database for iot_data and alerts tables
  - Supabase Auth for user management
  - Row Level Security for authorization
- **Configuration**: Requires SUPABASE_URL and SUPABASE_KEY environment variables
- **Credentials Location**: .env file (backend), Streamlit secrets (frontend)

### FastAPI Framework
- **Purpose**: High-performance Python web framework for REST API
- **Features Used**: Pydantic models for request validation, CORS middleware, async endpoints
- **Runs On**: Port 8000 (configurable)

### Streamlit Framework
- **Purpose**: Python-based web UI framework for data dashboards
- **Features Used**: Session state, tabs, forms, multi-page layout, chart components
- **Runs On**: Port 5000 (configurable)

### Python Libraries
- **requests**: HTTP client for IoT simulator to send data to backend
- **plotly**: Interactive visualization library for charts and graphs
- **pandas**: Data manipulation and analysis for dashboard queries
- **python-dotenv**: Environment variable management
- **supabase-py**: Official Supabase Python client library

### Database Configuration
- **Type**: PostgreSQL (via Supabase)
- **Tables**: Manually created via SQL Editor (not managed by migrations)
- **Setup**: Requires running SQL scripts from DATABASE_SETUP.md or QUICK_START.md
- **No ORM**: Direct SQL queries through Supabase client

### API Communication
- **Protocol**: HTTP/REST
- **Format**: JSON
- **CORS**: Enabled for all origins (suitable for development, needs restriction in production)
- **Endpoints**: /iot/data (POST), /iot/data/{batch_id} (GET), /alerts (GET), /verify (POST), /batches (GET)