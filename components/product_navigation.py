"""
Product Navigation Component
Handles route visualization and management for pharmaceutical batches
"""
import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import polyline
from datetime import datetime

BACKEND_URL = "http://localhost:8000"

def decode_polyline(encoded_polyline):
    """Decode Google Maps polyline to list of coordinates"""
    try:
        return polyline.decode(encoded_polyline)
    except:
        return []

def create_route_map(routes_data, center_lat=None, center_lng=None):
    """
    Create a Folium map with route visualization
    """
    # Determine map center
    if center_lat and center_lng:
        map_center = [center_lat, center_lng]
    elif routes_data and len(routes_data) > 0:
        # Use first route's starting point
        map_center = [routes_data[0].get("from_lat", 20.5937), routes_data[0].get("from_lng", 78.9629)]
    else:
        # Default to India center
        map_center = [20.5937, 78.9629]
    
    # Create map
    m = folium.Map(location=map_center, zoom_start=6)
    
    # Colors for different route segments
    colors = ['blue', 'green', 'red', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen']
    
    for idx, route in enumerate(routes_data):
        color = colors[idx % len(colors)]
        
        # Add start marker
        folium.Marker(
            location=[route["from_lat"], route["from_lng"]],
            popup=f"<b>From:</b> {route['from_address']}<br><b>Time:</b> {route['created_at'][:19]}",
            tooltip=f"Start: {route['from_address'][:30]}...",
            icon=folium.Icon(color='green' if idx == 0 else 'lightgray', icon='play', prefix='fa')
        ).add_to(m)
        
        # Add end marker
        is_last = (idx == len(routes_data) - 1)
        folium.Marker(
            location=[route["to_lat"], route["to_lng"]],
            popup=f"<b>To:</b> {route['to_address']}<br><b>Distance:</b> {route['distance']}<br><b>Duration:</b> {route['duration']}",
            tooltip=f"End: {route['to_address'][:30]}...",
            icon=folium.Icon(color='blue' if is_last else 'gray', icon='stop', prefix='fa')
        ).add_to(m)
        
        # Decode and draw polyline
        if route.get("polyline"):
            coordinates = decode_polyline(route["polyline"])
            if coordinates:
                folium.PolyLine(
                    locations=coordinates,
                    color=color,
                    weight=4,
                    opacity=0.8,
                    popup=f"Route {idx+1}: {route['distance']} - {route['duration']}"
                ).add_to(m)
    
    return m

def manufacturer_navigation_tab(user_email, batch_ids):
    """
    Product Navigation tab for Manufacturer Dashboard
    """
    st.markdown("### 📦 Product Navigation - Set Shipment Route")
    
    if not batch_ids:
        st.info("Create a batch first to set up navigation routes.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_batch = st.selectbox("Select Batch", batch_ids, key="mfg_nav_batch")
    
    with col2:
        # Check if route already exists
        try:
            response = requests.get(f"{BACKEND_URL}/shipment/route/latest/{selected_batch}", timeout=5)
            if response.status_code == 200:
                latest_route = response.json().get("route")
                if latest_route:
                    st.info(f"📍 Last destination: {latest_route['to_address'][:50]}...")
                else:
                    st.info("🆕 No route set yet")
        except:
            pass
    
    st.markdown("---")
    
    with st.form("manufacturer_route_form"):
        st.markdown("#### Set New Route")
        
        # Two-way method for From Address
        st.markdown("**📍 From Address (Starting Point)**")
        address_method = st.radio(
            "Choose method:",
            ["🌍 Auto-detect (Current Location)", "✍️ Enter Manually"],
            index=0,
            horizontal=True,
            help="Select how to set the starting location",
            key="address_method_radio"
        )
        
        use_auto_detect = (address_method == "🌍 Auto-detect (Current Location)")
        
        # Always show the manual input field, but with different styling
        if use_auto_detect:
            st.success("✅ From Address will be auto-detected using your current location")
            # Show disabled input to indicate auto-detect is active
            from_address_manual = st.text_input(
                "Or Enter From Address Manually (Optional - will override auto-detect)",
                placeholder="Leave empty to use auto-detect",
                help="Leave empty to use auto-detected location, or enter address to override",
                key="from_address_input"
            )
        else:
            # Show enabled input for manual entry
            from_address_manual = st.text_input(
                "Enter From Address* (Required)",
                placeholder="e.g., Manufacturing Plant, Chennai, Tamil Nadu, India",
                help="Enter the complete starting location address",
                key="from_address_input_manual"
            )
        
        st.markdown("---")
        
        # To Address
        st.markdown("**📍 To Address (Destination)**")
        to_address = st.text_input(
            "Enter To Address*",
            placeholder="e.g., Distributor Warehouse, Bengaluru, Karnataka, India",
            help="Enter the complete destination address",
            key="to_address_input"
        )
        
        st.markdown("---")
        submit = st.form_submit_button("🚀 Generate Route", use_container_width=True, type="primary")
        
        if submit:
            if not to_address:
                st.error("Please enter a destination address")
            elif not use_auto_detect and not from_address_manual:
                st.error("Please enter a starting address when using manual mode")
            else:
                with st.spinner("Calculating route..."):
                    try:
                        # Determine from_address
                        # If manual address is provided, use it (even if auto-detect is selected)
                        if from_address_manual and from_address_manual.strip():
                            from_address = from_address_manual.strip()
                            st.info(f"Using manually entered address: {from_address}")
                        elif use_auto_detect:
                            # Get current location
                            import os
                            from dotenv import load_dotenv
                            load_dotenv()
                            GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
                            
                            if GOOGLE_API_KEY:
                                # Get coordinates with increased timeout
                                try:
                                    geo_response = requests.post(
                                        f"https://www.googleapis.com/geolocation/v1/geolocate?key={GOOGLE_API_KEY}",
                                        json={},
                                        timeout=15
                                    )
                                    
                                    if geo_response.status_code == 200:
                                        geo_data = geo_response.json()
                                        if "location" in geo_data:
                                            lat = geo_data["location"]["lat"]
                                            lng = geo_data["location"]["lng"]
                                            
                                            # Get address from coordinates
                                            try:
                                                geocode_response = requests.get(
                                                    f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={GOOGLE_API_KEY}",
                                                    timeout=15
                                                )
                                            except requests.exceptions.Timeout:
                                                st.warning("Geocoding timed out. Using coordinates only.")
                                                from_address = f"{lat},{lng}"
                                                geocode_response = None
                                        else:
                                            st.error("Could not get location from Geolocation API")
                                            from_address = "Auto-Detected"
                                    else:
                                        st.error(f"Geolocation API error: {geo_response.status_code}")
                                        from_address = "Auto-Detected"
                                except requests.exceptions.Timeout:
                                    st.error("⏱️ Location detection timed out. Please uncheck 'Auto-detect' and enter address manually.")
                                    from_address = None
                                    geo_response = None
                                except Exception as geo_error:
                                    st.error(f"Location detection error: {str(geo_error)}")
                                    from_address = None
                                    geo_response = None
                                
                                # Only proceed if we have geo_response
                                if geo_response and geo_response.status_code == 200:
                                    if geocode_response and geocode_response.status_code == 200:
                                        geocode_data = geocode_response.json()
                                        if geocode_data.get("results"):
                                            from_address = geocode_data["results"][0]["formatted_address"]
                                        else:
                                            from_address = f"{lat},{lng}"
                                    else:
                                        from_address = f"{lat},{lng}"
                                else:
                                    # Auto-detect failed
                                    if from_address is None:
                                        st.error("Auto-detection failed. Please uncheck 'Auto-detect' and enter address manually.")
                                from_address = None
                        else:
                            # Use manual address
                            from_address = from_address_manual
                        
                        # Only create route if we have a from_address
                        if not from_address:
                            st.error("Could not determine starting address. Please try again or enter manually.")
                        else:
                            # Create route
                            route_data = {
                                "batch_id": selected_batch,
                                "from_address": from_address,
                                "to_address": to_address,
                                "updated_by": user_email
                            }
                            
                            response = requests.post(
                                f"{BACKEND_URL}/shipment/route",
                                json=route_data,
                                timeout=15
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                route_details = result.get("route_details", {})
                                
                                st.success(f"✅ Route created successfully!")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Distance", route_details.get("distance", "N/A"))
                                with col2:
                                    st.metric("Duration", route_details.get("duration", "N/A"))
                                
                                st.info(f"📍 From: {route_details.get('from', 'N/A')}")
                                st.info(f"📍 To: {route_details.get('to', 'N/A')}")
                                
                                st.rerun()
                            else:
                                st.error(f"Failed to create route: {response.text}")
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    # Display existing routes
    st.markdown("---")
    st.markdown("### 🗺️ Current Route")
    
    try:
        response = requests.get(f"{BACKEND_URL}/shipment/routes/{selected_batch}", timeout=5)
        if response.status_code == 200:
            routes_data = response.json().get("routes", [])
            
            if routes_data:
                # Show map
                route_map = create_route_map(routes_data)
                st_folium(route_map, width=700, height=500)
                
                # Show route details
                st.markdown("#### Route History")
                for idx, route in enumerate(routes_data):
                    with st.expander(f"Route {idx+1}: {route['from_address'][:40]}... → {route['to_address'][:40]}...", expanded=(idx == len(routes_data)-1)):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Distance:** {route['distance']}")
                        with col2:
                            st.write(f"**Duration:** {route['duration']}")
                        with col3:
                            st.write(f"**Status:** {route['status'].upper()}")
                        
                        st.write(f"**From:** {route['from_address']}")
                        st.write(f"**To:** {route['to_address']}")
                        st.write(f"**Updated:** {route['created_at'][:19]}")
                        st.write(f"**By:** {route['updated_by']}")
            else:
                st.info("No routes created yet. Use the form above to create the first route.")
    except Exception as e:
        st.error(f"Error loading routes: {str(e)}")

def distributor_navigation_tab(user_email, batch_ids):
    """
    Product Navigation tab for Distributor Dashboard
    """
    st.markdown("### 🚚 Product Navigation - Update Shipment Route")
    
    if not batch_ids:
        st.info("No batches available.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_batch = st.selectbox("Select Batch", batch_ids, key="dist_nav_batch")
    
    with col2:
        # Get latest route
        try:
            response = requests.get(f"{BACKEND_URL}/shipment/route/latest/{selected_batch}", timeout=5)
            if response.status_code == 200:
                latest_route = response.json().get("route")
                if latest_route:
                    st.success(f"📍 Current location: {latest_route['to_address'][:50]}...")
                else:
                    st.warning("⚠️ No route set yet")
        except:
            pass
    
    st.markdown("---")
    
    with st.form("distributor_route_form"):
        st.markdown("#### Update Route to Next Destination")
        
        # Get last destination as new "From"
        last_destination = None
        try:
            response = requests.get(f"{BACKEND_URL}/shipment/route/latest/{selected_batch}", timeout=5)
            if response.status_code == 200:
                latest_route = response.json().get("route")
                if latest_route:
                    last_destination = latest_route['to_address']
        except:
            pass
        
        # Two-way method for From Address
        st.markdown("**📍 From Address (Starting Point)**")
        
        if last_destination:
            address_method = st.radio(
                "Choose method:",
                ["📦 Use Last Destination", "✍️ Enter Manually"],
                index=0,
                horizontal=True,
                help="Select how to set the starting location"
            )
            
            use_last_destination = (address_method == "📦 Use Last Destination")
            
            if use_last_destination:
                st.success(f"✅ From Address: {last_destination}")
                from_address_manual = None
            else:
                from_address_manual = st.text_input(
                    "Enter From Address*",
                    placeholder="e.g., Current Warehouse, Bengaluru, Karnataka, India",
                    help="Enter the complete starting location address",
                    key="dist_from_address_input"
                )
        else:
            st.info("ℹ️ No previous route found. Please enter starting address manually.")
            from_address_manual = st.text_input(
                "Enter From Address*",
                placeholder="e.g., Current Warehouse, Bengaluru, Karnataka, India",
                help="Enter the complete starting location address",
                key="dist_from_address_input_2"
            )
            use_last_destination = False
        
        st.markdown("---")
        
        # To Address
        st.markdown("**📍 To Address (Destination)**")
        to_address = st.text_input(
            "Enter To Address*",
            placeholder="e.g., FDA Testing Facility, Chennai, Tamil Nadu, India",
            help="Enter the complete destination address",
            key="dist_to_address_input"
        )
        
        st.markdown("---")
        submit = st.form_submit_button("🚀 Update Route", use_container_width=True, type="primary")
        
        if submit:
            if not to_address:
                st.error("Please enter a destination address")
            elif not use_last_destination and not from_address_manual:
                st.error("Please enter a starting address")
            else:
                with st.spinner("Calculating route..."):
                    try:
                        # Determine from_address based on user choice
                        if use_last_destination and last_destination:
                            from_address = last_destination
                        elif from_address_manual:
                            from_address = from_address_manual
                        else:
                            st.error("Could not determine starting address")
                            from_address = None
                        
                        if not from_address:
                            st.error("Please provide a valid starting address")
                        else:
                            # Create route
                            route_data = {
                                "batch_id": selected_batch,
                                "from_address": from_address,
                                "to_address": to_address,
                                "updated_by": user_email
                            }
                            
                            response = requests.post(
                                f"{BACKEND_URL}/shipment/route",
                                json=route_data,
                                timeout=15
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                route_details = result.get("route_details", {})
                                
                                st.success(f"✅ Route updated successfully!")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Distance", route_details.get("distance", "N/A"))
                                with col2:
                                    st.metric("Duration", route_details.get("duration", "N/A"))
                                
                                st.rerun()
                            else:
                                st.error(f"Failed to update route: {response.text}")
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    # Display existing routes (same as manufacturer)
    st.markdown("---")
    st.markdown("### 🗺️ Complete Journey")
    
    try:
        response = requests.get(f"{BACKEND_URL}/shipment/routes/{selected_batch}", timeout=5)
        if response.status_code == 200:
            routes_data = response.json().get("routes", [])
            
            if routes_data:
                # Show map
                route_map = create_route_map(routes_data)
                st_folium(route_map, width=700, height=500)
                
                # Show route details
                st.markdown("#### Route History")
                for idx, route in enumerate(routes_data):
                    with st.expander(f"Leg {idx+1}: {route['from_address'][:40]}... → {route['to_address'][:40]}...", expanded=(idx == len(routes_data)-1)):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Distance:** {route['distance']}")
                        with col2:
                            st.write(f"**Duration:** {route['duration']}")
                        with col3:
                            st.write(f"**Status:** {route['status'].upper()}")
                        
                        st.write(f"**From:** {route['from_address']}")
                        st.write(f"**To:** {route['to_address']}")
                        st.write(f"**Updated:** {route['created_at'][:19]}")
            else:
                st.info("No routes available yet.")
    except Exception as e:
        st.error(f"Error loading routes: {str(e)}")

def fda_navigation_tab(batch_ids):
    """
    Product Navigation tab for FDA Dashboard (Read-only)
    """
    st.markdown("### 🏛️ Product Navigation - Route Verification")
    
    if not batch_ids:
        st.info("No batches available.")
        return
    
    selected_batch = st.selectbox("Select Batch to Verify", batch_ids, key="fda_nav_batch")
    
    st.markdown("---")
    
    # Verify route integrity
    col1, col2 = st.columns([2, 1])
    
    with col2:
        if st.button("🔍 Verify Route Integrity", use_container_width=True):
            with st.spinner("Verifying..."):
                try:
                    response = requests.get(f"{BACKEND_URL}/shipment/route/verify/{selected_batch}", timeout=10)
                    if response.status_code == 200:
                        result = response.json()
                        
                        if result["is_valid"]:
                            st.success(f"✅ Route integrity verified - {result['total_routes']} route(s)")
                        else:
                            st.error(f"⚠️ Route integrity issues detected")
                            for issue in result.get("issues", []):
                                st.warning(f"• {issue}")
                        
                        # Show summary
                        st.markdown("#### Route Summary")
                        for idx, route_sum in enumerate(result.get("routes_summary", [])):
                            st.write(f"**Leg {idx+1}:** {route_sum['from'][:40]}... → {route_sum['to'][:40]}...")
                            st.write(f"  Distance: {route_sum['distance']} | Duration: {route_sum['duration']}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Display routes (read-only)
    st.markdown("### 🗺️ Complete Journey Map")
    
    try:
        response = requests.get(f"{BACKEND_URL}/shipment/routes/{selected_batch}", timeout=5)
        if response.status_code == 200:
            routes_data = response.json().get("routes", [])
            
            if routes_data:
                # Show map
                route_map = create_route_map(routes_data)
                st_folium(route_map, width=700, height=500)
                
                # Show route details in table format
                st.markdown("#### Route Details")
                
                import pandas as pd
                df = pd.DataFrame([
                    {
                        "Leg": idx+1,
                        "From": r["from_address"][:50],
                        "To": r["to_address"][:50],
                        "Distance": r["distance"],
                        "Duration": r["duration"],
                        "Status": r["status"].upper(),
                        "Updated": r["created_at"][:19]
                    }
                    for idx, r in enumerate(routes_data)
                ])
                
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No route data available for this batch.")
    except Exception as e:
        st.error(f"Error loading routes: {str(e)}")

def pharmacy_navigation_tab(batch_ids):
    """
    Product Navigation tab for Pharmacy Dashboard
    Shows complete journey timeline
    """
    st.markdown("### 💊 Product Navigation - Complete Journey Timeline")
    
    if not batch_ids:
        st.info("No batches available.")
        return
    
    selected_batch = st.selectbox("Select Batch", batch_ids, key="pharm_nav_batch")
    
    st.markdown("---")
    
    try:
        response = requests.get(f"{BACKEND_URL}/shipment/routes/{selected_batch}", timeout=5)
        if response.status_code == 200:
            routes_data = response.json().get("routes", [])
            
            if routes_data:
                # Show complete journey map
                st.markdown("### 🗺️ Complete Supply Chain Journey")
                route_map = create_route_map(routes_data)
                st_folium(route_map, width=700, height=600)
                
                # Show timeline
                st.markdown("### 📅 Journey Timeline")
                
                for idx, route in enumerate(routes_data):
                    stage_name = ["Manufacturer", "Distributor", "FDA", "Pharmacy"][min(idx, 3)]
                    
                    with st.expander(f"Stage {idx+1}: {stage_name} - {route['created_at'][:19]}", expanded=True):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**From:** {route['from_address']}")
                            st.write(f"**To:** {route['to_address']}")
                            st.write(f"**Updated by:** {route['updated_by']}")
                        
                        with col2:
                            st.metric("Distance", route['distance'])
                            st.metric("Duration", route['duration'])
                        
                        # Status badge
                        status_color = {"in_transit": "🟡", "delivered": "🟢", "cancelled": "🔴"}
                        st.write(f"**Status:** {status_color.get(route['status'], '⚪')} {route['status'].upper()}")
                
                # Summary metrics
                st.markdown("---")
                st.markdown("### 📊 Journey Summary")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Legs", len(routes_data))
                
                with col2:
                    # Calculate total distance (rough estimate)
                    total_km = sum([float(r['distance'].replace(' km', '').replace(',', '')) for r in routes_data if 'km' in r['distance']])
                    st.metric("Total Distance", f"{total_km:.1f} km")
                
                with col3:
                    # Show journey duration
                    start_time = routes_data[0]['created_at']
                    end_time = routes_data[-1]['created_at']
                    st.write(f"**Journey Duration:**")
                    st.write(f"{start_time[:10]} to {end_time[:10]}")
            else:
                st.info("No route data available for this batch yet.")
    except Exception as e:
        st.error(f"Error loading routes: {str(e)}")
