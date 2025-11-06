"""
Blockchain Ledger Viewer Component
Displays chain of custody with hash verification
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

def display_blockchain_ledger(ledger_data, batch_id):
    """Display blockchain ledger with visual timeline"""
    
    if not ledger_data or len(ledger_data) == 0:
        st.info("No blockchain records found for this batch")
        return
    
    st.subheader(f"🔗 Blockchain Ledger: {batch_id}")
    
    # Verify integrity
    is_valid = True
    for i in range(1, len(ledger_data)):
        if ledger_data[i]["prev_hash"] != ledger_data[i-1]["curr_hash"]:
            is_valid = False
            break
    
    if is_valid:
        st.success(f"✅ Blockchain Integrity Verified - {len(ledger_data)} blocks")
    else:
        st.error("⚠️ Blockchain Tampering Detected!")
    
    # Timeline visualization
    events = [entry["event"] for entry in ledger_data]
    timestamps = [datetime.fromisoformat(entry["timestamp"].replace('Z', '+00:00')) for entry in ledger_data]
    actors = [entry["actor_role"] for entry in ledger_data]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=list(range(len(events))),
        mode='markers+lines+text',
        marker=dict(size=15, color='lightblue', line=dict(width=2, color='darkblue')),
        text=events,
        textposition="top center",
        name="Events",
        hovertemplate='<b>%{text}</b><br>Time: %{x}<br>Actor: ' + '<br>'.join(actors)
    ))
    
    fig.update_layout(
        title="Chain of Custody Timeline",
        xaxis_title="Time",
        yaxis_title="Block Number",
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed blocks
    st.markdown("### 📦 Block Details")
    
    for idx, block in enumerate(ledger_data):
        with st.expander(f"Block #{idx} - {block['event']} by {block['actor_role']}", expanded=(idx < 3)):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Event:** {block['event']}")
                st.write(f"**Actor:** {block['actor_role']}")
                st.write(f"**Email:** {block.get('actor_email', 'N/A')}")
                st.write(f"**Timestamp:** {block['timestamp']}")
            
            with col2:
                st.write(f"**Previous Hash:**")
                st.code(block['prev_hash'][:32] + "...", language="text")
                st.write(f"**Current Hash:**")
                st.code(block['curr_hash'][:32] + "...", language="text")
            
            if block.get('data'):
                st.json(block['data'])
            
            # Verify this block
            if idx > 0:
                if block['prev_hash'] == ledger_data[idx-1]['curr_hash']:
                    st.success("✅ Hash chain valid")
                else:
                    st.error("❌ Hash mismatch - tampering detected!")

def display_audit_logs(audit_data):
    """Display audit trail"""
    
    if not audit_data or len(audit_data) == 0:
        st.info("No audit logs available")
        return
    
    st.subheader("📋 Audit Trail")
    
    df = pd.DataFrame(audit_data)
    
    # Format timestamp
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Display as table
    display_cols = ['timestamp', 'user_email', 'role', 'action', 'batch_id']
    available_cols = [col for col in display_cols if col in df.columns]
    
    st.dataframe(
        df[available_cols],
        use_container_width=True,
        height=400
    )
    
    # Summary stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Actions", len(df))
    with col2:
        unique_users = df['user_email'].nunique() if 'user_email' in df.columns else 0
        st.metric("Unique Users", unique_users)
    with col3:
        unique_batches = df['batch_id'].nunique() if 'batch_id' in df.columns else 0
        st.metric("Batches Affected", unique_batches)
