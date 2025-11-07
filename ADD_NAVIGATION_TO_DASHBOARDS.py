"""
This file contains the exact code snippets to add Product Navigation tabs
to each dashboard in app.py

Copy and paste these into the appropriate dashboard functions
"""

# ============================================================================
# MANUFACTURER DASHBOARD - Add this at the END of manufacturer_dashboard()
# ============================================================================

MANUFACTURER_NAVIGATION_CODE = '''
    # Product Navigation Tab
    st.markdown("---")
    st.markdown("## 🗺️ Product Navigation")
    
    if NAVIGATION_AVAILABLE:
        # Get manufacturer's batches
        try:
            batches_data = fetch_data("/batch/all")
            batch_ids = []
            if batches_data and batches_data.get("batches"):
                manufacturer_batches = [b for b in batches_data["batches"] 
                                       if b.get("manufacturer_email") == st.session_state.user_email]
                batch_ids = [b["batch_id"] for b in manufacturer_batches]
            
            if batch_ids:
                manufacturer_navigation_tab(st.session_state.user_email, batch_ids)
            else:
                st.info("Create a batch first to set up navigation routes.")
        except Exception as e:
            st.error(f"Error loading navigation: {str(e)}")
    else:
        st.warning("Product Navigation feature not available. Please install dependencies: pip install folium streamlit-folium polyline")
'''

# ============================================================================
# DISTRIBUTOR DASHBOARD - Add this at the END of distributor_dashboard()
# ============================================================================

DISTRIBUTOR_NAVIGATION_CODE = '''
    # Product Navigation Tab
    st.markdown("---")
    st.markdown("## 🗺️ Product Navigation")
    
    if NAVIGATION_AVAILABLE:
        # Get approved batches
        try:
            approved_batches_data = fetch_data("/batch/all")
            batch_ids = []
            if approved_batches_data and approved_batches_data.get("batches"):
                approved_batches = [b for b in approved_batches_data["batches"] 
                                   if b["status"] == "approved"]
                batch_ids = [b["batch_id"] for b in approved_batches]
            
            if batch_ids:
                distributor_navigation_tab(st.session_state.user_email, batch_ids)
            else:
                st.info("No approved batches available for navigation.")
        except Exception as e:
            st.error(f"Error loading navigation: {str(e)}")
    else:
        st.warning("Product Navigation feature not available. Please install dependencies: pip install folium streamlit-folium polyline")
'''

# ============================================================================
# FDA DASHBOARD - Add this as a NEW TAB in the existing tabs
# ============================================================================

FDA_NAVIGATION_CODE = '''
    # Add "🗺️ Product Navigation" to the existing tabs
    # Change this line:
    # tab1, tab2, tab3, tab4 = st.tabs(["⚠️ Active Alerts", "🔐 Blockchain Verification", "🔗 Blockchain Explorer", "📋 Audit Logs"])
    # To this:
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "⚠️ Active Alerts", 
        "🔐 Blockchain Verification", 
        "🔗 Blockchain Explorer", 
        "📋 Audit Logs",
        "🗺️ Product Navigation"
    ])
    
    # Then add this new tab5 section after tab4:
    with tab5:
        if NAVIGATION_AVAILABLE:
            # Get all batches
            try:
                all_batches_data = fetch_data("/batch/all")
                batch_ids = []
                if all_batches_data and all_batches_data.get("batches"):
                    batch_ids = [b["batch_id"] for b in all_batches_data["batches"]]
                
                if batch_ids:
                    fda_navigation_tab(batch_ids)
                else:
                    st.info("No batches available for navigation.")
            except Exception as e:
                st.error(f"Error loading navigation: {str(e)}")
        else:
            st.warning("Product Navigation feature not available. Please install dependencies: pip install folium streamlit-folium polyline")
'''

# ============================================================================
# PHARMACY DASHBOARD - Add this at the END of pharmacy_dashboard()
# ============================================================================

PHARMACY_NAVIGATION_CODE = '''
    # Product Navigation Tab
    st.markdown("---")
    st.markdown("## 🗺️ Product Navigation - Complete Journey")
    
    if NAVIGATION_AVAILABLE:
        # Get approved batches
        try:
            approved_batches_data = fetch_data("/batch/all")
            batch_ids = []
            if approved_batches_data and approved_batches_data.get("batches"):
                approved_batches = [b for b in approved_batches_data["batches"] 
                                   if b["status"] == "approved"]
                batch_ids = [b["batch_id"] for b in approved_batches]
            
            if batch_ids:
                pharmacy_navigation_tab(batch_ids)
            else:
                st.info("No approved batches available for navigation.")
        except Exception as e:
            st.error(f"Error loading navigation: {str(e)}")
    else:
        st.warning("Product Navigation feature not available. Please install dependencies: pip install folium streamlit-folium polyline")
'''

# ============================================================================
# INSTRUCTIONS
# ============================================================================

print("=" * 80)
print("PRODUCT NAVIGATION - INTEGRATION INSTRUCTIONS")
print("=" * 80)
print()
print("1. The import statement has already been added to app.py")
print()
print("2. Add the navigation code to each dashboard:")
print()
print("   MANUFACTURER DASHBOARD:")
print("   - Find the manufacturer_dashboard() function")
print("   - Scroll to the END of the function (before the next def)")
print("   - Copy and paste MANUFACTURER_NAVIGATION_CODE")
print()
print("   DISTRIBUTOR DASHBOARD:")
print("   - Find the distributor_dashboard() function")
print("   - Scroll to the END of the function")
print("   - Copy and paste DISTRIBUTOR_NAVIGATION_CODE")
print()
print("   FDA DASHBOARD:")
print("   - Find the fda_dashboard() function")
print("   - Find the line with st.tabs([...])")
print("   - Add '🗺️ Product Navigation' to the tabs list")
print("   - Add the tab5 section with FDA_NAVIGATION_CODE")
print()
print("   PHARMACY DASHBOARD:")
print("   - Find the pharmacy_dashboard() function")
print("   - Scroll to the END of the function")
print("   - Copy and paste PHARMACY_NAVIGATION_CODE")
print()
print("3. Install dependencies:")
print("   pip install folium streamlit-folium polyline")
print()
print("4. Create Supabase table:")
print("   Run the SQL from create_shipment_routes_table.sql")
print()
print("5. Restart services:")
print("   Backend:  uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload")
print("   Frontend: streamlit run app.py")
print()
print("=" * 80)
print("The code snippets are stored in this file for easy copy-paste!")
print("=" * 80)
