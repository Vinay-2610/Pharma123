"""
Verify all tables exist and check their status
"""
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("=" * 70)
print("PharmaChain Database Tables Verification")
print("=" * 70)

tables_to_check = [
    ("iot_data", "IoT sensor readings"),
    ("alerts", "Temperature alerts"),
    ("batches", "Batch information"),
    ("user_profiles", "User accounts"),
    ("ledger", "Blockchain ledger"),
    ("alerts_log", "Real-time alerts"),
    ("audit_logs", "Audit trail"),
    ("shipments", "Shipment tracking"),
    ("signatures", "Multi-party signatures (optional)"),
    ("vehicle_telemetry", "Vehicle health (optional)")
]

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("\n✅ Connected to Supabase\n")
    
    for table_name, description in tables_to_check:
        try:
            result = supabase.table(table_name).select("*").limit(1).execute()
            count_result = supabase.table(table_name).select("id", count="exact").execute()
            count = count_result.count if hasattr(count_result, 'count') else len(result.data)
            
            status = "✅" if count > 0 else "⚪"
            print(f"{status} {table_name:20} - {description:40} ({count} records)")
            
        except Exception as e:
            if "PGRST205" in str(e) or "Could not find" in str(e):
                print(f"❌ {table_name:20} - Table does not exist")
            else:
                print(f"⚠️  {table_name:20} - Error: {str(e)[:50]}")
    
    print("\n" + "=" * 70)
    print("Legend:")
    print("✅ = Table exists with data")
    print("⚪ = Table exists but empty (normal for new tables)")
    print("❌ = Table does not exist (needs to be created)")
    print("=" * 70)
    
    print("\n📝 Notes:")
    print("- 'signatures' and 'vehicle_telemetry' are optional and can be empty")
    print("- 'ledger' will populate when IoT data is received")
    print("- 'alerts_log' will populate when temperature alerts occur")
    print("- 'audit_logs' will populate when users perform actions")
    
except Exception as e:
    print(f"\n❌ Connection failed: {str(e)}")
