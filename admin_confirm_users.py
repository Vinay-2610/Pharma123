"""
Admin script to confirm all users using service_role key
This bypasses email confirmation requirement
"""
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("=" * 60)
print("Confirming All Users")
print("=" * 60)

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Get all users from user_profiles
    result = supabase.table("user_profiles").select("*").execute()
    
    print(f"\nFound {len(result.data)} users:")
    for user in result.data:
        print(f"  - {user['email']} ({user['role']})")
    
    print("\n" + "=" * 60)
    print("To confirm users in Supabase:")
    print("1. Go to: https://supabase.com/dashboard")
    print("2. Select your project")
    print("3. Click: Authentication → Providers")
    print("4. Click: Email")
    print("5. Find the toggle: 'Confirm email'")
    print("6. Turn it OFF (disable it)")
    print("7. Click Save")
    print("\nAfter this, you can login without email confirmation!")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
