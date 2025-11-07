import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import time
from streamlit_autorefresh import st_autorefresh

# Product Navigation imports
try:
    from components.product_navigation import (
        manufacturer_navigation_tab,
        distributor_navigation_tab,
        fda_navigation_tab,
        pharmacy_navigation_tab
    )
    NAVIGATION_AVAILABLE = True
except ImportError:
    NAVIGATION_AVAILABLE = False
    print("Warning: Product Navigation component not available")

# MUST BE FIRST: Set page config
st.set_page_config(
    page_title="PharmaChain - Supply Chain Monitoring",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables from .env file
load_dotenv()

BACKEND_URL = "http://localhost:8000"

if "SUPABASE_URL" not in os.environ or "SUPABASE_KEY" not in os.environ:
    st.error("⚠️ Please set SUPABASE_URL and SUPABASE_KEY environment variables")
    st.info("Add your Supabase credentials to continue using PharmaChain")
    st.stop()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Custom CSS for role-based styling
st.markdown("""
<style>
    .manufacturer-accent { border-left: 5px solid #4A90E2; padding-left: 15px; }
    .fda-accent { border-left: 5px solid #50C878; padding-left: 15px; }
    .distributor-accent { border-left: 5px solid #FF8C00; padding-left: 15px; }
    .pharmacy-accent { border-left: 5px solid #9370DB; padding-left: 15px; }
    
    .temp-normal { background-color: #d4edda; padding: 15px; border-radius: 8px; color: #155724; }
    .temp-warning { background-color: #fff3cd; padding: 15px; border-radius: 8px; color: #856404; }
    .temp-danger { background-color: #f8d7da; padding: 15px; border-radius: 8px; color: #721c24; }
    
    .metric-live {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    .activity-log {
        background-color: #2d3748;
        color: #e2e8f0;
        padding: 15px;
        border-left: 4px solid #667eea;
        margin: 8px 0;
        border-radius: 8px;
        font-size: 0.95em;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .activity-log strong {
        color: #90cdf4;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None

def login_page():
    st.title("🔐 PharmaChain Login")
    st.markdown("### Pharmaceutical Supply Chain Monitoring System")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="user@pharmachain.com")
                password = st.text_input("Password", type="password")
                
                submitted = st.form_submit_button("Login", use_container_width=True)
                
                if submitted:
                    if email and password:
                        try:
                            response = supabase.auth.sign_in_with_password({
                                "email": email,
                                "password": password
                            })
                            
                            if response.user:
                                profile_response = supabase.table("user_profiles").select("role").eq("id", response.user.id).execute()
                                
                                if not profile_response.data or len(profile_response.data) == 0:
                                    st.error("Account setup incomplete. Please create a new account with a role assigned.")
                                else:
                                    user_role = profile_response.data[0]["role"]
                                    st.session_state.authenticated = True
                                    st.session_state.user_email = email
                                    st.session_state.user_role = user_role
                                    st.session_state.user_id = response.user.id
                                    
                                    # Log login to audit trail
                                    try:
                                        requests.post(f"{BACKEND_URL}/audit/log", 
                                                    json={
                                                        "user_email": email,
                                                        "role": user_role,
                                                        "action": "User Login",
                                                        "details": {"login_time": datetime.now().isoformat()}
                                                    },
                                                    timeout=5)
                                    except:
                                        pass
                                    
                                    st.success(f"✓ Welcome back, {user_role}!")
                                    st.rerun()
                            else:
                                st.error("Invalid credentials")
                        except Exception as e:
                            error_msg = str(e)
                            if "Email not confirmed" in error_msg:
                                st.error("⚠️ Email not confirmed. Please check Supabase settings:")
                                st.info("Go to Supabase Dashboard → Authentication → Providers → Email → Disable 'Confirm email'")
                            else:
                                st.error(f"Login failed: {error_msg}")
                    else:
                        st.warning("Please enter email and password")
        
        with tab2:
            with st.form("signup_form"):
                new_email = st.text_input("Email", placeholder="newuser@pharmachain.com", key="signup_email")
                new_password = st.text_input("Password", type="password", key="signup_password")
                confirm_password = st.text_input("Confirm Password", type="password")
                new_role = st.selectbox("Select Your Role", ["Manufacturer", "FDA", "Distributor", "Pharmacy"], key="signup_role")
                
                signup_submitted = st.form_submit_button("Create Account", use_container_width=True)
                
                if signup_submitted:
                    if new_email and new_password:
                        if new_password != confirm_password:
                            st.error("Passwords do not match")
                        elif len(new_password) < 6:
                            st.error("Password must be at least 6 characters")
                        else:
                            try:
                                response = supabase.auth.sign_up({
                                    "email": new_email,
                                    "password": new_password
                                })
                                
                                if response.user:
                                    try:
                                        profile_data = {
                                            "id": response.user.id,
                                            "email": new_email,
                                            "role": new_role
                                        }
                                        supabase.table("user_profiles").insert(profile_data).execute()
                                        st.success(f"✓ Account created successfully as {new_role}! Please log in.")
                                    except Exception as profile_error:
                                        st.error(f"Account created but role assignment failed: {str(profile_error)}")
                                else:
                                    st.error("Account creation failed")
                            except Exception as e:
                                st.error(f"Sign up failed: {str(e)}")
                    else:
                        st.warning("Please fill in all fields")

def fetch_data(endpoint):
    try:
        response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

def get_temp_status(temp):
    """Determine temperature status and color"""
    if 20 <= temp <= 30:
        return "normal", "🟢", "#d4edda"
    elif (temp >= 15 and temp < 20) or (temp > 30 and temp <= 35):
        return "warning", "🟡", "#fff3cd"
    else:
        return "danger", "🔴", "#f8d7da"

def display_live_iot_metrics(role_color="#667eea"):
    """Shared component for real-time IoT metrics across all dashboards"""
    
    # Fetch latest IoT data
    iot_data = fetch_data("/iot/data?limit=100")
    alerts_data = fetch_data("/alerts?limit=20")
    
    if iot_data and iot_data.get("data"):
        df = pd.DataFrame(iot_data["data"])
        # Handle timestamp parsing with error handling
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            # Remove any rows with invalid timestamps
            df = df.dropna(subset=['timestamp'])
        except Exception as e:
            st.error(f"Error parsing timestamps: {e}")
            return None, None
        
        if df.empty:
            st.warning("⚠️ No valid IoT data available")
            return None, None
        
        df = df.sort_values('timestamp', ascending=False)
        
        latest = df.iloc[0]
        temp = latest['temperature']
        humidity = latest['humidity']
        
        temp_status, temp_icon, temp_color = get_temp_status(temp)
        
        # Live Metrics Row
        st.markdown(f"### 🌡️ Live IoT Monitoring")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {role_color} 0%, #764ba2 100%); 
                        padding: 20px; border-radius: 10px; color: white; text-align: center;">
                <h3 style="margin:0; color:white;">{temp_icon} {temp:.1f}°C</h3>
                <p style="margin:5px 0 0 0; font-size:0.9em;">Live Temperature</p>
                <small>Status: {temp_status.upper()}</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #36D1DC 0%, #5B86E5 100%); 
                        padding: 20px; border-radius: 10px; color: white; text-align: center;">
                <h3 style="margin:0; color:white;">💧 {humidity:.1f}%</h3>
                <p style="margin:5px 0 0 0; font-size:0.9em;">Live Humidity</p>
                <small>Optimal Range</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.metric("📊 Total Readings", len(df), delta=f"+{len(df)-90}")
        
        with col4:
            active_alerts = len([a for a in alerts_data.get("alerts", []) if not a.get('resolved', False)]) if alerts_data else 0
            st.metric("⚠️ Active Alerts", active_alerts, delta=None, delta_color="inverse")
        
        # Alert Box
        if temp_status == "danger":
            st.markdown(f"""
            <div class="temp-danger">
                🚨 <strong>CRITICAL ALERT:</strong> Temperature {temp:.1f}°C is outside safe range (20-30°C)!
                Immediate action required.
            </div>
            """, unsafe_allow_html=True)
        elif temp_status == "warning":
            st.markdown(f"""
            <div class="temp-warning">
                ⚠️ <strong>WARNING:</strong> Temperature {temp:.1f}°C is approaching limits. Monitor closely.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="temp-normal">
                ✅ <strong>ALL SYSTEMS NORMAL:</strong> Temperature {temp:.1f}°C is within safe range (20-30°C).
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Live Graphs
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🌡️ Real-Time Temperature Tracking")
            fig_temp = go.Figure()
            
            for batch_id in df['batch_id'].unique()[:4]:  # Show top 4 batches
                batch_df = df[df['batch_id'] == batch_id].sort_values('timestamp')
                fig_temp.add_trace(go.Scatter(
                    x=batch_df['timestamp'],
                    y=batch_df['temperature'],
                    mode='lines+markers',
                    name=batch_id,
                    line=dict(width=3),
                    marker=dict(size=8)
                ))
            
            # Safe range indicators
            fig_temp.add_hrect(y0=20, y1=30, fillcolor="green", opacity=0.1, 
                              annotation_text="Safe Range", annotation_position="top left")
            fig_temp.add_hline(y=30, line_dash="dash", line_color="red", annotation_text="Max Safe")
            fig_temp.add_hline(y=20, line_dash="dash", line_color="blue", annotation_text="Min Safe")
            
            fig_temp.update_layout(
                xaxis_title="Time",
                yaxis_title="Temperature (°C)",
                height=400,
                hovermode='x unified',
                template="plotly_white"
            )
            
            st.plotly_chart(fig_temp, use_container_width=True)
        
        with col2:
            st.subheader("💧 Real-Time Humidity Tracking")
            fig_humid = go.Figure()
            
            for batch_id in df['batch_id'].unique()[:4]:
                batch_df = df[df['batch_id'] == batch_id].sort_values('timestamp')
                fig_humid.add_trace(go.Scatter(
                    x=batch_df['timestamp'],
                    y=batch_df['humidity'],
                    mode='lines+markers',
                    name=batch_id,
                    line=dict(width=3),
                    marker=dict(size=8),
                    fill='tonexty'
                ))
            
            fig_humid.update_layout(
                xaxis_title="Time",
                yaxis_title="Humidity (%)",
                height=400,
                hovermode='x unified',
                template="plotly_white"
            )
            
            st.plotly_chart(fig_humid, use_container_width=True)
        
        # System Activity Log
        st.markdown("### 📋 System Activity Log")
        current_time = datetime.now().strftime("%H:%M:%S")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"""
            <div class="activity-log">
                <strong>[{current_time}]</strong> 🔄 New IoT data received | Temp: {temp:.1f}°C | Humidity: {humidity:.1f}%
            </div>
            """, unsafe_allow_html=True)
            
            if active_alerts > 0:
                st.markdown(f"""
                <div class="activity-log">
                    <strong>[{current_time}]</strong> ⚠️ {active_alerts} active alert(s) detected
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="activity-log">
                <strong>[{current_time}]</strong> ✅ System sync complete | {len(df)} records processed
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.info(f"🔄 Auto-refresh: 10s\n\n🕐 Updated: {current_time}")
        
        return df, latest
    
    else:
        st.warning("⚠️ Unable to fetch real-time IoT data")
        return None, None

def manufacturer_dashboard():
    st.markdown('<div class="manufacturer-accent">', unsafe_allow_html=True)
    st.title("🏭 Manufacturer Dashboard")
    st.markdown("### Real-time IoT Data & Analytics")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # FIRST: Create New Shipment Section (shown first, expanded by default)
    with st.expander("📦 Create New Shipment", expanded=True):
        st.markdown("### Register a New Pharmaceutical Batch")
        
        # Fetch latest temperature, humidity from Supabase and location from Google API
        try:
            latest_iot = supabase.table("iot_data").select("temperature, humidity, timestamp").order("timestamp", desc=True).limit(1).execute()
            if latest_iot.data and len(latest_iot.data) > 0:
                auto_temp = float(latest_iot.data[0].get('temperature', 25.0))
                auto_humidity = float(latest_iot.data[0].get('humidity', 45.0))
                last_reading_time = latest_iot.data[0].get('timestamp', datetime.now().isoformat())
            else:
                auto_temp = 25.0  # Default fallback
                auto_humidity = 45.0
                last_reading_time = datetime.now().isoformat()
            
            # Fetch fresh location from Google Geolocation + Geocoding API
            auto_location = "Location Not Available"
            auto_location_display = "Location Not Available"
            
            try:
                GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
                
                if GOOGLE_API_KEY:
                    # Step 1: Get coordinates from Geolocation API
                    try:
                        geo_response = requests.post(
                            f"https://www.googleapis.com/geolocation/v1/geolocate?key={GOOGLE_API_KEY}",
                            json={},
                            timeout=10
                        )
                        
                        if geo_response.status_code == 200:
                            geo_data = geo_response.json()
                            if "location" in geo_data:
                                lat = geo_data["location"]["lat"]
                                lng = geo_data["location"]["lng"]
                                
                                # Step 2: Convert coordinates to address using Geocoding API
                                try:
                                    geocode_response = requests.get(
                                        f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={GOOGLE_API_KEY}",
                                        timeout=10
                                    )
                                    
                                    if geocode_response.status_code == 200:
                                        geocode_data = geocode_response.json()
                                        if geocode_data.get("status") == "OK" and geocode_data.get("results"):
                                            address = geocode_data["results"][0]["formatted_address"]
                                            auto_location = f"{address} ({lat:.4f}, {lng:.4f})"
                                            auto_location_display = address
                                        else:
                                            # Geocoding failed, use coordinates only
                                            auto_location = f"Location ({lat:.4f}, {lng:.4f})"
                                            auto_location_display = f"Lat: {lat:.4f}, Lng: {lng:.4f}"
                                    else:
                                        # Geocoding API error
                                        auto_location = f"Location ({lat:.4f}, {lng:.4f})"
                                        auto_location_display = f"Lat: {lat:.4f}, Lng: {lng:.4f}"
                                except Exception as geocode_error:
                                    print(f"Geocoding error: {geocode_error}")
                                    auto_location = f"Location ({lat:.4f}, {lng:.4f})"
                                    auto_location_display = f"Lat: {lat:.4f}, Lng: {lng:.4f}"
                            else:
                                auto_location = "Location Detection Failed"
                                auto_location_display = "Location Detection Failed"
                        else:
                            print(f"Geolocation API error: {geo_response.status_code} - {geo_response.text}")
                            auto_location = "Location Detection Failed"
                            auto_location_display = "Location Detection Failed"
                    except requests.exceptions.Timeout:
                        print("Geolocation API timeout")
                        auto_location = "Location Detection Timeout"
                        auto_location_display = "Location Detection Timeout"
                    except Exception as geo_error:
                        print(f"Geolocation error: {geo_error}")
                        auto_location = "Location Detection Failed"
                        auto_location_display = "Location Detection Failed"
                else:
                    auto_location = "Google API Key Not Configured"
                    auto_location_display = "Google API Key Not Configured"
            except Exception as e:
                print(f"Error fetching location: {e}")
                auto_location = "Location Detection Error"
                auto_location_display = "Location Detection Error"
                
        except Exception as e:
            print(f"Error fetching latest IoT data: {e}")
            auto_temp = 25.0
            auto_humidity = 45.0
            auto_location = "Auto-Detected"
            auto_location_display = "Current Location"
            last_reading_time = datetime.now().isoformat()
        
        # Show live IoT info with location
        st.info(f"🌡️ **Live Temperature:** {auto_temp}°C | 💧 **Humidity:** {auto_humidity}% | 📍 **Location:** {auto_location_display} | ⏱️ **Last Updated:** {last_reading_time[:19]}")
        
        with st.form("new_shipment_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                batch_id = st.text_input("Batch ID*", placeholder="e.g., BATCH-2025-005")
                product_name = st.text_input("Product Name*", placeholder="e.g., Insulin Vials")
                quantity = st.number_input("Quantity (units)*", min_value=1, value=1000, step=100)
                manufacturing_date = st.date_input("Manufacturing Date*")
            
            with col2:
                expiry_date = st.date_input("Expiry Date*")
                # Location is auto-fetched from latest IoT data (read-only)
                st.text_input(
                    "Initial Location* (Auto-detected from IoT)",
                    value=auto_location_display,
                    disabled=True,
                    help="Location is automatically fetched from the latest IoT sensor reading"
                )
                # Use the full location string (with coordinates) for backend
                location = auto_location
            
            submit_shipment = st.form_submit_button("🚀 Create Batch & Submit for FDA Approval", use_container_width=True)
            
            if submit_shipment:
                if batch_id and product_name and location:
                    try:
                        # Create batch record
                        batch_data = {
                            "batch_id": batch_id,
                            "manufacturer_email": st.session_state.user_email,
                            "product_name": product_name,
                            "quantity": quantity,
                            "manufacturing_date": str(manufacturing_date),
                            "expiry_date": str(expiry_date),
                            "initial_location": location
                        }
                        
                        response = requests.post(f"{BACKEND_URL}/batch/create", 
                                               json=batch_data,
                                               timeout=10)
                        
                        if response.status_code == 200:
                            # Also create initial IoT reading using live temperature/humidity
                            iot_data = {
                                "batch_id": batch_id,
                                "temperature": auto_temp,  # Use live temperature
                                "humidity": auto_humidity,  # Use live humidity
                                "location": location,
                                "sensor_id": f"SENSOR-MFG-{batch_id[-3:]}",
                                "timestamp": datetime.now().isoformat()
                            }
                            
                            requests.post(f"{BACKEND_URL}/iot/data", json=iot_data, timeout=10)
                            
                            st.success(f"✅ Batch {batch_id} created and submitted for FDA approval!")
                            st.info("📋 Status: Pending FDA Review")
                            st.rerun()
                        else:
                            st.error(f"Failed to create batch: {response.text}")
                    except Exception as e:
                        st.error(f"Error creating batch: {str(e)}")
                else:
                    st.warning("Please fill in all required fields (*)")
    
    st.markdown("---")
    
    # NOW: Display live IoT metrics (after create shipment section)
    df, latest = display_live_iot_metrics(role_color="#4A90E2")
    
    if df is None:
        return
    
    st.markdown("---")
    
    # Additional manufacturer-specific content
    if df is not None:
        # Timestamp is already parsed in display_live_iot_metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Temperature Trends by Batch")
            fig = px.line(df, x='timestamp', y='temperature', color='batch_id',
                         title='Temperature Over Time',
                         labels={'temperature': 'Temperature (°C)', 'timestamp': 'Time'})
            fig.add_hline(y=8, line_dash="dash", line_color="red", annotation_text="Max Safe Temp")
            fig.add_hline(y=2, line_dash="dash", line_color="blue", annotation_text="Min Safe Temp")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("💧 Humidity Trends by Batch")
            fig2 = px.line(df, x='timestamp', y='humidity', color='batch_id',
                          title='Humidity Over Time',
                          labels={'humidity': 'Humidity (%)', 'timestamp': 'Time'})
            st.plotly_chart(fig2, use_container_width=True)
        
        st.subheader("📋 Recent IoT Data Records")
        display_df = df[['batch_id', 'temperature', 'humidity', 'location', 'sensor_id', 'timestamp']].head(20)
        st.dataframe(display_df, use_container_width=True, height=400)
        
        st.subheader("📍 Temperature by Location")
        location_df = df.groupby('location')['temperature'].mean().reset_index()
        fig3 = px.bar(location_df, x='location', y='temperature',
                     title='Average Temperature by Location',
                     labels={'temperature': 'Avg Temperature (°C)', 'location': 'Location'})
        fig3.add_hline(y=5, line_dash="dash", line_color="green", annotation_text="Target Temp")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No IoT data available. Start the IoT simulator to generate data.")
    
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

def fda_dashboard():
    st.markdown('<div class="fda-accent">', unsafe_allow_html=True)
    st.title("🏛️ FDA Regulatory Dashboard")
    st.markdown("### Compliance Monitoring & Blockchain Verification")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # FIRST: Batch Approval Section (shown first, at the top)
    st.subheader("📋 Pending Batch Approvals")
    pending_batches = fetch_data("/batch/pending")
    
    if pending_batches and pending_batches.get("batches") and len(pending_batches["batches"]) > 0:
        for batch in pending_batches["batches"]:
            with st.expander(f"🔍 {batch['batch_id']} - {batch['product_name']} ({batch['quantity']} units)", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Manufacturer:** {batch['manufacturer_email']}")
                    st.write(f"**Product:** {batch['product_name']}")
                    st.write(f"**Quantity:** {batch['quantity']} units")
                
                with col2:
                    st.write(f"**Mfg Date:** {batch['manufacturing_date']}")
                    st.write(f"**Expiry Date:** {batch['expiry_date']}")
                    st.write(f"**Location:** {batch['initial_location']}")
                
                with col3:
                    st.write(f"**Status:** {batch['status'].upper()}")
                    st.write(f"**Submitted:** {batch['created_at'][:10]}")
                
                st.markdown("---")
                
                # Verify blockchain integrity
                verify_response = fetch_data(f"/verify/batch/{batch['batch_id']}")
                if verify_response:
                    if verify_response.get('is_valid'):
                        st.success(f"✅ Blockchain Verified: {verify_response.get('integrity_percentage', 0):.1f}% integrity")
                    else:
                        st.error(f"⚠️ Blockchain Warning: {verify_response.get('invalid_records', 0)} tampered records detected!")
                
                # Approval/Rejection Form
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    remarks = st.text_area(f"FDA Remarks for {batch['batch_id']}", 
                                          placeholder="Enter approval/rejection remarks...",
                                          key=f"remarks_{batch['batch_id']}")
                
                with col2:
                    st.write("")
                    st.write("")
                    if st.button("✅ Approve", key=f"approve_{batch['batch_id']}", type="primary", use_container_width=True):
                        if remarks:
                            try:
                                approval_data = {
                                    "batch_id": batch['batch_id'],
                                    "approved": True,
                                    "fda_email": st.session_state.user_email,
                                    "remarks": remarks
                                }
                                response = requests.post(f"{BACKEND_URL}/batch/approve", 
                                                       json=approval_data, timeout=10)
                                if response.status_code == 200:
                                    st.success(f"✅ Batch {batch['batch_id']} approved!")
                                    st.rerun()
                                else:
                                    st.error(f"Error: {response.text}")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                        else:
                            st.warning("Please enter remarks")
                    
                    if st.button("❌ Reject", key=f"reject_{batch['batch_id']}", use_container_width=True):
                        if remarks:
                            try:
                                approval_data = {
                                    "batch_id": batch['batch_id'],
                                    "approved": False,
                                    "fda_email": st.session_state.user_email,
                                    "remarks": remarks
                                }
                                response = requests.post(f"{BACKEND_URL}/batch/approve", 
                                                       json=approval_data, timeout=10)
                                if response.status_code == 200:
                                    st.error(f"❌ Batch {batch['batch_id']} rejected!")
                                    st.rerun()
                                else:
                                    st.error(f"Error: {response.text}")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                        else:
                            st.warning("Please enter rejection reason")
    else:
        st.info("✅ No pending batches for approval")
    
    st.markdown("---")
    
    # NOW: Display live IoT monitoring (after approval section)
    df, latest = display_live_iot_metrics(role_color="#50C878")
    
    st.markdown("---")
    
    alerts_data = fetch_data("/alerts?limit=100")
    
    col1, col2, col3 = st.columns(3)
    
    if alerts_data and alerts_data.get("alerts"):
        alerts = alerts_data["alerts"]
        total_alerts = len(alerts)
        high_severity = len([a for a in alerts if a.get("severity") == "high"])
        medium_severity = len([a for a in alerts if a.get("severity") == "medium"])
    else:
        total_alerts = 0
        high_severity = 0
        medium_severity = 0
    
    with col1:
        st.metric("Total Alerts", total_alerts, delta=None)
    with col2:
        st.metric("High Severity", high_severity, delta=None, delta_color="inverse")
    with col3:
        st.metric("Medium Severity", medium_severity, delta=None, delta_color="inverse")
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚠️ Active Alerts", "🔐 Blockchain Verification", "🔗 Blockchain Explorer", "📋 Audit Logs", "🗺️ Product Navigation"])
    
    with tab1:
        st.subheader("Active Temperature Alerts")
        
        if alerts_data and alerts_data.get("alerts"):
            alerts_df = pd.DataFrame(alerts_data["alerts"])
            # Handle timestamp parsing with error handling
            try:
                alerts_df['timestamp'] = pd.to_datetime(alerts_df['timestamp'], errors='coerce')
                alerts_df = alerts_df.dropna(subset=['timestamp'])
            except Exception as e:
                st.error(f"Error parsing timestamps: {e}")
            
            for idx, alert in alerts_df.iterrows():
                severity_color = "🔴" if alert['severity'] == "high" else "🟡"
                with st.expander(f"{severity_color} {alert['batch_id']} - {alert['alert_type']} ({alert['timestamp'].strftime('%Y-%m-%d %H:%M')})", expanded=(idx < 3)):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Batch ID:** {alert['batch_id']}")
                        st.write(f"**Severity:** {alert['severity'].upper()}")
                        st.write(f"**Temperature:** {alert['temperature']}°C")
                    with col2:
                        st.write(f"**Location:** {alert['location']}")
                        st.write(f"**Time:** {alert['timestamp']}")
                        st.write(f"**Message:** {alert['message']}")
        else:
            st.success("✓ No active alerts. All batches within safe parameters.")
    
    with tab2:
        st.subheader("Verify Data Integrity with Blockchain")
        
        with st.form("verify_form"):
            record_id = st.number_input("Enter Record ID to Verify", min_value=1, step=1)
            verify_button = st.form_submit_button("🔍 Verify Blockchain Hash")
            
            if verify_button:
                try:
                    response = requests.post(f"{BACKEND_URL}/verify", 
                                            json={"record_id": record_id},
                                            timeout=10)
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Log verification to audit trail
                        try:
                            requests.post(f"{BACKEND_URL}/audit/log", 
                                        json={
                                            "user_email": st.session_state.user_email,
                                            "role": st.session_state.user_role,
                                            "action": "Verified Blockchain Hash",
                                            "details": {
                                                "record_id": record_id,
                                                "is_valid": result["is_valid"]
                                            }
                                        },
                                        timeout=5)
                        except:
                            pass
                        
                        if result["is_valid"]:
                            st.success("✅ DATA INTEGRITY VERIFIED - No tampering detected")
                        else:
                            st.error("❌ TAMPERING DETECTED - Blockchain hash mismatch!")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**Stored Hash:**")
                            st.code(result["stored_hash"], language="text")
                        with col2:
                            st.write("**Calculated Hash:**")
                            st.code(result["calculated_hash"], language="text")
                        
                        st.json(result["record"])
                    else:
                        st.error(f"Verification failed: {response.text}")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        st.markdown("---")
        st.info("💡 **How it works:** Each IoT record is hashed using SHA-256. The verification process recalculates the hash from the stored data and compares it with the original hash. Any data modification will result in a different hash, detecting tampering.")
    
    with tab3:
        st.subheader("🔗 Public Blockchain Explorer")
        st.markdown("View all blockchain ledgers across the supply chain")
        
        # Log audit entry for viewing blockchain
        try:
            requests.post(f"{BACKEND_URL}/audit/log", 
                        json={
                            "user_email": st.session_state.user_email,
                            "role": st.session_state.user_role,
                            "action": "Viewed Blockchain Explorer",
                            "details": {"timestamp": datetime.now().isoformat()}
                        },
                        timeout=5)
        except:
            pass
        
        # Get all ledgers
        verify_all = fetch_data("/ledger/verify/all")
        
        if verify_all and verify_all.get("verifications"):
            verifications = verify_all["verifications"]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Batches", verify_all.get("total_batches", 0))
            with col2:
                valid_count = len([v for v in verifications if v["is_valid"]])
                st.metric("Valid Chains", valid_count)
            with col3:
                invalid_count = len([v for v in verifications if not v["is_valid"]])
                st.metric("Tampered Chains", invalid_count, delta_color="inverse")
            
            st.markdown("---")
            
            for verification in verifications:
                status_icon = "✅" if verification["is_valid"] else "❌"
                with st.expander(f"{status_icon} {verification['batch_id']} - {verification['total_blocks']} blocks", expanded=False):
                    if verification["is_valid"]:
                        st.success(f"Blockchain integrity verified - {verification['total_blocks']} blocks")
                    else:
                        st.error(f"Tampering detected in blocks: {verification['tampered_blocks']}")
                    
                    # Fetch and display ledger
                    ledger_data = fetch_data(f"/ledger/{verification['batch_id']}")
                    if ledger_data and ledger_data.get("ledger"):
                        for idx, block in enumerate(ledger_data["ledger"][:5]):  # Show first 5 blocks
                            st.write(f"**Block {idx}:** {block['event']} by {block['actor_role']} at {block['timestamp'][:19]}")
                        
                        if len(ledger_data["ledger"]) > 5:
                            st.info(f"... and {len(ledger_data['ledger']) - 5} more blocks")
        else:
            st.info("No blockchain data available yet")
    
    with tab4:
        st.subheader("📋 Complete Audit Trail")
        
        audit_logs = fetch_data("/audit/logs?limit=100")
        
        if audit_logs and audit_logs.get("logs"):
            logs = audit_logs["logs"]
            
            st.metric("Total Audit Entries", len(logs))
            
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                roles = list(set([log["role"] for log in logs]))
                selected_role = st.selectbox("Filter by Role", ["All"] + roles)
            with col2:
                actions = list(set([log["action"] for log in logs]))
                selected_action = st.selectbox("Filter by Action", ["All"] + actions)
            
            # Filter logs
            filtered_logs = logs
            if selected_role != "All":
                filtered_logs = [log for log in filtered_logs if log["role"] == selected_role]
            if selected_action != "All":
                filtered_logs = [log for log in filtered_logs if log["action"] == selected_action]
            
            # Display logs
            for log in filtered_logs[:50]:  # Show first 50
                with st.expander(f"{log['timestamp'][:19]} - {log['action']} by {log['user_email']}", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**User:** {log['user_email']}")
                        st.write(f"**Role:** {log['role']}")
                        st.write(f"**Action:** {log['action']}")
                    with col2:
                        st.write(f"**Batch ID:** {log.get('batch_id', 'N/A')}")
                        st.write(f"**Timestamp:** {log['timestamp']}")
                        st.write(f"**Hash Ref:** {log.get('hash_ref', 'N/A')[:16]}...")
                    
                    if log.get('details'):
                        st.json(log['details'])
        else:
            st.info("No audit logs available")
    
    with tab5:
        st.subheader("🗺️ Product Navigation - Route Verification")
        
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

def distributor_dashboard():
    st.markdown('<div class="distributor-accent">', unsafe_allow_html=True)
    st.title("🚚 Distributor Dashboard")
    st.markdown("### Shipment Tracking & Status Management")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # FIRST: Show FDA approved batches and shipment management
    all_batch_records = fetch_data("/batch/all")
    if all_batch_records and all_batch_records.get("batches"):
        approved_count = len([b for b in all_batch_records["batches"] if b["status"] == "approved"])
        pending_count = len([b for b in all_batch_records["batches"] if b["status"] == "pending"])
        rejected_count = len([b for b in all_batch_records["batches"] if b["status"] == "rejected"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ FDA Approved", approved_count)
        with col2:
            st.metric("⏳ Pending Approval", pending_count)
        with col3:
            st.metric("❌ Rejected", rejected_count)
        
        st.markdown("---")
    
    # Get FDA approved batches from batches table
    approved_batches_data = fetch_data("/batch/all")
    approved_batches = []
    if approved_batches_data and approved_batches_data.get("batches"):
        approved_batches = [b for b in approved_batches_data["batches"] if b["status"] == "approved"]
    
    # Get IoT data for batches
    batches_data = fetch_data("/batches")
    iot_batches = batches_data.get("batches", []) if batches_data else []
    
    # Merge: Show all approved batches, with IoT data if available
    batches = []
    for approved_batch in approved_batches:
        # Find matching IoT data
        iot_data = next((b for b in iot_batches if b["batch_id"] == approved_batch["batch_id"]), None)
        
        if iot_data:
            # Has IoT data
            batches.append(iot_data)
        else:
            # No IoT data yet, create placeholder
            batches.append({
                "batch_id": approved_batch["batch_id"],
                "latest_temperature": 0.0,
                "latest_humidity": 0.0,
                "location": approved_batch.get("initial_location", "No location data"),
                "last_update": approved_batch.get("created_at", "N/A"),
                "record_count": 0
            })
    
    if batches:
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Active Shipments", len(batches))
        with col2:
            in_transit = len([b for b in batches if "Transit" in b.get("location", "")])
            st.metric("In Transit", in_transit)
        with col3:
            avg_temp = sum([b["latest_temperature"] for b in batches]) / len(batches)
            st.metric("Avg Temperature", f"{avg_temp:.1f}°C")
        
        st.markdown("---")
        st.subheader("📦 Manage Shipments")
        
        for batch in batches:
            # Get current status
            try:
                status_response = requests.get(f"{BACKEND_URL}/batch/{batch['batch_id']}/status", timeout=5)
                current_status = status_response.json().get("current_status", "Created") if status_response.status_code == 200 else "Created"
            except:
                current_status = "Created"
            
            # Status badge
            status_emoji = {"Created": "📝", "Picked Up": "📦", "In Transit": "🚛", "Delivered": "✅"}
            status_color = {"Created": "🔵", "Picked Up": "🟡", "In Transit": "🟠", "Delivered": "🟢"}
            
            with st.expander(f"{status_emoji.get(current_status, '📦')} {batch['batch_id']} - Status: {current_status}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Batch info
                    subcol1, subcol2, subcol3 = st.columns(3)
                    with subcol1:
                        temp_status = "✅" if 2 <= batch['latest_temperature'] <= 8 else "⚠️"
                        st.metric("Temperature", f"{batch['latest_temperature']}°C", 
                                 delta=None if 2 <= batch['latest_temperature'] <= 8 else "Out of range")
                    with subcol2:
                        st.metric("Humidity", f"{batch['latest_humidity']}%")
                    with subcol3:
                        st.metric("Total Records", batch['record_count'])
                    
                    st.write(f"**Location:** {batch['location']}")
                    st.write(f"**Last Update:** {batch['last_update']}")
                
                with col2:
                    st.markdown("### Update Status")
                    new_status = st.selectbox(
                        "Change Status",
                        ["Created", "Picked Up", "In Transit", "Delivered"],
                        index=["Created", "Picked Up", "In Transit", "Delivered"].index(current_status),
                        key=f"status_{batch['batch_id']}"
                    )
                    
                    if st.button("Update Status", key=f"btn_{batch['batch_id']}", use_container_width=True):
                        try:
                            response = requests.post(
                                f"{BACKEND_URL}/batch/status",
                                json={
                                    "batch_id": batch['batch_id'],
                                    "status": new_status,
                                    "updated_by": "Distributor"
                                },
                                timeout=10
                            )
                            if response.status_code == 200:
                                st.success(f"✅ Status updated to: {new_status}")
                                st.rerun()
                            else:
                                st.error("Failed to update status")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                
                # Live IoT Data Table
                st.markdown("### 📊 Live IoT Readings")
                batch_detail = fetch_data(f"/iot/data/{batch['batch_id']}")
                if batch_detail and batch_detail.get("data"):
                    df = pd.DataFrame(batch_detail["data"])
                    # Handle timestamp parsing with error handling
                    try:
                        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                        df = df.dropna(subset=['timestamp'])
                    except Exception as e:
                        st.error(f"Error parsing timestamps: {e}")
                        continue
                    
                    # Filter out status update records
                    df_filtered = df[~df['sensor_id'].str.contains("STATUS_UPDATE", na=False)]
                    
                    # Highlight alerts
                    def highlight_alerts(row):
                        if row['temperature'] < 2 or row['temperature'] > 8:
                            return ['background-color: #ff4444; color: white'] * len(row)
                        return [''] * len(row)
                    
                    display_df = df_filtered[['timestamp', 'temperature', 'humidity', 'location', 'sensor_id']].head(10)
                    st.dataframe(display_df, use_container_width=True, height=300)
                    
                    # Temperature chart
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=df_filtered['timestamp'], y=df_filtered['temperature'], 
                                            mode='lines+markers', name='Temperature', line=dict(color='#FF6B6B')))
                    fig.add_hline(y=8, line_dash="dash", line_color="red")
                    fig.add_hline(y=2, line_dash="dash", line_color="blue")
                    fig.update_layout(title=f"Temperature History - {batch['batch_id']}",
                                     xaxis_title="Time", yaxis_title="Temperature (°C)",
                                     height=300)
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No active shipments at this time.")
    
    st.markdown("---")
    
    # NOW: Display live IoT monitoring (after shipment management)
    df, latest = display_live_iot_metrics(role_color="#FF8C00")
    
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

def pharmacy_dashboard():
    st.title("💊 Pharmacy Dashboard")
    st.markdown("### Batch Verification & Authenticity Check")
    
    st.markdown("---")
    
    # Batch Verification Section
    st.subheader("🔍 Verify Received Batch")
    
    # Get FDA approved batches from batches table
    approved_batches_data = fetch_data("/batch/all")
    batch_ids = []
    approved_batches = []
    
    if approved_batches_data and approved_batches_data.get("batches"):
        # Show only approved batches
        approved_batches = [b for b in approved_batches_data["batches"] if b["status"] == "approved"]
        batch_ids = [b["batch_id"] for b in approved_batches]
        
        # Debug info
        st.info(f"📊 Found {len(approved_batches)} FDA-approved batches available for verification")
    
    if batch_ids:
        
        selected_batch = st.selectbox("Select Batch to Verify", batch_ids)
        
        if st.button("Verify Batch Quality", type="primary"):
            batch_detail = fetch_data(f"/iot/data/{selected_batch}")
            
            if batch_detail and batch_detail.get("data") and len(batch_detail["data"]) > 0:
                records = batch_detail["data"]
                df = pd.DataFrame(records)
                
                temp_violations = len(df[(df['temperature'] < 2) | (df['temperature'] > 8)])
                total_records = len(df)
                compliance_rate = ((total_records - temp_violations) / total_records) * 100
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Records", total_records)
                with col2:
                    st.metric("Temperature Violations", temp_violations, 
                             delta_color="inverse")
                with col3:
                    status_emoji = "✅" if compliance_rate >= 95 else "⚠️"
                    st.metric("Compliance Rate", f"{compliance_rate:.1f}%", 
                             delta=f"{status_emoji}")
                
                if compliance_rate >= 95:
                    st.success(f"✅ **BATCH APPROVED** - {selected_batch} meets quality standards")
                else:
                    st.error(f"⚠️ **BATCH REJECTED** - {selected_batch} has quality issues")
                
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Temperature Distribution")
                    fig = px.histogram(df, x='temperature', nbins=20,
                                      title='Temperature Distribution',
                                      labels={'temperature': 'Temperature (°C)'})
                    fig.add_vline(x=2, line_dash="dash", line_color="blue", annotation_text="Min")
                    fig.add_vline(x=8, line_dash="dash", line_color="red", annotation_text="Max")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("Batch Journey")
                    # Handle timestamp parsing with error handling
                    try:
                        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                        df = df.dropna(subset=['timestamp'])
                    except Exception as e:
                        st.error(f"Error parsing timestamps: {e}")
                    df_sorted = df.sort_values('timestamp')
                    
                    for idx, row in df_sorted.head(10).iterrows():
                        status = "✅" if 2 <= row['temperature'] <= 8 else "⚠️"
                        st.write(f"{status} **{row['location']}** - {row['temperature']}°C - {row['timestamp'].strftime('%m/%d %H:%M')}")
                
                st.subheader("📊 Detailed Records")
                st.dataframe(df[['timestamp', 'temperature', 'humidity', 'location', 'sensor_id']], 
                           use_container_width=True)
            else:
                # No IoT data available for this batch yet
                st.warning(f"⚠️ No IoT monitoring data available for {selected_batch} yet.")
                st.info("This batch has been FDA approved but hasn't started IoT monitoring. IoT data will be available once the batch enters the supply chain with sensor monitoring.")
                
                # Show batch details from batches table
                batch_info = next((b for b in approved_batches if b["batch_id"] == selected_batch), None)
                if batch_info:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Product:** {batch_info.get('product_name', 'N/A')}")
                        st.write(f"**Quantity:** {batch_info.get('quantity', 'N/A')} units")
                        st.write(f"**Manufacturer:** {batch_info.get('manufacturer_email', 'N/A')}")
                    with col2:
                        st.write(f"**Mfg Date:** {batch_info.get('manufacturing_date', 'N/A')}")
                        st.write(f"**Expiry Date:** {batch_info.get('expiry_date', 'N/A')}")
                        st.write(f"**Status:** {batch_info.get('status', 'N/A').upper()}")
    else:
        st.info("No FDA-approved batches available for verification.")
    
    st.markdown("---")
    st.subheader("📋 Recent Batches")
    
    if batches_data and batches_data.get("batches"):
        for batch in batches_data["batches"][:5]:
            temp_status = "✅" if 2 <= batch['latest_temperature'] <= 8 else "⚠️"
            st.write(f"{temp_status} **{batch['batch_id']}** - {batch['latest_temperature']}°C - Last update: {batch['last_update']}")

def pharmacy_dashboard():
    st.markdown('<div class="pharmacy-accent">', unsafe_allow_html=True)
    st.title("💊 Pharmacy Dashboard")
    st.markdown("### Batch Verification & Quality Control")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # FIRST: Batch Verification Section
    st.subheader("🔍 Verify Received Batch")
    
    batches_data = fetch_data("/batches")
    
    if batches_data and batches_data.get("batches"):
        batch_ids = [b["batch_id"] for b in batches_data["batches"]]
        
        selected_batch = st.selectbox("Select Batch to Verify", batch_ids)
        
        if st.button("Verify Batch Quality", type="primary"):
            batch_detail = fetch_data(f"/iot/data/{selected_batch}")
            
            if batch_detail and batch_detail.get("data"):
                records = batch_detail["data"]
                df_batch = pd.DataFrame(records)
                
                temp_violations = len(df_batch[(df_batch['temperature'] < 20) | (df_batch['temperature'] > 30)])
                total_records = len(df_batch)
                compliance_rate = ((total_records - temp_violations) / total_records) * 100 if total_records > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Records", total_records)
                with col2:
                    st.metric("Temperature Violations", temp_violations, delta_color="inverse")
                with col3:
                    status_emoji = "✅" if compliance_rate >= 95 else "⚠️"
                    st.metric("Compliance Rate", f"{compliance_rate:.1f}%", delta=f"{status_emoji}")
                
                if compliance_rate >= 95:
                    st.success(f"✅ **BATCH APPROVED** - {selected_batch} meets quality standards")
                else:
                    st.error(f"⚠️ **BATCH REJECTED** - {selected_batch} has quality issues")
    else:
        st.info("No batches available for verification.")
    
    st.markdown("---")
    
    # NOW: Display live IoT monitoring (after verification section)
    df, latest = display_live_iot_metrics(role_color="#9370DB")
    
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

def main():
    init_session_state()
    
    if not st.session_state.authenticated:
        login_page()
    else:
        # Auto-refresh every 5 minutes ONLY when authenticated (300000ms = 5 minutes)
        count = st_autorefresh(interval=300000, limit=None, key="iot_refresh")
        st.sidebar.title("PharmaChain")
        st.sidebar.markdown(f"**User:** {st.session_state.user_email}")
        st.sidebar.markdown(f"**Role:** {st.session_state.user_role}")
        st.sidebar.markdown("---")
        
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.session_state.user_role = None
            st.rerun()
        
        st.sidebar.markdown("---")
        
        # Manual refresh button
        if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### System Status")
        
        try:
            health = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if health.status_code == 200:
                st.sidebar.success("✅ Backend Online")
            else:
                st.sidebar.error("❌ Backend Error")
        except:
            st.sidebar.error("❌ Backend Offline")
        
        # Show auto-refresh info
        st.sidebar.info("🔄 Auto-refresh: Every 5 min")
        
        st.sidebar.markdown("---")
        
        if st.session_state.user_role == "Manufacturer":
            manufacturer_dashboard()
        elif st.session_state.user_role == "FDA":
            fda_dashboard()
        elif st.session_state.user_role == "Distributor":
            distributor_dashboard()
        elif st.session_state.user_role == "Pharmacy":
            pharmacy_dashboard()

if __name__ == "__main__":
    main()
