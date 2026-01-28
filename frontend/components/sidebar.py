"""Sidebar configuration component."""
import streamlit as st
import os


def render_sidebar():
    """
    Render the sidebar with configuration options.
    
    Returns:
        str: Backend API URL (from environment variable)
    """
    with st.sidebar:
        # Help section
        st.subheader("📚 Quick Guide")
        st.markdown("""
        <div style="color: #1a1a1a; line-height: 1.8;">
        <strong>Step 1:</strong> Upload incident data files<br><br>
        <strong>Step 2:</strong> Click "Generate Draft" to create a status update<br><br>
        <strong>Step 3:</strong> Review the draft, evidence, and quality scores<br><br>
        <strong>Step 4:</strong> Copy and post to your status page
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # About section
        st.subheader("ℹ️ About")
        st.caption("Version: 0.1.0 (MVP)")
        st.caption("AI-Enhanced Incident Communications")
        
        # Links
        st.write("")
        st.markdown("📖 [View Documentation](https://github.com)")
    
    # Return backend URL from environment variable
    return os.getenv("BACKEND_URL", "http://localhost:8000")
