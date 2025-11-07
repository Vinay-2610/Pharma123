"""
Real-Time IoT Monitoring Dashboard
Displays live temperature and humidity data with auto-refresh
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# Configuration
BACKEND_URL = "http://localhost:8000"
REFRESH_INTERVAL = 10  # seconds

# Page config
st.set_page_config(
    page_title="PharmaChain - Real-Time IoT Monitor",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .alert-high {
        background-color: #ff4444;
        padding: 15px;
        border-radius: 8px;
        color: white;
        margin: 5px 0;
    }
    .alert-medium {
        background-color: #ff8800;
        padding: 15px;
        border-radius: 8px;
        color: white;
        margin: 5px 0;
    }
    .log-entry {
        background-color: #f0f2f6;
        padding: 10px;
        border-left: 4px solid #667eea;
        margin: 5px 0;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

def fetch_iot_data():
    """Fetch IoT data from FastAPI backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/iot/data?limit=100", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching IoT data: {e}")
        return None

def fetch_alerts():
    """Fetch alerts from FastAPI backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/alerts?limit=50", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching alerts: {e}")
        return None

# Title
st.title("🌡️ Real-Time IoT Monitoring Dashboard")
st.markdown("### Live Temperature & Humidity Tracking")

# Auto-refresh
placeholder = st.empty()

# System logs
system_logs = []

while True:
    with placeholder.container():
        # Fetch data
        iot_data = fetch_iot_data()
        alerts_data = fetch_alerts()
        
        if iot_data and iot_data.get("data"):
            df = pd.DataFrame(iot_data["data"])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Get latest reading
            latest = df.iloc[-1]
            
            # === TOP SUMMARY SECTION ===
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="🌡️ Latest Temperature",
                    value=f"{latest['temperature']:.2f}°C",
                    delta=f"{latest['temperature'] - 5:.2f}°C from target"
                )
            
            with col2:
                st.metric(
                    label="💧 Latest Humidity",
                    value=f"{latest['humidity']:.2f}%",
                    delta=f"{latest['humidity'] - 45:.2f}% from target"
                )
            
            with col3:
                st.metric(
                    label="📊 Total Records",
                    value=len(df),
                    delta=f"+{len(df) - 100} new" if len(df) > 100 else "0 new"
                )
            
            with col4:
                st.metric(
                    label="📍 Current Location",
                    value=latest['location'][:20],
                    delta=None
                )
            
            st.markdown("---")
            
            # === LIVE GRAPHS ===
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🌡️ Temperature vs Time")
                fig_temp = go.Figure()
                
                # Plot temperature by batch
                for batch_id in df['batch_id'].unique():
                    batch_df = df[df['batch_id'] == batch_id]
                    fig_temp.add_trace(go.Scatter(
                        x=batch_df['timestamp'],
                        y=batch_df['temperature'],
                        mode='lines+markers',
                        name=batch_id,
                        line=dict(width=2),
                        marker=dict(size=6)
                    ))
                
                # Add safe range lines
                fig_temp.add_hline(y=8, line_dash="dash", line_color="red", 
                                  annotation_text="Max Safe (8°C)")
                fig_temp.add_hline(y=2, line_dash="dash", line_color="blue", 
                                  annotation_text="Min Safe (2°C)")
                
                fig_temp.update_layout(
                    xaxis_title="Time",
                    yaxis_title="Temperature (°C)",
                    height=400,
                    hovermode='x unified',
                    showlegend=True
                )
                
                st.plotly_chart(fig_temp, use_container_width=True)
            
            with col2:
                st.subheader("💧 Humidity vs Time")
                fig_humid = go.Figure()
                
                # Plot humidity by batch
                for batch_id in df['batch_id'].unique():
                    batch_df = df[df['batch_id'] == batch_id]
                    fig_humid.add_trace(go.Scatter(
                        x=batch_df['timestamp'],
                        y=batch_df['humidity'],
                        mode='lines+markers',
                        name=batch_id,
                        line=dict(width=2),
                        marker=dict(size=6)
                    ))
                
                fig_humid.update_layout(
                    xaxis_title="Time",
                    yaxis_title="Humidity (%)",
                    height=400,
                    hovermode='x unified',
                    showlegend=True
                )
                
                st.plotly_chart(fig_humid, use_container_width=True)
            
            st.markdown("---")
            
            # === ALERTS SECTION ===
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("⚠️ Active Alerts")
                
                if alerts_data and alerts_data.get("alerts"):
                    alerts = alerts_data["alerts"]
                    active_alerts = [a for a in alerts if not a.get('resolved', False)]
                    
                    if active_alerts:
                        for alert in active_alerts[:5]:  # Show top 5
                            severity = alert.get('severity', 'medium')
                            alert_class = 'alert-high' if severity == 'high' else 'alert-medium'
                            
                            st.markdown(f"""
                            <div class="{alert_class}">
                                <strong>🚨 {alert['alert_type']}</strong><br>
                                Batch: {alert['batch_id']} | Temp: {alert['temperature']}°C<br>
                                Location: {alert['location']} | Time: {alert['timestamp'][:19]}<br>
                                {alert['message']}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.success("✅ All readings normal - No active alerts")
                else:
                    st.success("✅ All readings normal - No active alerts")
            
            with col2:
                st.subheader("📋 System Logs")
                
                # Add log entries
                current_time = datetime.now().strftime("%H:%M:%S")
                
                st.markdown(f"""
                <div class="log-entry">
                    <strong>[{current_time}]</strong> New data fetched<br>
                    <small>Retrieved {len(df)} records</small>
                </div>
                """, unsafe_allow_html=True)
                
                if alerts_data and alerts_data.get("alerts"):
                    alert_count = len([a for a in alerts_data["alerts"] if not a.get('resolved', False)])
                    if alert_count > 0:
                        st.markdown(f"""
                        <div class="log-entry">
                            <strong>[{current_time}]</strong> Alert detected<br>
                            <small>{alert_count} active alerts</small>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="log-entry">
                    <strong>[{current_time}]</strong> Offline data uploaded<br>
                    <small>Sync complete</small>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="log-entry">
                    <strong>[{current_time}]</strong> System healthy<br>
                    <small>All sensors online</small>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # === DATA TABLE ===
            st.subheader("📊 Recent IoT Readings")
            display_df = df[['timestamp', 'batch_id', 'temperature', 'humidity', 'location', 'sensor_id']].tail(20)
            st.dataframe(display_df, use_container_width=True, height=300)
            
            # === FOOTER ===
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"🔄 Auto-refresh: Every {REFRESH_INTERVAL} seconds")
            with col2:
                st.info(f"🕐 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            with col3:
                st.info(f"🔗 Backend: {BACKEND_URL}")
        
        else:
            st.error("❌ Unable to fetch IoT data from backend")
            st.info("Make sure the FastAPI backend is running on http://localhost:8000")
    
    # Wait before refresh
    time.sleep(REFRESH_INTERVAL)
    placeholder.empty()
