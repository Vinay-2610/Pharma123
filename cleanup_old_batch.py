"""
Script to delete the old batch with incorrect location format
Run this to clean up the test batch that shows "Enable Geocoding API"
"""
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 70)
print("Cleaning Up Old Batches with Incorrect Location Format")
print("=" * 70)

# Find batches with old location format
print("\n1. Finding batches with 'Enable Geocoding API' in location...")
result = supabase.table("batches").select("*").execute()

old_batches = [b for b in result.data if "Enable Geocoding API" in b.get("initial_location", "")]

if not old_batches:
    print("✅ No old batches found! All batches have proper location format.")
else:
    print(f"Found {len(old_batches)} batch(es) with old location format:")
    for batch in old_batches:
        print(f"  - {batch['batch_id']}: {batch['initial_location']}")
    
    print("\n2. Deleting old batches...")
    for batch in old_batches:
        try:
            supabase.table("batches").delete().eq("batch_id", batch['batch_id']).execute()
            print(f"  ✅ Deleted: {batch['batch_id']}")
        except Exception as e:
            print(f"  ❌ Error deleting {batch['batch_id']}: {e}")
    
    print(f"\n✅ Cleanup complete! Deleted {len(old_batches)} old batch(es).")

print("\n" + "=" * 70)
print("Now create a new batch in the Manufacturer Dashboard")
print("It will have the proper location format!")
print("=" * 70)
