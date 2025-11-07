from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import hashlib
import json
import asyncio
import requests
import os
from dotenv import load_dotenv
from backend.supabase_config import get_supabase_client

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

app = FastAPI(title="PharmaChain API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Google Maps API Helper Functions
def get_coordinates():
    """Fetch approximate coordinates using Google Geolocation API"""
    if not GOOGLE_API_KEY:
        return None, None
    try:
        res = requests.post(
            f"https://www.googleapis.com/geolocation/v1/geolocate?key={GOOGLE_API_KEY}",
            timeout=5
        )
        data = res.json()
        if "location" in data:
            return data["location"]["lat"], data["location"]["lng"]
        return None, None
    except:
        return None, None

def get_place_name(lat, lng):
    """Convert coordinates into a readable address using Geocoding API"""
    if not GOOGLE_API_KEY:
        return f"Location ({lat:.4f}, {lng:.4f})"
    try:
        res = requests.get(
            f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={GOOGLE_API_KEY}",
            timeout=5
        )
        data = res.json()
        
        # Check for API errors
        if data.get("status") == "REQUEST_DENIED":
            print(f"Geocoding API Error: {data.get('error_message', 'API not enabled')}")
            return f"Location ({lat:.4f}, {lng:.4f}) - Enable Geocoding API"
        
        if data.get("results"):
            return data["results"][0]["formatted_address"]
        
        # Fallback with coordinates
        return f"Location ({lat:.4f}, {lng:.4f})"
    except Exception as e:
        print(f"Geocoding error: {str(e)}")
        return f"Location ({lat:.4f}, {lng:.4f})"

def get_route_directions(origin, destination):
    """Fetch the driving route between two coordinates using Directions API"""
    if not GOOGLE_API_KEY:
        return {"error": "Google API key not configured"}
    try:
        url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&key={GOOGLE_API_KEY}"
        res = requests.get(url, timeout=10)
        return res.json()
    except:
        return {"error": "Failed to fetch route"}

class IoTData(BaseModel):
    batch_id: str
    temperature: float
    humidity: float
    location: str
    sensor_id: str
    timestamp: Optional[str] = None

class BlockchainVerification(BaseModel):
    record_id: int

class BatchStatusUpdate(BaseModel):
    batch_id: str
    status: str  # "Created", "Picked Up", "In Transit", "Delivered"
    updated_by: str  # Role of user updating

class BatchCreate(BaseModel):
    batch_id: str
    manufacturer_email: str
    product_name: str
    quantity: int
    manufacturing_date: str
    expiry_date: str
    initial_location: str

class BatchApproval(BaseModel):
    batch_id: str
    approved: bool  # True for approve, False for reject
    fda_email: str
    remarks: str

class LedgerEntry(BaseModel):
    batch_id: str
    event: str
    actor_role: str
    actor_email: str
    data: Optional[dict] = None

class AuditLog(BaseModel):
    user_email: str
    role: str
    action: str
    batch_id: Optional[str] = None
    details: Optional[dict] = None

@app.get("/")
async def root():
    return {
        "message": "PharmaChain API",
        "version": "1.0.0",
        "endpoints": [
            "/iot/data",
            "/iot/data/{batch_id}",
            "/alerts",
            "/verify",
            "/batches"
        ]
    }

@app.post("/iot/data")
async def receive_iot_data(data: IoTData):
    try:
        supabase = get_supabase_client()
        
        if not data.timestamp:
            data.timestamp = datetime.utcnow().isoformat()
        
        # Auto-detect location if "Auto-Detected" is sent
        location = data.location
        if location == "Auto-Detected":
            if GOOGLE_API_KEY:
                lat, lng = get_coordinates()
                if lat and lng:
                    address = get_place_name(lat, lng)
                    # Only add coordinates if address doesn't already contain them
                    if "(" not in address:
                        location = f"{address} ({lat:.4f}, {lng:.4f})"
                    else:
                        location = address
                else:
                    # Fallback when API call fails
                    location = "Location Detection Failed (Check API Key)"
            else:
                # Fallback when API key is not configured
                location = "Auto-Detection Disabled (Configure GOOGLE_API_KEY)"
        
        data_dict = {
            "batch_id": data.batch_id,
            "temperature": data.temperature,
            "humidity": data.humidity,
            "location": location,  # Use processed location
            "sensor_id": data.sensor_id,
            "timestamp": data.timestamp
        }
        
        data_string = json.dumps(data_dict, sort_keys=True)
        blockchain_hash = hashlib.sha256(data_string.encode()).hexdigest()
        data_dict["blockchain_hash"] = blockchain_hash
        
        is_alert = data.temperature < 2.0 or data.temperature > 8.0
        data_dict["is_alert"] = is_alert
        
        result = supabase.table("iot_data").insert(data_dict).execute()
        
        if is_alert:
            alert_data = {
                "batch_id": data.batch_id,
                "alert_type": "Temperature Out of Range",
                "severity": "high" if (data.temperature < 0 or data.temperature > 10) else "medium",
                "message": f"Temperature {data.temperature}°C is outside safe range (2-8°C)",
                "timestamp": data.timestamp,
                "temperature": data.temperature,
                "location": data.location
            }
            supabase.table("alerts").insert(alert_data).execute()
            
            # Also log to alerts_log for real-time tracking
            try:
                supabase.table("alerts_log").insert(alert_data).execute()
            except:
                pass
        
        # Skip ledger logging for IoT readings to prevent timeout
        # Ledger is still used for important events (batch creation, approval, etc.)
        
        return {
            "status": "success",
            "message": "IoT data received and stored",
            "blockchain_hash": blockchain_hash,
            "alert_generated": is_alert,
            "data": result.data[0] if result.data else None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/iot/data")
async def get_all_iot_data(limit: int = 100):
    try:
        supabase = get_supabase_client()
        result = supabase.table("iot_data").select("*").order("timestamp", desc=True).limit(limit).execute()
        return {"status": "success", "data": result.data, "count": len(result.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/iot/data/{batch_id}")
async def get_batch_data(batch_id: str):
    try:
        supabase = get_supabase_client()
        result = supabase.table("iot_data").select("*").eq("batch_id", batch_id).order("timestamp", desc=True).execute()
        return {"status": "success", "batch_id": batch_id, "data": result.data, "count": len(result.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts")
async def get_alerts(limit: int = 50):
    try:
        supabase = get_supabase_client()
        result = supabase.table("alerts").select("*").order("timestamp", desc=True).limit(limit).execute()
        return {"status": "success", "alerts": result.data, "count": len(result.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify")
async def verify_blockchain_hash(verification: BlockchainVerification):
    try:
        supabase = get_supabase_client()
        result = supabase.table("iot_data").select("*").eq("id", verification.record_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Record not found")
        
        record = result.data[0]
        stored_hash = record.get("blockchain_hash")
        
        data_dict = {
            "batch_id": record["batch_id"],
            "temperature": record["temperature"],
            "humidity": record["humidity"],
            "location": record["location"],
            "sensor_id": record["sensor_id"],
            "timestamp": record["timestamp"]
        }
        
        data_string = json.dumps(data_dict, sort_keys=True)
        calculated_hash = hashlib.sha256(data_string.encode()).hexdigest()
        
        is_valid = stored_hash == calculated_hash
        
        return {
            "status": "success",
            "record_id": verification.record_id,
            "is_valid": is_valid,
            "stored_hash": stored_hash,
            "calculated_hash": calculated_hash,
            "message": "Data integrity verified" if is_valid else "Data has been tampered with!",
            "record": record
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/batches")
async def get_all_batches():
    try:
        supabase = get_supabase_client()
        result = supabase.table("iot_data").select("batch_id").execute()
        
        unique_batches = list(set([item["batch_id"] for item in result.data]))
        
        batch_info = []
        for batch_id in unique_batches:
            batch_result = supabase.table("iot_data").select("*").eq("batch_id", batch_id).order("timestamp", desc=True).execute()
            if batch_result.data:
                latest = batch_result.data[0]
                batch_info.append({
                    "batch_id": batch_id,
                    "latest_temperature": latest["temperature"],
                    "latest_humidity": latest["humidity"],
                    "location": latest["location"],
                    "last_update": latest["timestamp"],
                    "record_count": len(batch_result.data)
                })
        
        return {"status": "success", "batches": batch_info, "count": len(batch_info)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch/status")
async def update_batch_status(status_update: BatchStatusUpdate):
    try:
        supabase = get_supabase_client()
        
        # Check if batch_status table exists, if not use a metadata approach
        # For now, we'll store status in a separate table or use iot_data metadata
        
        # Get the latest record for this batch
        result = supabase.table("iot_data").select("*").eq("batch_id", status_update.batch_id).order("timestamp", desc=True).limit(1).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        # Insert a status update record (we'll use iot_data with a special marker)
        status_record = {
            "batch_id": status_update.batch_id,
            "temperature": result.data[0]["temperature"],
            "humidity": result.data[0]["humidity"],
            "location": f"Status: {status_update.status}",
            "sensor_id": f"STATUS_UPDATE_BY_{status_update.updated_by}",
            "timestamp": datetime.utcnow().isoformat(),
            "blockchain_hash": hashlib.sha256(f"{status_update.batch_id}{status_update.status}".encode()).hexdigest(),
            "is_alert": False
        }
        
        supabase.table("iot_data").insert(status_record).execute()
        
        return {
            "status": "success",
            "message": f"Batch {status_update.batch_id} status updated to {status_update.status}",
            "batch_id": status_update.batch_id,
            "new_status": status_update.status
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/batch/{batch_id}/status")
async def get_batch_status(batch_id: str):
    try:
        supabase = get_supabase_client()
        
        # Look for status update records
        result = supabase.table("iot_data").select("*").eq("batch_id", batch_id).order("timestamp", desc=True).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        # Find the latest status update
        current_status = "Created"
        for record in result.data:
            if "Status:" in record.get("location", ""):
                current_status = record["location"].replace("Status: ", "")
                break
        
        return {
            "status": "success",
            "batch_id": batch_id,
            "current_status": current_status,
            "total_records": len(result.data)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify/batch/{batch_id}")
async def verify_batch_integrity(batch_id: str):
    try:
        supabase = get_supabase_client()
        result = supabase.table("iot_data").select("*").eq("batch_id", batch_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        total_records = len(result.data)
        valid_records = 0
        invalid_records = 0
        
        for record in result.data:
            stored_hash = record.get("blockchain_hash")
            
            # Skip status update records
            if "STATUS_UPDATE" in record.get("sensor_id", ""):
                continue
            
            data_dict = {
                "batch_id": record["batch_id"],
                "temperature": record["temperature"],
                "humidity": record["humidity"],
                "location": record["location"],
                "sensor_id": record["sensor_id"],
                "timestamp": record["timestamp"]
            }
            
            data_string = json.dumps(data_dict, sort_keys=True)
            calculated_hash = hashlib.sha256(data_string.encode()).hexdigest()
            
            if stored_hash == calculated_hash:
                valid_records += 1
            else:
                invalid_records += 1
        
        is_valid = invalid_records == 0
        
        return {
            "status": "success",
            "batch_id": batch_id,
            "is_valid": is_valid,
            "total_records": total_records,
            "valid_records": valid_records,
            "invalid_records": invalid_records,
            "integrity_percentage": (valid_records / total_records * 100) if total_records > 0 else 0,
            "message": "Batch integrity verified - No tampering detected" if is_valid else "WARNING: Data tampering detected!"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch/create")
async def create_batch(batch: BatchCreate):
    try:
        supabase = get_supabase_client()
        
        batch_data = {
            "batch_id": batch.batch_id,
            "manufacturer_email": batch.manufacturer_email,
            "product_name": batch.product_name,
            "quantity": batch.quantity,
            "manufacturing_date": batch.manufacturing_date,
            "expiry_date": batch.expiry_date,
            "initial_location": batch.initial_location,
            "status": "pending"
        }
        
        result = supabase.table("batches").insert(batch_data).execute()
        
        # Log to audit trail
        log_audit(
            user_email=batch.manufacturer_email,
            role="Manufacturer",
            action="Created Batch",
            batch_id=batch.batch_id,
            details={
                "product_name": batch.product_name,
                "quantity": batch.quantity,
                "location": batch.initial_location
            }
        )
        
        # Add to blockchain ledger
        add_to_ledger(
            batch_id=batch.batch_id,
            event="Batch Created",
            actor_role="Manufacturer",
            actor_email=batch.manufacturer_email,
            data=batch_data
        )
        
        return {
            "status": "success",
            "message": f"Batch {batch.batch_id} created and pending FDA approval",
            "data": result.data[0] if result.data else None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/batch/pending")
async def get_pending_batches():
    try:
        supabase = get_supabase_client()
        result = supabase.table("batches").select("*").eq("status", "pending").order("created_at", desc=True).execute()
        return {"status": "success", "batches": result.data, "count": len(result.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/batch/all")
async def get_all_batch_records():
    try:
        supabase = get_supabase_client()
        # Add limit to prevent timeout on large datasets
        result = supabase.table("batches").select("*").order("created_at", desc=True).limit(100).execute()
        return {"status": "success", "batches": result.data if result.data else [], "count": len(result.data) if result.data else 0}
    except Exception as e:
        print(f"Error in get_all_batch_records: {str(e)}")
        # Return empty result instead of error to prevent dashboard crashes
        return {"status": "error", "batches": [], "count": 0, "error": str(e)}

@app.post("/batch/approve")
async def approve_or_reject_batch(approval: BatchApproval):
    try:
        supabase = get_supabase_client()
        
        update_data = {
            "status": "approved" if approval.approved else "rejected",
            "fda_approved_by": approval.fda_email,
            "fda_approval_date": datetime.utcnow().isoformat(),
            "fda_remarks": approval.remarks
        }
        
        result = supabase.table("batches").update(update_data).eq("batch_id", approval.batch_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        action = "Approved Batch" if approval.approved else "Rejected Batch"
        
        # Log to audit trail
        log_audit(
            user_email=approval.fda_email,
            role="FDA",
            action=action,
            batch_id=approval.batch_id,
            details={
                "remarks": approval.remarks,
                "decision": "approved" if approval.approved else "rejected"
            }
        )
        
        # Add to blockchain ledger
        add_to_ledger(
            batch_id=approval.batch_id,
            event=f"FDA {action}",
            actor_role="FDA",
            actor_email=approval.fda_email,
            data={
                "approved": approval.approved,
                "remarks": approval.remarks
            }
        )
        
        action_text = "approved" if approval.approved else "rejected"
        return {
            "status": "success",
            "message": f"Batch {approval.batch_id} has been {action_text} by FDA",
            "data": result.data[0]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/batch/details/{batch_id}")
async def get_batch_details(batch_id: str):
    try:
        supabase = get_supabase_client()
        result = supabase.table("batches").select("*").eq("batch_id", batch_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        return {"status": "success", "batch": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def add_to_ledger(batch_id: str, event: str, actor_role: str, actor_email: str, data: dict = None):
    """Add an entry to the blockchain ledger"""
    try:
        supabase = get_supabase_client()
        
        # Get the previous hash
        try:
            prev_result = supabase.table("ledger").select("curr_hash").eq("batch_id", batch_id).order("timestamp", desc=True).limit(1).execute()
            prev_hash = prev_result.data[0]["curr_hash"] if prev_result.data else "0" * 64
        except:
            prev_hash = "0" * 64
        
        # Create current hash
        ledger_data = {
            "batch_id": batch_id,
            "event": event,
            "actor_role": actor_role,
            "actor_email": actor_email,
            "timestamp": datetime.utcnow().isoformat(),
            "prev_hash": prev_hash,
            "data": data or {}
        }
        
        data_string = json.dumps(ledger_data, sort_keys=True)
        curr_hash = hashlib.sha256(data_string.encode()).hexdigest()
        ledger_data["curr_hash"] = curr_hash
        
        # Insert into ledger
        result = supabase.table("ledger").insert(ledger_data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Ledger error: {str(e)}")
        return None

def log_audit(user_email: str, role: str, action: str, batch_id: str = None, details: dict = None):
    """Log user action to audit trail"""
    try:
        supabase = get_supabase_client()
        
        audit_data = {
            "user_email": user_email,
            "role": role,
            "action": action,
            "batch_id": batch_id,
            "details": details or {},
            "hash_ref": hashlib.sha256(f"{user_email}{action}{datetime.utcnow().isoformat()}".encode()).hexdigest()
        }
        
        supabase.table("audit_logs").insert(audit_data).execute()
    except Exception as e:
        print(f"Audit log error: {str(e)}")

@app.post("/ledger/add")
async def add_ledger_entry(entry: LedgerEntry):
    try:
        result = add_to_ledger(
            batch_id=entry.batch_id,
            event=entry.event,
            actor_role=entry.actor_role,
            actor_email=entry.actor_email,
            data=entry.data
        )
        
        if result:
            return {"status": "success", "message": "Ledger entry added", "data": result}
        else:
            raise HTTPException(status_code=500, detail="Failed to add ledger entry")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ledger/{batch_id}")
async def get_batch_ledger(batch_id: str):
    try:
        supabase = get_supabase_client()
        result = supabase.table("ledger").select("*").eq("batch_id", batch_id).order("timestamp", desc=False).execute()
        
        # Verify blockchain integrity
        is_valid = True
        for i in range(1, len(result.data)):
            if result.data[i]["prev_hash"] != result.data[i-1]["curr_hash"]:
                is_valid = False
                result.data[i]["tampered"] = True
        
        return {
            "status": "success",
            "batch_id": batch_id,
            "ledger": result.data,
            "count": len(result.data),
            "blockchain_valid": is_valid
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ledger/verify/all")
async def verify_all_ledgers():
    """Public blockchain explorer - verify all batches"""
    try:
        supabase = get_supabase_client()
        
        # Get all unique batch IDs
        batches_result = supabase.table("ledger").select("batch_id").execute()
        unique_batches = list(set([b["batch_id"] for b in batches_result.data]))
        
        verification_results = []
        
        for batch_id in unique_batches:
            ledger_result = supabase.table("ledger").select("*").eq("batch_id", batch_id).order("timestamp", desc=False).execute()
            
            is_valid = True
            tampered_blocks = []
            
            for i in range(1, len(ledger_result.data)):
                if ledger_result.data[i]["prev_hash"] != ledger_result.data[i-1]["curr_hash"]:
                    is_valid = False
                    tampered_blocks.append(i)
            
            verification_results.append({
                "batch_id": batch_id,
                "total_blocks": len(ledger_result.data),
                "is_valid": is_valid,
                "tampered_blocks": tampered_blocks
            })
        
        return {
            "status": "success",
            "total_batches": len(unique_batches),
            "verifications": verification_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/audit/log")
async def create_audit_log(log: AuditLog):
    try:
        log_audit(
            user_email=log.user_email,
            role=log.role,
            action=log.action,
            batch_id=log.batch_id,
            details=log.details
        )
        return {"status": "success", "message": "Audit log created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/audit/logs")
async def get_audit_logs(limit: int = 100, batch_id: Optional[str] = None):
    try:
        supabase = get_supabase_client()
        
        query = supabase.table("audit_logs").select("*")
        
        if batch_id:
            query = query.eq("batch_id", batch_id)
        
        result = query.order("timestamp", desc=True).limit(limit).execute()
        
        return {"status": "success", "logs": result.data, "count": len(result.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts/realtime")
async def get_realtime_alerts(limit: int = 50):
    try:
        supabase = get_supabase_client()
        result = supabase.table("alerts_log").select("*").eq("acknowledged", False).order("timestamp", desc=True).limit(limit).execute()
        return {"status": "success", "alerts": result.data, "count": len(result.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/alerts/acknowledge/{alert_id}")
async def acknowledge_alert(alert_id: int, user_email: str):
    try:
        supabase = get_supabase_client()
        
        update_data = {
            "acknowledged": True,
            "acknowledged_by": user_email,
            "acknowledged_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("alerts_log").update(update_data).eq("id", alert_id).execute()
        
        if result.data:
            log_audit(user_email, "Unknown", f"Acknowledged alert {alert_id}", details={"alert_id": alert_id})
        
        return {"status": "success", "message": "Alert acknowledged"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/route")
async def get_shipment_route(origin: str = "Chennai, Tamil Nadu", destination: str = "Bengaluru, Karnataka"):
    """Get live route between origin and destination using Google Directions API"""
    try:
        route_data = get_route_directions(origin, destination)
        return {
            "status": "success",
            "origin": origin,
            "destination": destination,
            "route": route_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/geocode")
async def geocode_location(address: str):
    """Convert address to coordinates"""
    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="Google API key not configured")
    try:
        res = requests.get(
            f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_API_KEY}",
            timeout=5
        )
        data = res.json()
        if data.get("results"):
            location = data["results"][0]["geometry"]["location"]
            return {
                "status": "success",
                "address": address,
                "lat": location["lat"],
                "lng": location["lng"],
                "formatted_address": data["results"][0]["formatted_address"]
            }
        raise HTTPException(status_code=404, detail="Location not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "PharmaChain Backend", "google_maps": "enabled" if GOOGLE_API_KEY else "disabled"}


# ============================================================================
# PRODUCT NAVIGATION / SHIPMENT ROUTES FEATURE
# ============================================================================

class ShipmentRoute(BaseModel):
    batch_id: str
    from_address: str
    to_address: str
    updated_by: str

class RouteUpdate(BaseModel):
    batch_id: str
    status: str  # "in_transit", "delivered", "cancelled"
    updated_by: str

def geocode_address(address: str):
    """Convert address to coordinates using Google Geocoding API"""
    if not GOOGLE_API_KEY:
        return None, None
    try:
        res = requests.get(
            f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_API_KEY}",
            timeout=5
        )
        data = res.json()
        if data.get("results"):
            location = data["results"][0]["geometry"]["location"]
            return location["lat"], location["lng"]
        return None, None
    except:
        return None, None

def get_route_directions(origin_lat, origin_lng, dest_lat, dest_lng):
    """Get route details using Google Directions API"""
    if not GOOGLE_API_KEY:
        return None
    try:
        url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin_lat},{origin_lng}&destination={dest_lat},{dest_lng}&key={GOOGLE_API_KEY}"
        res = requests.get(url, timeout=10)
        data = res.json()
        
        if data.get("status") == "OK" and data.get("routes"):
            route = data["routes"][0]
            leg = route["legs"][0]
            
            return {
                "distance": leg["distance"]["text"],
                "duration": leg["duration"]["text"],
                "polyline": route["overview_polyline"]["points"],
                "start_address": leg["start_address"],
                "end_address": leg["end_address"]
            }
        return None
    except Exception as e:
        print(f"Directions API error: {str(e)}")
        return None

@app.post("/shipment/route")
async def create_or_update_shipment_route(route: ShipmentRoute):
    """
    Create or update a shipment route for a batch
    - Geocodes addresses to coordinates
    - Calculates route using Google Directions API
    - Stores in Supabase shipment_routes table
    """
    try:
        supabase = get_supabase_client()
        
        # Geocode from address
        from_lat, from_lng = geocode_address(route.from_address)
        if not from_lat or not from_lng:
            raise HTTPException(status_code=400, detail="Could not geocode 'from' address")
        
        # Geocode to address
        to_lat, to_lng = geocode_address(route.to_address)
        if not to_lat or not to_lng:
            raise HTTPException(status_code=400, detail="Could not geocode 'to' address")
        
        # Get route directions
        directions = get_route_directions(from_lat, from_lng, to_lat, to_lng)
        if not directions:
            raise HTTPException(status_code=400, detail="Could not calculate route")
        
        # Prepare route data
        route_data = {
            "batch_id": route.batch_id,
            "from_address": directions["start_address"],
            "to_address": directions["end_address"],
            "from_lat": from_lat,
            "from_lng": from_lng,
            "to_lat": to_lat,
            "to_lng": to_lng,
            "distance": directions["distance"],
            "duration": directions["duration"],
            "polyline": directions["polyline"],
            "status": "in_transit",
            "updated_by": route.updated_by,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Insert into Supabase
        result = supabase.table("shipment_routes").insert(route_data).execute()
        
        # Log to audit trail
        log_audit(
            user_email=route.updated_by,
            role="System",
            action="Created Shipment Route",
            batch_id=route.batch_id,
            details={
                "from": directions["start_address"],
                "to": directions["end_address"],
                "distance": directions["distance"],
                "duration": directions["duration"]
            }
        )
        
        return {
            "status": "success",
            "message": f"Route created for batch {route.batch_id}",
            "data": result.data[0] if result.data else None,
            "route_details": {
                "distance": directions["distance"],
                "duration": directions["duration"],
                "from": directions["start_address"],
                "to": directions["end_address"]
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/shipment/routes/{batch_id}")
async def get_shipment_routes(batch_id: str):
    """
    Get all route entries for a specific batch
    Returns the complete journey timeline
    """
    try:
        supabase = get_supabase_client()
        result = supabase.table("shipment_routes").select("*").eq("batch_id", batch_id).order("created_at", desc=False).execute()
        
        return {
            "status": "success",
            "batch_id": batch_id,
            "routes": result.data,
            "count": len(result.data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/shipment/route/latest/{batch_id}")
async def get_latest_shipment_route(batch_id: str):
    """
    Get the most recent route entry for a batch
    """
    try:
        supabase = get_supabase_client()
        result = supabase.table("shipment_routes").select("*").eq("batch_id", batch_id).order("created_at", desc=True).limit(1).execute()
        
        if not result.data:
            return {
                "status": "success",
                "batch_id": batch_id,
                "route": None,
                "message": "No route data found for this batch"
            }
        
        return {
            "status": "success",
            "batch_id": batch_id,
            "route": result.data[0]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/shipment/route/status")
async def update_route_status(update: RouteUpdate):
    """
    Update the status of the latest route for a batch
    """
    try:
        supabase = get_supabase_client()
        
        # Get the latest route
        result = supabase.table("shipment_routes").select("*").eq("batch_id", update.batch_id).order("created_at", desc=True).limit(1).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="No route found for this batch")
        
        route_id = result.data[0]["id"]
        
        # Update status
        update_data = {
            "status": update.status,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        updated = supabase.table("shipment_routes").update(update_data).eq("id", route_id).execute()
        
        # Log to audit trail
        log_audit(
            user_email=update.updated_by,
            role="System",
            action="Updated Route Status",
            batch_id=update.batch_id,
            details={"new_status": update.status}
        )
        
        return {
            "status": "success",
            "message": f"Route status updated to {update.status}",
            "data": updated.data[0] if updated.data else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/shipment/route/verify/{batch_id}")
async def verify_route_integrity(batch_id: str):
    """
    Verify route data integrity for FDA dashboard
    Checks if route data is consistent and valid
    """
    try:
        supabase = get_supabase_client()
        result = supabase.table("shipment_routes").select("*").eq("batch_id", batch_id).order("created_at", desc=False).execute()
        
        if not result.data:
            return {
                "status": "success",
                "batch_id": batch_id,
                "is_valid": False,
                "message": "No route data found",
                "total_routes": 0
            }
        
        routes = result.data
        is_valid = True
        issues = []
        
        # Check for data consistency
        for i, route in enumerate(routes):
            # Check if required fields are present
            if not route.get("from_address") or not route.get("to_address"):
                is_valid = False
                issues.append(f"Route {i+1}: Missing address data")
            
            if not route.get("distance") or not route.get("duration"):
                is_valid = False
                issues.append(f"Route {i+1}: Missing distance/duration data")
            
            # Check if next route starts where previous ended
            if i > 0:
                prev_route = routes[i-1]
                # This is a soft check - addresses might be slightly different
                # but coordinates should be close
                if route.get("from_lat") and prev_route.get("to_lat"):
                    lat_diff = abs(route["from_lat"] - prev_route["to_lat"])
                    lng_diff = abs(route["from_lng"] - prev_route["to_lng"])
                    if lat_diff > 0.1 or lng_diff > 0.1:  # ~11km tolerance
                        issues.append(f"Route {i+1}: Discontinuous journey detected")
        
        return {
            "status": "success",
            "batch_id": batch_id,
            "is_valid": is_valid,
            "total_routes": len(routes),
            "issues": issues if not is_valid else [],
            "message": "Route integrity verified" if is_valid else "Route integrity issues detected",
            "routes_summary": [
                {
                    "from": r["from_address"],
                    "to": r["to_address"],
                    "distance": r["distance"],
                    "duration": r["duration"],
                    "timestamp": r["created_at"]
                }
                for r in routes
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
