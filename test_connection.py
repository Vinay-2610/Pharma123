"""
Test Supabase connection and check if tables exist
"""
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("=" * 60)
print("Testing Supabase Connection")
print("=" * 60)

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Connection successful!")
    
    # Test iot_data table
    print("\n📊 Testing iot_data table...")
    try:
        result = supabase.table("iot_data").select("*").limit(1).execute()
        print(f"✅ iot_data table exists! Records: {len(result.data)}")
    except Exception as e:
        print(f"❌ iot_data table error: {str(e)}")
    
    # Test alerts table
    print("\n⚠️  Testing alerts table...")
    try:
        result = supabase.table("alerts").select("*").limit(1).execute()
        print(f"✅ alerts table exists! Records: {len(result.data)}")
    except Exception as e:
        print(f"❌ alerts table error: {str(e)}")
    
    # Test user_profiles table
    print("\n👤 Testing user_profiles table...")
    try:
        result = supabase.table("user_profiles").select("*").limit(5).execute()
        print(f"✅ user_profiles table exists! Users: {len(result.data)}")
        for user in result.data:
            print(f"   - {user['email']} ({user['role']})")
    except Exception as e:
        print(f"❌ user_profiles table error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("If you see errors above, you need to create the tables.")
    print("Run the SQL script from DATABASE_SETUP.md in Supabase SQL Editor")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Connection failed: {str(e)}")
