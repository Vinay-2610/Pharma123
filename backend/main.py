from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import hashlib
import json
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

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "PharmaChain Backend"}
