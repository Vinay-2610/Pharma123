# Product Navigation Feature - Setup Guide

## 🎯 Overview
The Product Navigation feature adds complete shipment route tracking and visualization to your PharmaChain system using Google Maps APIs and Folium for interactive maps.

## 📋 Prerequisites

1. **Google Maps APIs Enabled:**
   - Geolocation API ✓ (already enabled)
   - Geocoding API ✓ (already enabled)
   - Directions API ✓ (already enabled)
   - Maps JavaScript API ✓ (already enabled)

2. **Supabase Table:**
   - Run the SQL script: `create_shipment_routes_table.sql`

3. **Python Packages:**
   - Install new dependencies: `pip install folium streamlit-folium polyline`

## 🚀 Installation Steps

### Step 1: Create Supabase Table

```bash
# Copy the SQL from create_shipment_routes_table.sql
# Run it in your Supabase SQL Editor
```

Or run this SQL directly:

```sql
CREATE TABLE IF NOT EXISTS shipment_routes (
    id BIGSERIAL PRIMARY KEY,
    batch_id TEXT NOT NULL,
    from_address TEXT NOT NULL,
    to_address TEXT NOT NULL,
    from_lat DOUBLE PRECISION,
    from_lng DOUBLE PRECISION,
    to_lat DOUBLE PRECISION,
    to_lng DOUBLE PRECISION,
    distance TEXT,
    duration TEXT,
    polyline TEXT,
    status TEXT DEFAULT 'in_transit',
    updated_by TEXT,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_shipment_routes_batch_id ON shipment_routes(batch_id);
CREATE INDEX idx_shipment_routes_created_at ON shipment_routes(created_at DESC);
```

### Step 2: Install Python Dependencies

```bash
cd Pharma123
pip install -r requirements.txt
```

This will install:
- `folium==0.15.1` - Interactive map visualization
- `streamlit-folium==0.15.1` - Streamlit integration for Folium
- `polyline==2.0.0` - Decode Google Maps polylines

### Step 3: Restart Backend

The backend endpoints have been added to `backend/main.py`. Restart your backend:

```bash
cd Pharma123
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 4: Integrate into Dashboards

Add the Product Navigation tab to each dashboard in `app.py`:

#### For Manufacturer Dashboard:

```python
# Add import at top of app.py
from components.product_navigation import manufacturer_navigation_tab

# In manufacturer_dashboard() function, add a new tab:
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📦 Create Batch", "🗺️ Product Navigation"])

with tab3:
    # Get list of batch IDs for this manufacturer
    batches_data = fetch_data("/batch/all")
    batch_ids = []
    if batches_data and batches_data.get("batches"):
        manufacturer_batches = [b for b in batches_data["batches"] 
                               if b.get("manufacturer_email") == st.session_state.user_email]
        batch_ids = [b["batch_id"] for b in manufacturer_batches]
    
    manufacturer_navigation_tab(st.session_state.user_email, batch_ids)
```

#### For Distributor Dashboard:

```python
# Add import
from components.product_navigation import distributor_navigation_tab

# In distributor_dashboard(), add tab:
tab1, tab2 = st.tabs(["📊 Dashboard", "🗺️ Product Navigation"])

with tab2:
    # Get approved batch IDs
    approved_batches_data = fetch_data("/batch/all")
    batch_ids = []
    if approved_batches_data and approved_batches_data.get("batches"):
        approved_batches = [b for b in approved_batches_data["batches"] 
                           if b["status"] == "approved"]
        batch_ids = [b["batch_id"] for b in approved_batches]
    
    distributor_navigation_tab(st.session_state.user_email, batch_ids)
```

#### For FDA Dashboard:

```python
# Add import
from components.product_navigation import fda_navigation_tab

# In fda_dashboard(), add tab:
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⚠️ Active Alerts", 
    "🔐 Blockchain Verification", 
    "🔗 Blockchain Explorer", 
    "📋 Audit Logs",
    "🗺️ Product Navigation"
])

with tab5:
    # Get all batch IDs
    all_batches_data = fetch_data("/batch/all")
    batch_ids = []
    if all_batches_data and all_batches_data.get("batches"):
        batch_ids = [b["batch_id"] for b in all_batches_data["batches"]]
    
    fda_navigation_tab(batch_ids)
```

#### For Pharmacy Dashboard:

```python
# Add import
from components.product_navigation import pharmacy_navigation_tab

# In pharmacy_dashboard(), add tab:
tab1, tab2 = st.tabs(["🔍 Verify Batch", "🗺️ Product Navigation"])

with tab2:
    # Get approved batch IDs
    approved_batches_data = fetch_data("/batch/all")
    batch_ids = []
    if approved_batches_data and approved_batches_data.get("batches"):
        approved_batches = [b for b in approved_batches_data["batches"] 
                           if b["status"] == "approved"]
        batch_ids = [b["batch_id"] for b in approved_batches]
    
    pharmacy_navigation_tab(batch_ids)
