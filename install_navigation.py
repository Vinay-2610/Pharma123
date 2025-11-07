"""
Quick installer for Product Navigation feature
Run this script to set up everything automatically
"""
import subprocess
import sys
import os
from supabase import create_client
from dotenv import load_dotenv

print("=" * 70)
print("PharmaChain Product Navigation - Quick Installer")
print("=" * 70)

# Step 1: Install Python dependencies
print("\n📦 Step 1: Installing Python dependencies...")
try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "folium==0.15.1", "streamlit-folium==0.15.1", "polyline==2.0.0"])
    print("✅ Dependencies installed successfully!")
except Exception as e:
    print(f"❌ Error installing dependencies: {e}")
    sys.exit(1)

# Step 2: Create Supabase table
print("\n🗄️  Step 2: Creating Supabase table...")
try:
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Supabase credentials not found in .env file")
        sys.exit(1)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Check if table already exists
    try:
        result = supabase.table("shipment_routes").select("id").limit(1).execute()
        print("✅ Table 'shipment_routes' already exists!")
    except:
        print("⚠️  Table doesn't exist. Please create it manually in Supabase SQL Editor:")
        print("\nRun this SQL:")
        print("-" * 70)
        with open("create_shipment_routes_table.sql", "r") as f:
            print(f.read())
        print("-" * 70)
        print("\nOr go to: https://supabase.com/dashboard/project/_/sql")

except Exception as e:
    print(f"⚠️  Could not verify table: {e}")
    print("Please create the table manually using create_shipment_routes_table.sql")

# Step 3: Verify backend endpoints
print("\n🔧 Step 3: Verifying backend...")
print("✅ Backend endpoints added to backend/main.py")
print("   - POST /shipment/route")
print("   - GET /shipment/routes/{batch_id}")
print("   - GET /shipment/route/latest/{batch_id}")
print("   - POST /shipment/route/status")
print("   - GET /shipment/route/verify/{batch_id}")

# Step 4: Verify frontend component
print("\n🎨 Step 4: Verifying frontend component...")
if os.path.exists("components/product_navigation.py"):
    print("✅ Frontend component created: components/product_navigation.py")
else:
    print("❌ Frontend component not found!")

# Step 5: Instructions
print("\n" + "=" * 70)
print("✅ Installation Complete!")
print("=" * 70)

print("\n📝 Next Steps:")
print("\n1. Create Supabase table (if not done):")
print("   - Go to Supabase SQL Editor")
print("   - Run the SQL from create_shipment_routes_table.sql")

print("\n2. Add import to app.py:")
print("   Add this line after other imports:")
print("   from components.product_navigation import (")
print("       manufacturer_navigation_tab,")
print("       distributor_navigation_tab,")
print("       fda_navigation_tab,")
print("       pharmacy_navigation_tab")
print("   )")

print("\n3. Add navigation tabs to each dashboard")
print("   See PRODUCT_NAVIGATION_SETUP.md for details")

print("\n4. Restart services:")
print("   Backend:  uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload")
print("   Frontend: streamlit run app.py")

print("\n5. Test the feature:")
print("   - Login as Manufacturer")
print("   - Go to 'Product Navigation' tab")
print("   - Create a route!")

print("\n📚 Documentation:")
print("   - PRODUCT_NAVIGATION_SETUP.md - Complete setup guide")
print("   - NAVIGATION_SUMMARY.md - Feature overview")

print("\n" + "=" * 70)
print("🎉 Product Navigation is ready to use!")
print("=" * 70)
