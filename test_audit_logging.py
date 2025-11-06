"""
Test audit logging functionality
"""
import requests
import time

BACKEND_URL = "http://localhost:8000"

print("=" * 70)
print("Testing Audit Logging")
print("=" * 70)

# Test 1: Create a test audit log
print("\n1. Creating test audit log...")
try:
    response = requests.post(f"{BACKEND_URL}/audit/log", 
                           json={
                               "user_email": "test@pharmachain.com",
                               "role": "FDA",
                               "action": "Test Action",
                               "batch_id": "BATCH-TEST-001",
                               "details": {"test": "This is a test audit log"}
                           },
                           timeout=10)
    
    if response.status_code == 200:
        print("✅ Test audit log created successfully")
    else:
        print(f"❌ Failed: {response.text}")
except Exception as e:
    print(f"❌ Error: {str(e)}")

time.sleep(1)

# Test 2: Retrieve audit logs
print("\n2. Retrieving audit logs...")
try:
    response = requests.get(f"{BACKEND_URL}/audit/logs?limit=10", timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        logs = result.get("logs", [])
        print(f"✅ Retrieved {len(logs)} audit logs")
        
        if logs:
            print("\nMost recent audit log:")
            latest = logs[0]
            print(f"  User: {latest['user_email']}")
            print(f"  Role: {latest['role']}")
            print(f"  Action: {latest['action']}")
            print(f"  Batch: {latest.get('batch_id', 'N/A')}")
            print(f"  Time: {latest['timestamp']}")
    else:
        print(f"❌ Failed: {response.text}")
except Exception as e:
    print(f"❌ Error: {str(e)}")

print("\n" + "=" * 70)
print("Now audit logs will be created automatically when:")
print("  - Users log in")
print("  - Batches are created")
print("  - FDA approves/rejects batches")
print("  - Users view blockchain explorer")
print("  - Users verify blockchain hashes")
print("=" * 70)