```

### Step 5: Restart Streamlit

```bash
cd Pharma123
streamlit run app.py
```

## 🎮 Usage Guide

### Manufacturer Workflow:

1. **Login as Manufacturer**
2. **Go to "Product Navigation" tab**
3. **Select a batch**
4. **Enter destination address** (e.g., "Distributor Warehouse, Bengaluru")
5. **Click "Generate Route"**
6. **View route on map** with distance and duration

### Distributor Workflow:

1. **Login as Distributor**
2. **Go to "Product Navigation" tab**
3. **Select a batch** (shows last destination as starting point)
4. **Enter next destination** (e.g., "FDA Testing Facility, Chennai")
5. **Click "Update Route"**
6. **View complete journey** with all route segments

### FDA Workflow:

1. **Login as FDA**
2. **Go to "Product Navigation" tab**
3. **Select a batch**
4. **Click "Verify Route Integrity"**
5. **View complete journey map** (read-only)
6. **Check route details** in table format

### Pharmacy Workflow:

1. **Login as Pharmacy**
2. **Go to "Product Navigation" tab**
3. **Select a batch**
4. **View complete journey timeline** with all stages
5. **See journey summary** (total distance, duration, legs)

## 🗺️ Features

### Interactive Maps:
- **Folium-based** interactive maps
- **Color-coded routes** for different segments
- **Markers** for start/end points
- **Popups** with route details
- **Polyline visualization** from Google Directions API

### Route Management:
- **Auto-location detection** using Google Geolocation API
- **Address geocoding** to coordinates
- **Distance and duration** calculation
- **Route continuity** tracking
- **Status updates** (in_transit, delivered, cancelled)

### Data Integrity:
- **Route verification** for FDA
- **Blockchain logging** of route updates
- **Audit trail** for all changes
- **Continuity checks** between route segments

## 🔧 API Endpoints

### POST `/shipment/route`
Create or update a shipment route
```json
{
  "batch_id": "BATCH-2025-001",
  "from_address": "Manufacturer, Bengaluru",
  "to_address": "Distributor, Chennai",
  "updated_by": "user@example.com"
}
```

### GET `/shipment/routes/{batch_id}`
Get all routes for a batch

### GET `/shipment/route/latest/{batch_id}`
Get the most recent route for a batch

### POST `/shipment/route/status`
Update route status
```json
{
  "batch_id": "BATCH-2025-001",
  "status": "delivered",
  "updated_by": "user@example.com"
}
```

### GET `/shipment/route/verify/{batch_id}`
Verify route integrity (FDA)

## 🐛 Troubleshooting

### Maps not showing:
- Check if `folium` and `streamlit-folium` are installed
- Verify Google API key is configured
- Check browser console for errors

### Routes not calculating:
- Verify Google Directions API is enabled
- Check API key has no restrictions
- Ensure addresses are valid and geocodable

### Database errors:
- Verify `shipment_routes` table exists in Supabase
- Check table permissions
- Verify Supabase credentials in `.env`

## 📊 Database Schema

```
shipment_routes
├── id (bigserial, PK)
├── batch_id (text) - Links to batches table
├── from_address (text) - Starting location
├── to_address (text) - Destination
├── from_lat (double precision) - Start coordinates
├── from_lng (double precision)
├── to_lat (double precision) - End coordinates
├── to_lng (double precision)
├── distance (text) - e.g., "45.2 km"
├── duration (text) - e.g., "1 hour 15 mins"
├── polyline (text) - Encoded route polyline
├── status (text) - in_transit, delivered, cancelled
├── updated_by (text) - User email
├── last_updated (timestamptz)
└── created_at (timestamptz)
```

## 🎨 Customization

### Change Map Colors:
Edit `components/product_navigation.py`, line ~30:
```python
colors = ['blue', 'green', 'red', 'purple', 'orange']
```

### Change Map Center:
Edit default coordinates in `create_route_map()` function

### Add More Route Statuses:
Update backend `ShipmentRoute` model and add to status dropdown

## 🚀 Next Steps

1. **Test the feature** with a sample batch
2. **Create routes** from Manufacturer to Distributor
3. **Update routes** from Distributor to FDA
4. **Verify integrity** in FDA dashboard
5. **View complete journey** in Pharmacy dashboard

## 📝 Notes

- Routes are stored permanently in Supabase
- Each route update creates a new record (history preserved)
- Maps are interactive (zoom, pan, click markers)
- Auto-refresh updates maps every 5 minutes
- All route changes are logged in audit trail

## ✅ Success Criteria

- ✓ Manufacturer can set initial route
- ✓ Distributor can update route to next destination
- ✓ FDA can verify route integrity
- ✓ Pharmacy can see complete journey timeline
- ✓ Maps display correctly with polylines
- ✓ Distance and duration calculated accurately
- ✓ All data stored in Supabase
- ✓ Audit trail captures all changes

Your Product Navigation feature is now ready to use! 🎉
