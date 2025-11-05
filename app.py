import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from supabase import create_client, Client

BACKEND_URL = "http://localhost:8000"

if "SUPABASE_URL" not in os.environ or "SUPABASE_KEY" not in os.environ:
    st.error("⚠️ Please set SUPABASE_URL and SUPABASE_KEY environment variables")
    st.info("Add your Supabase credentials to continue using PharmaChain")
    st.stop()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(
    page_title="PharmaChain - Supply Chain Monitoring",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None

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
                role = st.selectbox("Role", ["Manufacturer", "FDA", "Distributor", "Pharmacy"])
                
                submitted = st.form_submit_button("Login", use_container_width=True)
                
                if submitted:
                    if email and password:
                        try:
                            response = supabase.auth.sign_in_with_password({
                                "email": email,
                                "password": password
                            })
                            
                            if response.user:
                                st.session_state.authenticated = True
                                st.session_state.user_email = email
                                st.session_state.user_role = role
                                st.success(f"✓ Welcome back, {role}!")
                                st.rerun()
                            else:
                                st.error("Invalid credentials")
                        except Exception as e:
                            st.error(f"Login failed: {str(e)}")
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
                                    st.success("✓ Account created successfully! Please log in.")
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

def manufacturer_dashboard():
    st.title("🏭 Manufacturer Dashboard")
    st.markdown("### Real-time IoT Data & Analytics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    batches_data = fetch_data("/batches")
    iot_data = fetch_data("/iot/data?limit=100")
    alerts_data = fetch_data("/alerts?limit=50")
    
    if batches_data and batches_data.get("batches"):
        total_batches = len(batches_data["batches"])
    else:
        total_batches = 0
    
    if iot_data and iot_data.get("data"):
        total_readings = len(iot_data["data"])
    else:
        total_readings = 0
    
    if alerts_data and alerts_data.get("alerts"):
        total_alerts = len(alerts_data["alerts"])
    else:
        total_alerts = 0
    
    with col1:
        st.metric("Active Batches", total_batches)
    with col2:
        st.metric("Total Readings", total_readings)
    with col3:
        st.metric("Active Alerts", total_alerts)
    with col4:
        if iot_data and iot_data.get("data"):
            latest_temp = iot_data["data"][0]["temperature"]
            st.metric("Latest Temp", f"{latest_temp}°C")
    
    st.markdown("---")
    
    if iot_data and iot_data.get("data"):
        df = pd.DataFrame(iot_data["data"])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
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

def fda_dashboard():
    st.title("🏛️ FDA Regulatory Dashboard")
    st.markdown("### Compliance Monitoring & Blockchain Verification")
    
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
    
    tab1, tab2 = st.tabs(["⚠️ Active Alerts", "🔐 Blockchain Verification"])
    
    with tab1:
        st.subheader("Active Temperature Alerts")
        
        if alerts_data and alerts_data.get("alerts"):
            alerts_df = pd.DataFrame(alerts_data["alerts"])
            alerts_df['timestamp'] = pd.to_datetime(alerts_df['timestamp'])
            
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

def distributor_dashboard():
    st.title("🚚 Distributor Dashboard")
    st.markdown("### Shipment Tracking & Monitoring")
    
    batches_data = fetch_data("/batches")
    
    if batches_data and batches_data.get("batches"):
        batches = batches_data["batches"]
        
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
        st.subheader("📦 Active Shipments")
        
        for batch in batches:
            with st.expander(f"📦 {batch['batch_id']} - {batch['location']}", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    temp_status = "✅" if 2 <= batch['latest_temperature'] <= 8 else "⚠️"
                    st.metric("Temperature", f"{batch['latest_temperature']}°C", 
                             delta=None if 2 <= batch['latest_temperature'] <= 8 else "Out of range")
                with col2:
                    st.metric("Humidity", f"{batch['latest_humidity']}%")
                with col3:
                    st.metric("Total Records", batch['record_count'])
                
                st.write(f"**Location:** {batch['location']}")
                st.write(f"**Last Update:** {batch['last_update']}")
                
                batch_detail = fetch_data(f"/iot/data/{batch['batch_id']}")
                if batch_detail and batch_detail.get("data"):
                    df = pd.DataFrame(batch_detail["data"])
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['temperature'], 
                                            mode='lines+markers', name='Temperature'))
                    fig.add_hline(y=8, line_dash="dash", line_color="red")
                    fig.add_hline(y=2, line_dash="dash", line_color="blue")
                    fig.update_layout(title=f"Temperature History - {batch['batch_id']}",
                                     xaxis_title="Time", yaxis_title="Temperature (°C)",
                                     height=300)
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No active shipments at this time.")

def pharmacy_dashboard():
    st.title("💊 Pharmacy Dashboard")
    st.markdown("### Batch Verification & Quality Control")
    
    st.subheader("🔍 Verify Received Batch")
    
    batches_data = fetch_data("/batches")
    
    if batches_data and batches_data.get("batches"):
        batch_ids = [b["batch_id"] for b in batches_data["batches"]]
        
        selected_batch = st.selectbox("Select Batch to Verify", batch_ids)
        
        if st.button("Verify Batch Quality", type="primary"):
            batch_detail = fetch_data(f"/iot/data/{selected_batch}")
            
            if batch_detail and batch_detail.get("data"):
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
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df_sorted = df.sort_values('timestamp')
                    
                    for idx, row in df_sorted.head(10).iterrows():
                        status = "✅" if 2 <= row['temperature'] <= 8 else "⚠️"
                        st.write(f"{status} **{row['location']}** - {row['temperature']}°C - {row['timestamp'].strftime('%m/%d %H:%M')}")
                
                st.subheader("📊 Detailed Records")
                st.dataframe(df[['timestamp', 'temperature', 'humidity', 'location', 'sensor_id']], 
                           use_container_width=True)
    else:
        st.info("No batches available for verification.")
    
    st.markdown("---")
    st.subheader("📋 Recent Batches")
    
    if batches_data and batches_data.get("batches"):
        for batch in batches_data["batches"][:5]:
            temp_status = "✅" if 2 <= batch['latest_temperature'] <= 8 else "⚠️"
            st.write(f"{temp_status} **{batch['batch_id']}** - {batch['latest_temperature']}°C - Last update: {batch['last_update']}")

def main():
    init_session_state()
    
    if not st.session_state.authenticated:
        login_page()
    else:
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
        st.sidebar.markdown("### System Status")
        
        try:
            health = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if health.status_code == 200:
                st.sidebar.success("✅ Backend Online")
            else:
                st.sidebar.error("❌ Backend Error")
        except:
            st.sidebar.error("❌ Backend Offline")
        
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
