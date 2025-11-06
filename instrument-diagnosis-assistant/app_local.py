import streamlit as st
import json
import time
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Instrument Diagnosis Assistant (Local Demo)",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Remove Streamlit deployment components
st.markdown(
    """
      <style>
        .stAppDeployButton {display:none;}
        #MainMenu {visibility: hidden;}
      </style>
    """,
    unsafe_allow_html=True,
)

def simulate_diagnosis(files_info, analysis_mode, confidence_threshold):
    """Simulate AI diagnosis for demo purposes"""
    
    # Simulate processing time
    time.sleep(2)
    
    # Mock diagnosis results based on inputs
    if files_info['failed_logs'] and files_info['gold_logs']:
        # Simulate comparison analysis
        status = "FAIL" if "fail" in str(files_info['failed_logs']).lower() else "PASS"
        confidence = 0.85 if status == "FAIL" else 0.92
        
        failure_indicators = [
            "Optical alignment deviation detected in sector 3",
            "Communication timeout errors in log entries 45-67", 
            "Temperature sensor readings outside normal range"
        ] if status == "FAIL" else []
        
        recommendations = [
            "Recalibrate optical alignment system",
            "Check communication cable connections",
            "Verify temperature sensor functionality"
        ] if status == "FAIL" else [
            "System operating within normal parameters",
            "Continue routine maintenance schedule"
        ]
        
    else:
        status = "UNCERTAIN"
        confidence = 0.45
        failure_indicators = ["Insufficient data for complete analysis"]
        recommendations = ["Upload both gold standard and failed unit logs for comparison"]
    
    return {
        'status': status,
        'confidence': confidence,
        'failure_indicators': failure_indicators,
        'recommendations': recommendations,
        'summary': f"Analysis completed using {analysis_mode} mode with {confidence:.1%} confidence. " +
                  f"Based on uploaded files: {sum(len(files) for files in files_info.values())} total files processed."
    }

