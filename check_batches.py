"""Check recent batches in database"""
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("=" * 70)
print("Recent Batches in Database")
print("=" * 70)

result = supabase.table('batches').select('*').order('created_at', desc=True).limit(10).execute()

print(f"\nTotal batches: {len(result.data)}\n")

for batch in result.data:
    print(f"Batch ID: {batch['batch_id']}")
    print(f"  Status: {batch['status']}")
    print(f"  Product: {batch.get('product_name', 'N/A')}")
    print(f"  Created: {batch.get('created_at', 'N/A')[:19]}")
    print(f"  FDA Approved: {batch.get('fda_approved_by', 'Not yet')}")
    print()

print("=" * 70)
print("Approved batches:")
approved = [b for b in result.data if b['status'] == 'approved']
print(f"Count: {len(approved)}")
for b in approved:
    print(f"  - {b['batch_id']}: {b.get('product_name', 'N/A')}")
print("=" * 70)
