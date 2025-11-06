import sys
import streamlit as st
from .auth import AuthManager
from .chat import ChatManager
from .styles import apply_custom_styles


def main():
    """Main application entry point"""
    # Parse command line arguments
    agent_name = "default"
    if len(sys.argv) > 1:
        for arg in sys.argv:
            if arg.startswith("--agent="):
                agent_name = arg.split("=")[1]

    # Configure page
    st.set_page_config(layout="wide")

    # Apply custom styles
    apply_custom_styles()

    # Initialize managers
    auth_manager = AuthManager()
    chat_manager = ChatManager(agent_name)

    # Handle OAuth callback
    auth_manager.handle_oauth_callback()

    # Check authentication status
    if auth_manager.is_authenticated():
        # Authenticated user interface
        render_authenticated_interface(auth_manager, chat_manager)
    else:
        # Login interface
        render_login_interface(auth_manager)


def render_authenticated_interface(
    auth_manager: AuthManager, chat_manager: ChatManager
):
    """Render the interface for authenticated users"""
    # Sidebar
    st.sidebar.title("Access Tokens")
    st.sidebar.code(auth_manager.cookies.get("tokens"))

    if st.sidebar.button("Logout"):
        auth_manager.logout()

    st.sidebar.write("Agent Arn")
    st.sidebar.code(st.session_state["agent_arn"])

    st.sidebar.write("Session Id")
    st.sidebar.code(st.session_state["session_id"])

    # Main content
    st.title("🔧 Instrument Diagnosis Assistant")
    st.markdown(
        """
        <hr style='border:1px solid #298dff;'>
        """,
        unsafe_allow_html=True,
    )
    
    # Add file upload section for OAuth version
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
                key="oauth_gold_logs",
                help="Upload logs from properly functioning instruments"
            )
        
        with col2:
            failed_unit_logs = st.file_uploader(
                "Failed Unit Logs",
                type=['txt', 'log', 'csv'],
                accept_multiple_files=True,
                key="oauth_failed_logs",
                help="Upload logs from instruments experiencing issues"
            )
    
    with tab2:
        st.markdown("**Upload engineering documentation and component specifications**")
        engineering_docs = st.file_uploader(
            "Engineering Documents",
            type=['pdf', 'doc', 'docx', 'txt', 'md'],
            accept_multiple_files=True,
            key="oauth_eng_docs",
            help="Upload component specifications, system architecture docs, etc."
        )
    
    with tab3:
        st.markdown("**Upload troubleshooting guides with images and diagrams**")
        troubleshooting_guides = st.file_uploader(
            "Troubleshooting Guides",
            type=['pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            key="oauth_trouble_guides",
            help="Upload multi-modal troubleshooting documentation"
        )
    
    # Store uploaded files in session state
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = {
            'gold_logs': [],
            'failed_logs': [],
            'eng_docs': [],
            'trouble_guides': []
        }
    
    # Update session state with uploaded files
    if gold_standard_logs:
        st.session_state.uploaded_files['gold_logs'] = gold_standard_logs
    if failed_unit_logs:
        st.session_state.uploaded_files['failed_logs'] = failed_unit_logs
    if engineering_docs:
        st.session_state.uploaded_files['eng_docs'] = engineering_docs
    if troubleshooting_guides:
        st.session_state.uploaded_files['trouble_guides'] = troubleshooting_guides
    
    # Show file summary if files are uploaded
    total_files = sum(len(files) for files in st.session_state.uploaded_files.values())
    if total_files > 0:
        st.success(f"✅ {total_files} files uploaded and ready for analysis")
    
    st.divider()

    # Get user info and tokens
    tokens = auth_manager.get_tokens()
    user_claims = auth_manager.get_user_claims()

    
    # Display chat history
    chat_manager.display_chat_history()

    # Quick action buttons for OAuth version
    st.markdown("### 🚀 Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔍 Analyze Logs", key="oauth_analyze"):
            prompt = "Please analyze the uploaded log files. Compare failed unit logs against gold standard patterns and provide diagnosis."
            chat_manager.process_user_message(prompt, user_claims, tokens["access_token"])
    
    with col2:
        if st.button("🔧 Identify Components", key="oauth_components"):
            prompt = "Please identify all hardware and software components from the uploaded engineering documentation."
            chat_manager.process_user_message(prompt, user_claims, tokens["access_token"])
    
    with col3:
        if st.button("📚 Process Guides", key="oauth_guides"):
            prompt = "Please process the uploaded troubleshooting guides and extract relevant procedures with visual analysis."
            chat_manager.process_user_message(prompt, user_claims, tokens["access_token"])
    
    with col4:
        if st.button("🎯 Full Diagnosis", key="oauth_diagnosis"):
            prompt = "Please perform a comprehensive instrument diagnosis using all uploaded files. Provide pass/fail determination with detailed analysis."
            chat_manager.process_user_message(prompt, user_claims, tokens["access_token"])

    # Chat input
    if prompt := st.chat_input("Ask about instrument diagnosis, upload files, or request specific analysis..."):
        chat_manager.process_user_message(prompt, user_claims, tokens["access_token"])


def render_login_interface(auth_manager: AuthManager):
    """Render the login interface"""
    login_url = auth_manager.get_login_url()
    st.markdown(
        f'<meta http-equiv="refresh" content="0;url={login_url}">',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
