import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from supabase import create_client, Client
from dotenv import load_dotenv

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

def manufacturer_dashboard():
    st.title("🏭 Manufacturer Dashboard")
    st.markdown("### Real-time IoT Data & Analytics")
    
    # Add Create New Shipment Section
    with st.expander("📦 Create New Shipment", expanded=False):
        st.markdown("### Register a New Pharmaceutical Batch")
        with st.form("new_shipment_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                batch_id = st.text_input("Batch ID*", placeholder="e.g., BATCH-2025-005")
                product_name = st.text_input("Product Name*", placeholder="e.g., Insulin Vials")
                quantity = st.number_input("Quantity (units)*", min_value=1, value=1000, step=100)
                manufacturing_date = st.date_input("Manufacturing Date*")
            
            with col2:
                expiry_date = st.date_input("Expiry Date*")
                location = st.text_input("Initial Location*", placeholder="e.g., Manufacturing Plant - Mumbai")
                temperature = st.number_input("Initial Temperature (°C)", min_value=-10.0, max_value=50.0, value=5.0, step=0.1)
                humidity = st.number_input("Initial Humidity (%)", min_value=0.0, max_value=100.0, value=45.0, step=1.0)
            
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
                            # Also create initial IoT reading
                            iot_data = {
                                "batch_id": batch_id,
                                "temperature": temperature,
                                "humidity": humidity,
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
    
    # Batch Approval Section
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
    
    tab1, tab2, tab3, tab4 = st.tabs(["⚠️ Active Alerts", "🔐 Blockchain Verification", "🔗 Blockchain Explorer", "📋 Audit Logs"])
    
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

def distributor_dashboard():
    st.title("🚚 Distributor Dashboard")
    st.markdown("### Shipment Tracking & Status Management")
    
    # Show FDA approved batches
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
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    
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

def pharmacy_dashboard():
    st.title("💊 Pharmacy Dashboard")
    st.markdown("### Batch Verification & Authenticity Check")
    
    st.markdown("---")
    
    # Batch Verification Section
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