def main():
    st.title("🔧 Instrument Diagnosis Assistant")
    st.markdown("### 📍 **Local Demo Mode** - Simulated AI Responses")
    
    # Add file upload section at the top
    st.markdown("### 📁 Upload Files for Analysis")
    
    # Create tabs for different file types
    tab1, tab2, tab3 = st.tabs(["📊 Log Files", "📋 Documentation", "🔍 Troubleshooting Guides"])
    
    with tab1:
        st.markdown("**Upload instrument log files for analysis**")
        col1, col2 = st.columns(2)
        
        with col1:
            gold_standard_logs = st.file_uploader(
                "Gold Standard Logs (Reference)",
                type=['txt', 'log', 'csv'],
                accept_multiple_files=True,
                key="gold_logs",
                help="Upload logs from properly functioning instruments"
            )
        
        with col2:
            failed_unit_logs = st.file_uploader(
                "Failed Unit Logs",
                type=['txt', 'log', 'csv'],
                accept_multiple_files=True,
                key="failed_logs",
                help="Upload logs from instruments experiencing issues"
            )
    
    with tab2:
        st.markdown("**Upload engineering documentation and component specifications**")
        engineering_docs = st.file_uploader(
            "Engineering Documents",
            type=['pdf', 'doc', 'docx', 'txt', 'md'],
            accept_multiple_files=True,
            key="eng_docs",
            help="Upload component specifications, system architecture docs, etc."
        )
    
    with tab3:
        st.markdown("**Upload troubleshooting guides with images and diagrams**")
        troubleshooting_guides = st.file_uploader(
            "Troubleshooting Guides",
            type=['pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            key="trouble_guides",
            help="Upload multi-modal troubleshooting documentation"
        )
    
    # Store uploaded files info
    files_info = {
        'gold_logs': gold_standard_logs or [],
        'failed_logs': failed_unit_logs or [],
        'eng_docs': engineering_docs or [],
        'trouble_guides': troubleshooting_guides or []
    }
    
    # Show file summary if files are uploaded
    total_files = sum(len(files) for files in files_info.values())
    if total_files > 0:
        st.success(f"✅ {total_files} files uploaded and ready for analysis")
    
    st.divider()

    # Sidebar for settings
    with st.sidebar:
        st.header("Settings")
        
        # Diagnosis-specific options
        st.subheader("🔧 Diagnosis Options")
        
        analysis_mode = st.selectbox(
            "Analysis Mode",
            ["Comprehensive Analysis", "Quick Diagnosis", "Component Focus", "Log Comparison Only"],
            help="Choose the type of analysis to perform"
        )
        
        confidence_threshold = st.slider(
            "Confidence Threshold",
            min_value=0.5,
            max_value=0.95,
            value=0.75,
            step=0.05,
            help="Minimum confidence level for diagnosis decisions"
        )
        
        include_visual_analysis = st.checkbox(
            "Include Visual Analysis",
            value=True,
            help="Analyze images and diagrams in troubleshooting guides"
        )
        
        st.subheader("Demo Info")
        st.info("🎭 This is a local demo mode with simulated AI responses. For full functionality, deploy the complete AgentCore backend.")

    # Initialize session state for results
    if 'diagnosis_results' not in st.session_state:
        st.session_state.diagnosis_results = None

    # Diagnosis Results Display Section
    if st.session_state.diagnosis_results:
        st.markdown("### 🎯 Latest Diagnosis Results")
        
        results = st.session_state.diagnosis_results
        
        # Status indicator
        status = results.get('status', 'UNKNOWN')
        confidence = results.get('confidence', 0.0)
        
        if status == 'PASS':
            st.success(f"✅ **INSTRUMENT STATUS: PASS** (Confidence: {confidence:.1%})")
        elif status == 'FAIL':
            st.error(f"❌ **INSTRUMENT STATUS: FAIL** (Confidence: {confidence:.1%})")
        else:
            st.warning(f"⚠️ **INSTRUMENT STATUS: UNCERTAIN** (Confidence: {confidence:.1%})")
        
        # Results in columns
        col1, col2 = st.columns(2)
        
        with col1:
            if results.get('failure_indicators'):
                st.markdown("**🔍 Failure Indicators:**")
                for indicator in results['failure_indicators']:
                    st.markdown(f"• {indicator}")
        
        with col2:
            if results.get('recommendations'):
                st.markdown("**💡 Recommendations:**")
                for rec in results['recommendations']:
                    st.markdown(f"• {rec}")
        
        if results.get('summary'):
            with st.expander("📋 Detailed Analysis Summary"):
                st.markdown(results['summary'])
        
        st.divider()

    # Quick action buttons
    st.markdown("### 🚀 Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔍 Analyze Logs"):
            if total_files > 0:
                with st.spinner("Analyzing logs..."):
                    results = simulate_diagnosis(files_info, analysis_mode, confidence_threshold)
                    st.session_state.diagnosis_results = results
                st.rerun()
            else:
                st.warning("Please upload some files first!")
    
    with col2:
        if st.button("🔧 Identify Components"):
            if files_info['eng_docs']:
                with st.spinner("Identifying components..."):
                    st.success("Found 15 components: 8 optical sensors, 4 motor controllers, 2 communication modules, 1 main processor")
            else:
                st.warning("Please upload engineering documentation first!")
    
    with col3:
        if st.button("📚 Process Guides"):
            if files_info['trouble_guides']:
                with st.spinner("Processing troubleshooting guides..."):
                    st.success("Extracted 12 procedures from uploaded guides with visual analysis")
            else:
                st.warning("Please upload troubleshooting guides first!")
    
    with col4:
        if st.button("🎯 Full Diagnosis"):
            if total_files > 0:
                with st.spinner("Performing comprehensive diagnosis..."):
                    results = simulate_diagnosis(files_info, analysis_mode, confidence_threshold)
                    st.session_state.diagnosis_results = results
                st.rerun()
            else:
                st.warning("Please upload some files first!")

    # Chat interface
    st.markdown("### 💬 Ask Questions")
    
    if prompt := st.chat_input("Ask about instrument diagnosis, upload files, or request specific analysis..."):
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Simulate AI response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your question..."):
                time.sleep(1)
                
                # Generate contextual response based on prompt
                if "log" in prompt.lower():
                    response = "To analyze logs effectively, please upload both gold standard logs (from working instruments) and failed unit logs. I can then compare patterns and identify anomalies that indicate potential failures."
                elif "component" in prompt.lower():
                    response = "For component analysis, upload your engineering documentation and system architecture files. I can identify hardware and software components, their relationships, and potential failure points."
                elif "troubleshoot" in prompt.lower():
                    response = "Upload your troubleshooting guides with images and diagrams. I can process multi-modal content to extract step-by-step procedures and visual references for repair guidance."
                else:
                    response = f"I understand you're asking about: '{prompt}'. In the full version, I would analyze your uploaded files and provide specific guidance. For now, please use the Quick Actions buttons above to see simulated diagnosis capabilities."
                
                st.markdown(f"🤖 **Demo Response**: {response}")
                
                st.info("💡 **Note**: This is a simulated response. The full system would provide real AI-powered analysis using Amazon Nova models.")

if __name__ == "__main__":
    main()