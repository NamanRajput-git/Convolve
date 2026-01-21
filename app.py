"""
ASHA AI - Streamlit Frontend
Voice-first healthcare memory system
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main_pipeline import pipeline
from qdrant_manager import qdrant_client
from privacy import privacy_manager
import config

# Page configuration
st.set_page_config(
    page_title="ASHA AI - Healthcare Memory",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile-friendly design
st.markdown("""
<style>
    .main {
        padding: 1rem;
    }
    .risk-high {
        background-color: #ffebee;
        border-left: 4px solid  #c62828;
        padding: 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    .risk-medium {
        background-color: #fff8e1;
        border-left: 4px solid #f57c00;
        padding: 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    .risk-low {
        background-color: #e8f5e9;
        border-left: 4px solid #2e7d32;
        padding: 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    .stButton>button {
        width: 100%;
        height: 3rem;
        font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'user_context' not in st.session_state:
        st.session_state.user_context = {
            'age': 25,
            'pregnancy_stage': None,
            'language': 'hi'
        }


def user_interface_tab():
    """Main user-facing voice interface"""
    st.title("🏥 ASHA AI - आपकी स्वास्थ्य सहायक")
    st.caption("Voice-first healthcare memory system | आवाज़-आधारित स्वास्थ्य सहायता")
    
    # Health check
    health = pipeline.health_check()
    if not health['qdrant']:
        st.error("⚠️ System Error: Qdrant database not available. Please contact administrator.")
        st.stop()
    
    # Language selection
    col1, col2 = st.columns([2, 1])
    with col1:
        language = st.selectbox(
            "भाषा चुनें / Select Language",
            options=['hi', 'en'],
            format_func=lambda x: "हिंदी (Hindi)" if x == 'hi' else "English",
            key='language_select'
        )
        st.session_state.user_context['language'] = language
    
    # User context inputs (collapsible)
    with st.expander("📋 अपनी जानकारी / Your Information (Optional)"):
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("उम्र / Age", min_value=15, max_value=50, value=25)
            st.session_state.user_context['age'] = age
        
        with col2:
            pregnancy_options = {
                None: "Not Pregnant / गर्भवती नहीं",
                "1st_trimester": "1st Trimester (0-3 months) / पहली तिमाही",
                "2nd_trimester": "2nd Trimester (4-6 months) / दूसरी तिमाही",
                "3rd_trimester": "3rd Trimester (7-9 months) / तीसरी तिमाही",
                "postpartum": "After Delivery / प्रसव के बाद"
            }
            pregnancy_stage = st.selectbox(
                "गर्भावस्था / Pregnancy Stage",
                options=list(pregnancy_options.keys()),
                format_func=lambda x: pregnancy_options[x]
            )
            st.session_state.user_context['pregnancy_stage'] = pregnancy_stage
    
    st.divider()
    
    # Voice input section
    st.subheader("🎤 अपनी समस्या बताएं / Share Your Health Concern")
    
    # Create tabs for different input methods
    input_tab1, input_tab2 = st.tabs(["🎙️ Record Voice", "⌨️ Type Text"])
    
    # Initialize variables
    audio_bytes = None
    uploaded_audio = None
    text_input = None
    
    with input_tab1:
        st.write("Click the microphone button below to record your health concern:")
        
        # Using browser's native speech recognition via custom component
        from audio_recorder_streamlit import audio_recorder
        
        audio_bytes = audio_recorder(
            pause_threshold=2.0,
            sample_rate=16000,
            text="Click to record",
            recording_color="#e8b62c",
            neutral_color="#6aa36f",
            icon_name="microphone",
            icon_size="3x",
        )
        
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            st.success("✅ Recording captured! Click 'Get Guidance' below to process.")
    
    with input_tab2:
        text_input = st.text_area(
            "Type your health question / अपना स्वास्थ्य प्रश्न लिखें",
            placeholder="उदाहरण: मुझे चक्कर आ रहे हैं और कमजोरी महसूस हो रही है\nExample: I am feeling dizzy and weak",
            height=120
        )
    
    # Process button
    if st.button("✨ सलाह पाएं / Get Guidance", type="primary"):
        if audio_bytes:
            # Process live recording
            with st.spinner("आपकी आवाज़ सुन रहे हैं... / Listening to your voice..."):
                # Save audio bytes to temporary file
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                    tmp_file.write(audio_bytes)
                    audio_path = tmp_file.name
                
                try:
                    # Process through pipeline
                    result = pipeline.process_voice_query(
                        audio_path,
                        st.session_state.user_context,
                        language
                    )
                    
                    display_response(result)
                finally:
                    # Clean up temp file
                    if os.path.exists(audio_path):
                        os.unlink(audio_path)
        
        elif uploaded_audio:
            # Process audio
            with st.spinner("आपकी आवाज़ सुन रहे हैं... / Listening to your voice..."):
                # Save uploaded file
                from voice_input import voice_input
                audio_path = voice_input.save_uploaded_audio(uploaded_audio)
                
                # Process through pipeline
                result = pipeline.process_voice_query(
                    audio_path,
                    st.session_state.user_context,
                    language
                )
                
                display_response(result)
        
        elif text_input:
            # Process text
            with st.spinner("विश्लेषण कर रहे हैं... / Analyzing..."):
                result = pipeline.process_text_query(
                    text_input,
                    st.session_state.user_context,
                    language
                )
                
                display_response(result)
        
        else:
            st.warning("कृपया ऑडियो अपलोड करें या टेक्स्ट लिखें / Please upload audio or type text")
    
    # Show conversation history
    if st.session_state.conversation_history:
        st.divider()
        st.subheader("📝 पिछली बातचीत / Previous Conversations")
        
        for i, item in enumerate(reversed(st.session_state.conversation_history[-5:])):
            with st.expander(f"{item['timestamp'][:10]} - Risk: {item['risk_display']}"):
                st.write(f"**Question:** {item['query']}")
                st.write(f"**Answer:** {item['answer']}")
                if item.get('deterioration_alert') != "none":
                    st.warning(f"⚠️ {item['deterioration_message']}")


def display_response(result):
    """Display AI response in UI"""
    if not result['success']:
        st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
        return
    
    # Add to history
    st.session_state.conversation_history.append({
        'query': result['query'],
        'answer': result['answer'],
        'risk_score': result['risk_score'],
        'risk_display': result['risk_display'],
        'deterioration_alert': result['deterioration_alert'],
        'deterioration_message': result['deterioration_message'],
        'timestamp': result['timestamp']
    })
    
    st.success("✅ Response ready!")
    
    # Display main response
    st.markdown(f"### 🤖 ASHA AI:\n{result.get('answer')}")
    
    # Audio player
    if result.get("audio_path"):
        st.audio(result["audio_path"], format='audio/mp3')
        st.caption("🔊 सुनने के लिए प्ले करें / Click play to listen")
    
    # Risk display
    risk_score = result.get("risk_score", 0.0)
    risk_category = result.get('risk_category', 'Low')
    risk_display = result.get('risk_display', '#2ecc71')
    
    st.markdown(
        f"""
        <div style="padding: 15px; border-radius: 10px; background-color: {risk_display}20; border: 2px solid {risk_display}; margin-bottom: 20px;">
            <h4 style="color: {risk_display}; margin:0">Risk Level: {risk_category}</h4>
            <p style="margin:0">Score: {risk_score:.2f} | Sources: {result.get('evidence_count', 0)}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Escalation warning
    if result['should_escalate']:
        st.warning("⚠️ **Important:** Please consult ASHA worker or visit health center soon.")
        st.warning("⚠️ **महत्वपूर्ण:** कृपया ASHA कार्यकर्ता या स्वास्थ्य केंद्र से जल्द मिलें।")
    
    # Deterioration alert
    if result.get('deterioration_alert') == "high_priority":
        st.error(f"🚨 **Alert:** {result['deterioration_message']}")
    elif result.get('deterioration_alert') == "monitor":
        st.info(f"ℹ️ {result['deterioration_message']}")




def asha_dashboard_tab():
    """ASHA worker dashboard"""
    st.title("👩‍⚕️ ASHA Worker Dashboard")
    st.caption("Population health insights and high-risk alerts")
    
    # Health check
    health = pipeline.health_check()
    if not health['qdrant']:
        st.error("⚠️ System Error: Qdrant database not available.")
        st.stop()
    
    # High-risk women list
    st.subheader("🔴 High-Risk Women (Immediate Attention)")
    
    try:
        high_risk_users = qdrant_client.get_high_risk_users(
            threshold=config.RISK_THRESHOLD_HIGH,
            limit=20
        )
        
        if high_risk_users:
            # Create DataFrame
            df_data = []
            for user_data in high_risk_users:
                df_data.append({
                    "User ID": user_data.get("user_id", "")[:8] + "...",
                    "Age": user_data.get("age", "N/A"),
                    "Pregnancy Stage": user_data.get("pregnancy_stage", "N/A"),
                    "Risk Score": f"{user_data.get('risk_score', 0.0):.2f}",
                    "Last Signal": user_data.get("signal_type", "N/A"),
                    "Date": user_data.get("timestamp", "")[:10]
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
            
            st.metric("Total High-Risk Cases", len(high_risk_users))
        else:
            st.success("✅ No high-risk cases at the moment")
    
    except Exception as e:
        st.error(f"Error loading data: {e}")
    
    st.divider()
    
    # Statistics
    st.subheader("📊 Population Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("High Risk", len([u for u in high_risk_users if u.get('risk_score', 0) >= 0.7]) if high_risk_users else 0, delta=None)
    
    with col2:
        pregnant_count = len([u for u in high_risk_users if u.get('pregnancy_stage')]) if high_risk_users else 0
        st.metric("Pregnant Women Monitored", pregnant_count)
    
    with col3:
        st.metric("Evidence Records", "Qdrant-powered", delta="Real-time")
    
    st.divider()
    
    # Recommendations
    st.subheader("💡 Recommended Actions")
    
    if high_risk_users:
        for user in high_risk_users[:5]:  # Top 5
            risk_score = user.get('risk_score', 0.0)
            user_id = user.get('user_id', '')[:8]
            pregnancy_stage = user.get('pregnancy_stage', 'unknown')
            
            if risk_score >= 0.8:
                st.error(f"🚨 User {user_id}... - **Urgent follow-up needed** (Risk: {risk_score:.2f}, {pregnancy_stage})")
            elif risk_score >= 0.7:
                st.warning(f"⚠️ User {user_id}... - Schedule visit soon (Risk: {risk_score:.2f}, {pregnancy_stage})")
    else:
        st.info("No immediate actions required")
    
    st.divider()
    
    # Qdrant connection info
    st.subheader("🔧 System Status")
    health = pipeline.health_check()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Qdrant Database", "✅ Connected" if health['qdrant'] else "❌ Disconnected")
    with col2:
        st.metric("Memory System", "✅ Active" if health['qdrant'] else "❌ Inactive")
    
    if not health['qdrant']:
        st.error("⚠️ **CRITICAL:** Qdrant is not connected. System cannot function without vector database.")


def main():
    """Main application"""
    init_session_state()
    
    # Create tabs
    tab1, tab2 = st.tabs(["🏥 User Interface", "👩‍⚕️ ASHA Dashboard"])
    
    with tab1:
        user_interface_tab()
    
    with tab2:
        asha_dashboard_tab()
    
    # Footer
    st.divider()
    st.caption("ASHA AI - Powered by Qdrant Vector Memory | Built for rural healthcare workers and women")


if __name__ == "__main__":
    main()
