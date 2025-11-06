"""
Quick script to manually confirm users in Supabase
Run this if you can't disable email confirmation in Supabase settings
"""
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Note: This requires the service_role key, not the anon key
# You can find it in Supabase Dashboard -> Settings -> API -> service_role key

print("=" * 60)
print("Supabase User Confirmation Helper")
print("=" * 60)
print("\nTo confirm users, you need to:")
print("1. Go to Supabase Dashboard -> Authentication -> Users")
print("2. Click on each user")
print("3. Click 'Confirm User' button")
print("\nOR")
print("\n1. Go to Authentication -> Providers -> Email")
print("2. Disable 'Confirm email' toggle")
print("3. Save settings")
print("4. Try logging in again")
print("\n" + "=" * 60)
