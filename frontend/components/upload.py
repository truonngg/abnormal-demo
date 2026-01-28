"""File upload component."""
import streamlit as st


def render_upload_section(uploader_key=None):
    """
    Render file upload interface with drag-and-drop support.
    
    Returns:
        Dictionary of {filename: content} for uploaded files
    """
    st.markdown("""
    <div style="color: #e0e0e0; line-height: 1.6; margin-bottom: 1rem;">
    Upload <strong>any</strong> incident data files. The system automatically processes all uploaded files regardless of their source or naming.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="color: #cccccc; margin-bottom: 1rem;">
    <strong>Common examples:</strong><br>
    • <code style="color: #5DD9C1; background: #2a2a2a; padding: 0.1rem 0.3rem; border-radius: 0.25rem;">*.txt</code> - Slack threads, incident notes, context files<br>
    • <code style="color: #5DD9C1; background: #2a2a2a; padding: 0.1rem 0.3rem; border-radius: 0.25rem;">*logs*.json</code> - CloudWatch, Datadog, Splunk, application logs<br>
    • <code style="color: #5DD9C1; background: #2a2a2a; padding: 0.1rem 0.3rem; border-radius: 0.25rem;">*metrics*.json</code> - Prometheus, Grafana, New Relic metrics<br>
    • <code style="color: #5DD9C1; background: #2a2a2a; padding: 0.1rem 0.3rem; border-radius: 0.25rem;">*incident*.json</code> - PagerDuty, Opsgenie, VictorOps incidents<br>
    • <code style="color: #5DD9C1; background: #2a2a2a; padding: 0.1rem 0.3rem; border-radius: 0.25rem;">*deploy*.json</code> - GitHub, GitLab, Jenkins deployments
    </div>
    <div style="color: #aaaaaa; font-size: 0.9rem; margin-bottom: 1.5rem;">
    💡 The AI will intelligently extract relevant information from any structured or unstructured data you provide.
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_files = {}
    
    # File uploader with multiple file support - accepts ANY file type
    files = st.file_uploader(
        "Choose incident data files",
        type=["json", "txt", "log", "yaml", "yml", "csv", "xml", "md"],
        accept_multiple_files=True,
        help="Upload any incident data files - JSON, text, logs, YAML, CSV, etc.",
        key=uploader_key
    )
    
    if files:
        for uploaded_file in files:
            # Read file content
            content = uploaded_file.read().decode("utf-8")
            uploaded_files[uploaded_file.name] = content
            
        # Display uploaded files
        st.success(f"✅ Uploaded {len(uploaded_files)} file(s)")
    
    return uploaded_files
