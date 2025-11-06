from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import hashlib
import json
import asyncio
from backend.supabase_config import get_supabase_client

app = FastAPI(title="PharmaChain API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        
        data_dict = {
            "batch_id": data.batch_id,
            "temperature": data.temperature,
            "humidity": data.humidity,
            "location": data.location,
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
        result = supabase.table("batches").select("*").order("created_at", desc=True).execute()
        return {"status": "success", "batches": result.data, "count": len(result.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "PharmaChain Backend"}
