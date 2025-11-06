"""
Test if batches table exists and is accessible
"""
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("=" * 60)
print("Testing Batches Table")
print("=" * 60)

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Test batches table
    print("\n📦 Testing batches table...")
    try:
        result = supabase.table("batches").select("*").limit(1).execute()
        print(f"✅ batches table exists! Records: {len(result.data)}")
        
        if result.data:
            print("\nSample record:")
            for key, value in result.data[0].items():
                print(f"  {key}: {value}")
    except Exception as e:
        print(f"❌ batches table error: {str(e)}")
        print("\n⚠️  You need to create the batches table in Supabase!")
        print("\nGo to Supabase Dashboard → SQL Editor and run:")
        print("(See create_batches_table.sql file)")
    
    print("\n" + "=" * 60)
    
except Exception as e:
    print(f"❌ Connection failed: {str(e)}")
