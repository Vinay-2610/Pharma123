# PharmaChain Approval Workflow Guide

## 🔄 Complete Workflow

### Step 1: Manufacturer Creates Batch
1. Login as **Manufacturer** (fda@pharmachain.com / 123456)
2. Click **"📦 Create New Shipment"** to expand the form
3. Fill in batch details:
   - Batch ID (e.g., BATCH-2025-010)
   - Product Name (e.g., Insulin Vials)
   - Quantity (e.g., 1000 units)
   - Manufacturing Date
   - Expiry Date
   - Initial Location
   - Initial Temperature & Humidity
4. Click **"🚀 Create Batch & Submit for FDA Approval"**
5. Status: **PENDING FDA REVIEW**

### Step 2: FDA Reviews and Approves/Rejects
1. Login as **FDA** (babu@pharmachain.com / 123456)
2. See **"📋 Pending Batch Approvals"** section
3. Review batch details:
   - Manufacturer info
   - Product details
   - Manufacturing/Expiry dates
   - Blockchain integrity verification
4. Enter FDA remarks in the text area
5. Click either:
   - **✅ Approve** - Batch moves to approved status
   - **❌ Reject** - Batch is rejected with remarks

### Step 3: Distributor Tracks Approved Batches
1. Login as **Distributor**
2. See FDA approval metrics:
   - ✅ FDA Approved count
   - ⏳ Pending Approval count
   - ❌ Rejected count
3. Track approved shipments
4. Update shipment status:
   - Created → Picked Up → In Transit → Delivered

### Step 4: Pharmacy Verifies Batches
1. Login as **Pharmacy**
2. See only FDA-approved batches
3. Verify batch quality and compliance
4. Check blockchain integrity
5. Accept or reject delivery

## 📊 Database Tables

### batches table (NEW)
```sql
- id: Primary key
- batch_id: Unique batch identifier
- manufacturer_email: Who created it
- product_name: Product name
- quantity: Number of units
- manufacturing_date: When manufactured
- expiry_date: Expiration date
- initial_location: Starting location
- status: pending/approved/rejected/in_transit/delivered
- fda_approved_by: FDA email who approved/rejected
- fda_approval_date: When decision was made
- fda_remarks: FDA comments
```

## 🔧 Setup Instructions

### 1. Create the batches table in Supabase
Run this SQL in Supabase SQL Editor:

```sql
CREATE TABLE IF NOT EXISTS batches (
    id BIGSERIAL PRIMARY KEY,
    batch_id TEXT UNIQUE NOT NULL,
    manufacturer_email TEXT NOT NULL,
    product_name TEXT,
    quantity INTEGER,
    manufacturing_date DATE,
    expiry_date DATE,
    initial_location TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'in_transit', 'delivered')),
    fda_approved_by TEXT,
    fda_approval_date TIMESTAMPTZ,
    fda_remarks TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_batches_batch_id ON batches(batch_id);
CREATE INDEX idx_batches_status ON batches(status);
```

### 2. Start the services

**Terminal 1 - Backend:**
```bash
cd Pharma123
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Streamlit (Already Running):**
```bash
cd Pharma123
streamlit run app.py --server.port 5000
```

**Terminal 3 - IoT Simulator (Already Running):**
```bash
cd Pharma123
python simulator/send_data.py
```

### 3. Access the application
- **Frontend:** http://localhost:5000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## 🎯 Test the Workflow

1. **Create a batch** as Manufacturer
2. **Approve it** as FDA with remarks like "Quality standards met"
3. **Track it** as Distributor
4. **Verify it** as Pharmacy

## 📝 API Endpoints Added

- `POST /batch/create` - Create new batch
- `GET /batch/pending` - Get pending batches
- `GET /batch/all` - Get all batches
- `POST /batch/approve` - Approve/reject batch
- `GET /batch/details/{batch_id}` - Get batch details

## ✅ Features Implemented

- ✅ Manufacturer can create batches with full details
- ✅ Batches start in "pending" status
- ✅ FDA can see all pending batches
- ✅ FDA can approve with remarks
- ✅ FDA can reject with reasons
- ✅ Blockchain verification before approval
- ✅ Distributor sees approval status
- ✅ Pharmacy sees only approved batches
- ✅ Complete audit trail with timestamps
