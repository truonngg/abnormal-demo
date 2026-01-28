"""Streamlit frontend for AI-Enhanced Incident Communications Assistant."""
import streamlit as st
import requests
import json
from datetime import datetime
from components.upload import render_upload_section
from components.display import render_results_section
from components.sidebar import render_sidebar

# Page configuration
st.set_page_config(
    page_title="Incident Communications Assistant | Abnormal Security",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for Abnormal AI color scheme
st.markdown("""
    <style>
    /* Abnormal AI Brand Colors */
    :root {
        --abnormal-teal: #5DD9C1;
        --abnormal-dark: #1a1a1a;
        --abnormal-bg-main: #1a1a1a;
        --abnormal-text-main: #ffffff;
        --abnormal-bg-sidebar: #f8f8f8;
        --abnormal-text-sidebar: #1a1a1a;
    }
    
    /* Main container background - DARK */
    .main {
        background-color: var(--abnormal-bg-main) !important;
        color: var(--abnormal-text-main) !important;
    }
    
    .main .block-container {
        background-color: var(--abnormal-bg-main) !important;
    }
    
    /* Headers - WHITE TEXT */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #ffffff !important;
        margin-bottom: 1.5rem;
    }
    
    /* Primary button styling (Generate Draft) */
    .stButton > button[kind="primary"] {
        background-color: var(--abnormal-teal) !important;
        color: var(--abnormal-dark) !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.75rem 1.5rem !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #4bc4ad !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(93, 217, 193, 0.3) !important;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 0.25rem;
        font-weight: 600;
        font-size: 0.875rem;
    }
    .status-investigating {
        background-color: #5DD9C1;
        color: var(--abnormal-dark);
    }
    
    /* Cards and containers */
    .stContainer {
        background-color: var(--abnormal-bg);
    }
    
    /* Success messages - DARK THEME */
    .stSuccess {
        background-color: rgba(93, 217, 193, 0.2) !important;
        color: #ffffff !important;
        border: 1px solid rgba(93, 217, 193, 0.6) !important;
    }
    
    /* Warning messages - DARK THEME */
    .stWarning {
        background-color: rgba(255, 184, 77, 0.2) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 184, 77, 0.6) !important;
    }
    
    /* Error messages - DARK THEME */
    .stError {
        background-color: rgba(255, 107, 107, 0.2) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 107, 107, 0.6) !important;
    }
    
    /* Dividers - DARK THEME */
    hr {
        border-color: #444 !important;
    }
    
    /* Subheaders - WHITE TEXT */
    .main h2, .main h3, .main h1 {
        color: #ffffff !important;
    }
    
    /* Hide ALL header anchor links (copy/paste icons) */
    .main h1 a, .main h2 a, .main h3 a, .main h4 a, .main h5 a, .main h6 a,
    .main h1 .anchor-link, .main h2 .anchor-link, .main h3 .anchor-link,
    .main h1 > a, .main h2 > a, .main h3 > a {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }
    
    .main .stMarkdown h1 > a,
    .main .stMarkdown h2 > a,
    .main .stMarkdown h3 > a,
    .main .stMarkdown h4 > a,
    .main .stMarkdown h5 > a,
    .main .stMarkdown h6 > a {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Target Streamlit's header anchor specifically */
    [data-testid="stMarkdownContainer"] h1 a,
    [data-testid="stMarkdownContainer"] h2 a,
    [data-testid="stMarkdownContainer"] h3 a {
        display: none !important;
    }
    
    /* Hide link icon SVG in headers */
    .main h1 svg, .main h2 svg, .main h3 svg {
        display: none !important;
    }
    
    /* Sidebar styling - LIGHT with BLACK TEXT */
    [data-testid="stSidebar"] {
        background-color: var(--abnormal-bg-sidebar) !important;
        max-width: 280px !important;
        min-width: 280px !important;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        width: 280px !important;
        background-color: var(--abnormal-bg-sidebar) !important;
    }
    
    /* Sidebar text - force black */
    [data-testid="stSidebar"] * {
        color: var(--abnormal-text-sidebar) !important;
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown {
        color: var(--abnormal-text-sidebar) !important;
    }
    
    /* Sidebar input fields */
    [data-testid="stSidebar"] input {
        color: #1a1a1a !important;
        background-color: #ffffff !important;
    }
    
    /* Sidebar collapse arrow - force black at ALL times regardless of hover state */
    [data-testid="collapsedControl"],
    [data-testid="collapsedControl"]:hover,
    [data-testid="collapsedControl"]:active,
    [data-testid="collapsedControl"]:focus,
    section[data-testid="stSidebar"]:hover [data-testid="collapsedControl"],
    section:not(:hover) [data-testid="collapsedControl"] {
        color: #1a1a1a !important;
        background-color: transparent !important;
        opacity: 1 !important;
        visibility: visible !important;
    }
    
    [data-testid="collapsedControl"] svg,
    [data-testid="collapsedControl"]:hover svg,
    [data-testid="collapsedControl"]:active svg,
    [data-testid="collapsedControl"]:focus svg,
    section[data-testid="stSidebar"]:hover [data-testid="collapsedControl"] svg,
    section:not(:hover) [data-testid="collapsedControl"] svg {
        color: #1a1a1a !important;
        fill: #1a1a1a !important;
        stroke: #1a1a1a !important;
        opacity: 1 !important;
    }
    
    [data-testid="collapsedControl"] path,
    [data-testid="collapsedControl"] svg path {
        fill: #1a1a1a !important;
        stroke: #1a1a1a !important;
    }
    
    /* Sidebar toggle button - force black in ALL states */
    button[kind="header"],
    button[kind="header"]:hover,
    button[kind="header"]:active,
    button[kind="header"]:focus,
    section[data-testid="stSidebar"]:hover button[kind="header"],
    section:not(:hover) button[kind="header"] {
        color: #1a1a1a !important;
        opacity: 1 !important;
        visibility: visible !important;
    }
    
    button[kind="header"] svg,
    button[kind="header"]:hover svg,
    section[data-testid="stSidebar"]:hover button[kind="header"] svg,
    section:not(:hover) button[kind="header"] svg {
        color: #1a1a1a !important;
        fill: #1a1a1a !important;
        opacity: 1 !important;
    }
    
    /* Override any inherited styles that might change color */
    .main [data-testid="collapsedControl"],
    .main [data-testid="collapsedControl"] * {
        color: #1a1a1a !important;
        fill: #1a1a1a !important;
    }
    
    /* File uploader - DARK THEME */
    [data-testid="stFileUploader"] {
        background-color: #2a2a2a !important;
        border: 2px dashed #5DD9C1 !important;
        border-radius: 8px;
        padding: 1rem;
    }
    
    [data-testid="stFileUploader"] label,
    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] small {
        color: #ffffff !important;
    }
    
    [data-testid="stFileUploader"] section {
        border-color: #5DD9C1 !important;
    }
    
    [data-testid="stFileUploader"] button {
        color: #1a1a1a !important;
        background-color: #5DD9C1 !important;
    }
    
    /* Metrics - DARK THEME */
    [data-testid="stMetric"] {
        background-color: #2a2a2a !important;
        padding: 1rem;
        border-radius: 8px;
    }
    
    [data-testid="stMetric"] label,
    [data-testid="stMetric"] div {
        color: #ffffff !important;
    }
    
    /* Info boxes - DARK THEME */
    .stInfo {
        background-color: rgba(93, 217, 193, 0.2) !important;
        border-left: 4px solid var(--abnormal-teal) !important;
        color: #ffffff !important;
    }
    
    /* Text inputs and text areas - DARK THEME */
    .main .stTextInput input, 
    .main .stTextArea textarea {
        color: #ffffff !important;
        background-color: #2a2a2a !important;
        border: 1px solid #444 !important;
    }
    
    /* Labels and captions - WHITE TEXT in main */
    .main label, 
    .main .stCaption,
    .main p {
        color: #cccccc !important;
    }
    
    /* Expanders - DARK THEME */
    .main .streamlit-expanderHeader {
        color: #ffffff !important;
        font-weight: 500 !important;
        background-color: #2a2a2a !important;
    }
    
    .main .streamlit-expander {
        background-color: #2a2a2a !important;
        border: 1px solid #444 !important;
    }
    
    /* Code blocks - DARK THEME */
    .main code {
        color: #5DD9C1 !important;
        background-color: #2a2a2a !important;
    }
    
    /* Markdown text - WHITE */
    .main .stMarkdown {
        color: #ffffff !important;
    }
    
    /* List items - WHITE */
    .main li {
        color: #cccccc !important;
    }
    
    /* Secondary buttons - DARK THEME */
    .main .stButton > button:not([kind="primary"]) {
        background-color: #2a2a2a !important;
        color: #ffffff !important;
        border: 1px solid #5DD9C1 !important;
    }
    
    .main .stButton > button:not([kind="primary"]):hover {
        background-color: #3a3a3a !important;
        border-color: #5DD9C1 !important;
    }
    
    /* Copy button - make it prominent */
    button[data-testid="baseButton-primary"]:has-text("COPY"),
    button:contains("COPY") {
        font-size: 1rem !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 700 !important;
    }
    
    /* JSON viewer - DARK THEME */
    .main pre {
        background-color: #2a2a2a !important;
        color: #e0e0e0 !important;
        border: 1px solid #444 !important;
    }
    </style>
    
    <script>
    // Force sidebar arrow to stay black
    (function() {
        function forceArrowBlack() {
            // Find the collapse/expand button
            const arrowButton = document.querySelector('[data-testid="collapsedControl"]') || 
                               document.querySelector('button[kind="header"]') ||
                               document.querySelector('section button[aria-label*="Collapse"]') ||
                               document.querySelector('section button[aria-label*="Expand"]');
            
            if (arrowButton) {
                // Force color on button and all its children
                arrowButton.style.setProperty('color', '#000000', 'important');
                
                // Find and force SVG color
                const svg = arrowButton.querySelector('svg');
                if (svg) {
                    svg.style.setProperty('color', '#000000', 'important');
                    svg.style.setProperty('fill', '#000000', 'important');
                    
                    // Also force all paths inside SVG
                    const paths = svg.querySelectorAll('path, circle, rect, line, polyline, polygon');
                    paths.forEach(el => {
                        el.style.setProperty('fill', '#000000', 'important');
                        el.style.setProperty('stroke', '#000000', 'important');
                    });
                }
            }
        }
        
        // Run multiple times to catch Streamlit's re-renders
        setTimeout(forceArrowBlack, 100);
        setTimeout(forceArrowBlack, 500);
        setTimeout(forceArrowBlack, 1000);
        setTimeout(forceArrowBlack, 2000);
        
        // Also run on any DOM changes
        const observer = new MutationObserver(forceArrowBlack);
        observer.observe(document.body, { childList: true, subtree: true });
    })();
    </script>
""", unsafe_allow_html=True)


def main():
    """Main application entry point."""
    
    # Render sidebar
    backend_url = render_sidebar()
    
    # Main header
    st.markdown('<div class="main-header">Incident Communications Assistant</div>', unsafe_allow_html=True)
    
    # Check backend health (silently, show error only if fails)
    try:
        health_response = requests.get(f"{backend_url}/health", timeout=2)
        if health_response.status_code != 200:
            st.error(f"⚠️ Backend health check failed: {health_response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Cannot connect to backend at {backend_url}. Make sure the FastAPI server is running.")
        st.info("Start the backend with: `uvicorn backend.main:app --reload --port 8000`")
        return
    
    st.divider()
    
    # Phase selection section
    st.markdown('<h2 style="color: #ffffff;">🎯 Select Incident Phase</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color: #cccccc; margin-bottom: 1rem;">Choose the current phase of your incident. This prototype supports Investigating and Identified phases.</p>', unsafe_allow_html=True)
    
    phase_options = {
        "🔍 Investigating": "investigating",
        "✅ Identified": "identified"
    }
    
    phase_descriptions = {
        "investigating": "We are aware of the issue and working to identify the cause",
        "identified": "We know what's wrong and are implementing a fix"
    }
    
    selected_phase_label = st.radio(
        "Incident Phase",
        options=list(phase_options.keys()),
        index=0,
        horizontal=True,
        label_visibility="collapsed"
    )
    
    selected_phase = phase_options[selected_phase_label]
    st.info(f"**{selected_phase_label}**: {phase_descriptions[selected_phase]}")
    
    st.divider()
    
    # File upload section
    st.markdown('<h2 style="color: #ffffff;">📁 Upload Incident Data</h2>', unsafe_allow_html=True)
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0
    uploaded_files = render_upload_section(f"incident_files_{st.session_state.uploader_key}")
    
    st.divider()
    
    # Action buttons
    col1, col2 = st.columns([4, 1])
    with col1:
        generate_button = st.button("🤖 Generate Draft", type="primary", use_container_width=True)
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.draft_result = None
            st.session_state.incident_title = None
            st.session_state.uploader_key += 1
            st.success("Cache cleared!")
            st.rerun()
    
    # Initialize session state for results and title persistence
    if "draft_result" not in st.session_state:
        st.session_state.draft_result = None
    if "incident_title" not in st.session_state:
        st.session_state.incident_title = None
    
    # Handle "Generate Draft" button
    if generate_button:
        if not uploaded_files:
            st.warning("Please upload at least one incident data file.")
        else:
            with st.spinner("Generating status update draft... This may take 2-3 minutes."):
                try:
                    # Prepare incident data payload
                    incident_data = prepare_incident_data(uploaded_files, selected_phase)
                    
                    # Call generate endpoint
                    response = requests.post(
                        f"{backend_url}/api/generate-draft",
                        json=incident_data,
                        timeout=300
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        # IMPORTANT: Force refresh by clearing and resetting
                        st.session_state.draft_result = None  # Clear first
                        # Persist title from Investigating phase for reuse in later phases
                        if selected_phase == "investigating":
                            st.session_state.incident_title = result.get("title")
                        elif st.session_state.incident_title:
                            result["title"] = st.session_state.incident_title
                        st.session_state.draft_result = result  # Set new result
                        st.success("✅ Draft generated successfully!")
                        st.rerun()  # Force reload to display fresh data
                    else:
                        st.error(f"Error generating draft: {response.text}")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    st.divider()
    
    # Display draft results
    if st.session_state.draft_result:
        st.markdown('<h2 style="color: #ffffff;">📝 Generated Draft</h2>', unsafe_allow_html=True)
        render_results_section(st.session_state.draft_result)


def prepare_incident_data(uploaded_files, phase):
    """Prepare incident data payload from uploaded files.
    
    This function dynamically handles ANY file type by:
    1. Converting filename to a clean field name (e.g., "aws_logs.json" -> "aws_logs")
    2. Parsing JSON files automatically
    3. Passing text files as-is
    """
    incident_data = {
        "phase": phase
    }
    
    for file_name, file_content in uploaded_files.items():
        # Create a clean field name from the filename
        # e.g., "aws_outage_pagerduty.json" -> "aws_outage_pagerduty"
        # e.g., "slack_thread.txt" -> "slack_thread"
        field_name = file_name.rsplit('.', 1)[0]  # Remove extension
        field_name = field_name.replace('-', '_').replace(' ', '_')  # Normalize to snake_case
        
        # Parse JSON files, keep text files as-is
        if file_name.endswith('.json'):
            try:
                incident_data[field_name] = json.loads(file_content)
            except json.JSONDecodeError as e:
                st.error(f"Failed to parse JSON file {file_name}: {e}")
                continue
        else:
            # Text file (or any other format)
            incident_data[field_name] = file_content
    
    return incident_data


if __name__ == "__main__":
    main()
