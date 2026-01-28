"""Results display component with comprehensive transparency and evaluation features."""
import streamlit as st
import streamlit.components.v1 as components
from typing import List, Dict, Any
import html
import re


def _clean_text(value: Any) -> str:
    """
    Clean text by removing all HTML tags and escaping for safe display.
    
    Steps:
    1. Convert to string
    2. Unescape any HTML entities
    3. Strip all HTML tags
    4. Escape for safe insertion into HTML
    """
    if value is None:
        return ""
    
    text = str(value)
    
    # Unescape any HTML entities first
    text = html.unescape(text)
    
    # Remove ALL HTML tags (handles nested tags properly)
    text = re.sub(r'<[^>]+>', '', text)
    
    # Clean up any leftover angle brackets
    text = text.replace('<', '').replace('>', '')
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Escape for safe HTML insertion
    text = html.escape(text)
    
    return text


def _sanitize_text(value: Any) -> str:
    """Strip HTML tags/entities and return safe HTML text."""
    if value is None:
        return ""
    text = str(value)
    # Normalize any already-escaped HTML entities (handle double-escaped).
    for _ in range(3):
        unescaped = html.unescape(text)
        if unescaped == text:
            break
        text = unescaped
    # Remove fenced code blocks to avoid markdown code rendering.
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Remove any HTML tags the model might have returned.
    # Run multiple times to handle nested tags
    prev_text = None
    while prev_text != text:
        prev_text = text
        text = re.sub(r"<[^>]+>", "", text)
    # Remove any leftover angle brackets from malformed tags.
    text = text.replace("<", "").replace(">", "")
    # Normalize whitespace and trim.
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    # Escape again for safe rendering inside HTML.
    text = html.escape(text)
    return text.replace("\n", "<br>")


def render_results_section(draft_result):
    """
    Render the generated draft with quality metrics and evidence.
    
    Args:
        draft_result: DraftResponse object from the API
    """
    # Display confidence level badge
    confidence_level = draft_result.get("confidence_level", "Medium")
    confidence_score = draft_result.get("confidence_score", 0.0)
    
    # Use colored badges instead of emojis
    badge_colors = {
        "High": "#5DD9C1",
        "Medium": "#FFB84D",
        "Low": "#FF6B6B"
    }
    badge_color = badge_colors.get(confidence_level, "#999")
    
    st.markdown(f"""
        <div style="margin-bottom: 1rem;">
            <span style="font-size: 1.25rem; font-weight: 700; color: #ffffff;">Overall Quality Score: </span>
            <span style="
                background-color: {badge_color};
                color: #1a1a1a;
                padding: 0.25rem 0.75rem;
                border-radius: 0.25rem;
                font-weight: 600;
                font-size: 1rem;
            ">{confidence_level}</span>
            <span style="font-size: 1rem; color: #cccccc; margin-left: 0.5rem;">({confidence_score:.2f})</span>
        </div>
        <div style="color: #aaaaaa; font-size: 0.85rem; margin-bottom: 1.5rem; margin-top: -0.5rem;">
            Based on LLM-as-Judge evaluation across 5 quality dimensions
        </div>
    """, unsafe_allow_html=True)
    
    # Display warnings if any
    warnings = draft_result.get("warnings", [])
    if warnings:
        warnings_text = "<br>".join([f"• {html.escape(str(w))}" for w in warnings])
        st.markdown(f"""
            <div style="
                background-color: rgba(255, 184, 77, 0.2);
                border: 1px solid rgba(255, 184, 77, 0.6);
                border-radius: 0.5rem;
                padding: 1rem;
                margin-bottom: 1rem;
            ">
                <div style="color: #ffffff; font-weight: 600; margin-bottom: 0.5rem;">⚠️ Warnings:</div>
                <div style="color: #e0e0e0; line-height: 1.6;">{warnings_text}</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Data sources used badges
    data_sources = draft_result.get("data_sources_used", [])
    if data_sources:
        render_data_sources_badges(data_sources)
    
    st.write("---")
    
    # Draft preview in a nice card
    st.markdown('<h3 style="color: #ffffff;">📄 Status Update Draft</h3>', unsafe_allow_html=True)
    
    # Get draft values
    draft_title_raw = draft_result.get('title', 'Untitled')
    draft_status_raw = draft_result.get('status', 'Unknown')
    draft_message_raw = draft_result.get('message', '')
    draft_next_update_raw = draft_result.get('next_update', 'TBD')
    
    # Prepare the full draft text for copying and display
    full_draft_text = f"""Title: {draft_title_raw}
Status: {draft_status_raw}

{draft_message_raw}

Next update: {draft_next_update_raw}"""
    
    # Escaped versions for HTML display
    draft_title = html.escape(str(draft_title_raw))
    draft_status = html.escape(str(draft_status_raw))
    draft_message = html.escape(str(draft_message_raw)).replace('\n', '<br>')
    draft_next_update = html.escape(str(draft_next_update_raw))
    
    # Single unified card with all content
    st.markdown(f"""
        <div style="
            background-color: #2a2a2a;
            padding: 2rem;
            border-radius: 0.75rem;
            border: 2px solid #444;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            margin-bottom: 1.5rem;
        ">
            <div style="font-size: 1.5rem; font-weight: 700; color: #ffffff; margin-bottom: 0.75rem;">
                {draft_title}
            </div>
            <div style="margin-bottom: 1rem;">
                <span class="status-badge status-investigating">{draft_status}</span>
            </div>
            <div style="font-size: 1rem; line-height: 1.6; color: #e0e0e0; margin-bottom: 1.5rem;">
                {draft_message}
            </div>
            <div style="
                background-color: rgba(93, 217, 193, 0.2);
                padding: 0.75rem 1rem;
                border-radius: 0.5rem;
                border-left: 4px solid #5DD9C1;
                margin-bottom: 1.5rem;
            ">
                <span style="color: #ffffff; font-weight: 600;">⏰ Next update:</span>
                <span style="color: #e0e0e0; font-weight: 500;"> {draft_next_update}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Prominent copy area below the card
    st.write("")  # Add spacing
    
    st.markdown('<p style="color: #aaaaaa; font-size: 0.9rem; margin-bottom: 0.5rem;">📋 Copy the draft below:</p>', unsafe_allow_html=True)
    
    # Use Streamlit's code block with built-in copy button to avoid iframe overlay
    st.code(full_draft_text, language="text")
    
    st.write("---")
    
    # Tabbed interface for detailed information
    st.markdown('<h2 style="color: #ffffff;">📊 Detailed Analysis & Evidence</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🔍 Extracted Evidence", "✅ Quality Evaluation", "🔗 Evidence Mappings"])
    
    with tab1:
        # Extracted Evidence Section
        evidence_summary = draft_result.get("extracted_evidence_summary", {})
        if evidence_summary:
            render_extracted_evidence(evidence_summary)
        else:
            st.info("No extracted evidence available")
    
    with tab2:
        # Quality Evaluation Section (Deterministic + LLM Judge)
        evaluation_result = draft_result.get("evaluation_result", {})
        if evaluation_result:
            # Deterministic checks
            st.markdown('<h3 style="color: #ffffff;">Deterministic Quality Checks</h3>', unsafe_allow_html=True)
            deterministic_checks = evaluation_result.get("deterministic_checks", [])
            if deterministic_checks:
                render_deterministic_checks(deterministic_checks)
            else:
                st.info("No deterministic checks available")
            
            st.write("")
            st.write("---")
            st.write("")
            
            # LLM-as-Judge evaluation
            st.markdown('<h3 style="color: #ffffff;">LLM-as-Judge Evaluation</h3>', unsafe_allow_html=True)
            llm_judge_result = evaluation_result.get("llm_judge_result", {})
            if llm_judge_result and llm_judge_result.get("dimensions"):
                render_llm_judge_dimensions(llm_judge_result)
            else:
                st.info("No LLM-as-Judge evaluation available")
        else:
            st.info("No evaluation results available")
    
    with tab3:
        # Evidence Mappings Section
        evidence_mappings = draft_result.get("evidence_mappings", [])
        if evidence_mappings:
            render_evidence_mappings(evidence_mappings)
        else:
            st.info("No evidence mappings available")
    
    st.write("---")
    
    # Expandable section for full response
    with st.expander("🔧 View Full API Response"):
        st.markdown('<div style="color: #ffffff;">', unsafe_allow_html=True)
        st.json(draft_result)
        st.markdown('</div>', unsafe_allow_html=True)


def render_data_sources_badges(sources: List[str]):
    """
    Display data source badges showing which sources contributed to the draft.
    
    Args:
        sources: List of data source names
    """
    st.markdown('<h3 style="color: #ffffff; margin-top: 1rem;">📦 Data Sources Used</h3>', unsafe_allow_html=True)
    
    # Define colors for different source types
    source_colors = {
        "PagerDuty": "#06AC38",
        "Incident Context": "#5DD9C1",
        "CloudWatch Logs": "#FF9900",
        "Prometheus Metrics": "#E6522C",
        "GitHub Deployments": "#24292E"
    }
    
    badges_html = ""
    for source in sources:
        color = source_colors.get(source, "#666666")
        source_escaped = html.escape(str(source))
        badges_html += f"""
            <span style="
                display: inline-block;
                background-color: {color};
                color: #ffffff;
                padding: 0.4rem 0.8rem;
                border-radius: 0.25rem;
                font-weight: 600;
                font-size: 0.85rem;
                margin-right: 0.5rem;
                margin-bottom: 0.5rem;
            ">{source_escaped}</span>
        """
    
    st.markdown(f"""
        <div style="margin-bottom: 1rem;">
            {badges_html}
        </div>
    """, unsafe_allow_html=True)


def render_extracted_evidence(evidence_summary: Dict[str, Any]):
    """
    Render comprehensive extracted evidence section.
    
    Args:
        evidence_summary: Extracted evidence summary from the API
    """
    # Incident Metadata
    st.markdown('<h4 style="color: #ffffff;">📋 Incident Metadata</h4>', unsafe_allow_html=True)
    
    incident_metadata = evidence_summary.get("incident_metadata", {})
    
    # Escape HTML in metadata fields
    title_escaped = html.escape(str(incident_metadata.get('title', 'N/A')))
    affected_service_escaped = html.escape(str(incident_metadata.get('affected_service', 'N/A')))
    severity_escaped = html.escape(str(incident_metadata.get('severity', 'N/A')))
    start_time_escaped = html.escape(str(incident_metadata.get('start_time', 'N/A')))
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
            <div style="background-color: #2a2a2a; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; border: 1px solid #444;">
                <div style="color: #aaaaaa; font-size: 0.8rem; margin-bottom: 0.25rem;">Title</div>
                <div style="color: #ffffff; font-weight: 600;">{title_escaped}</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div style="background-color: #2a2a2a; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; border: 1px solid #444;">
                <div style="color: #aaaaaa; font-size: 0.8rem; margin-bottom: 0.25rem;">Affected Service</div>
                <div style="color: #ffffff; font-weight: 600;">{affected_service_escaped}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div style="background-color: #2a2a2a; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; border: 1px solid #444;">
                <div style="color: #aaaaaa; font-size: 0.8rem; margin-bottom: 0.25rem;">Severity</div>
                <div style="color: #ffffff; font-weight: 600;">{severity_escaped}</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div style="background-color: #2a2a2a; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; border: 1px solid #444;">
                <div style="color: #aaaaaa; font-size: 0.8rem; margin-bottom: 0.25rem;">Start Time</div>
                <div style="color: #ffffff; font-weight: 600;">{start_time_escaped}</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.write("")
    
    # Customer Symptoms
    st.markdown('<h4 style="color: #ffffff;">🚨 Customer Symptoms</h4>', unsafe_allow_html=True)
    
    customer_symptoms = evidence_summary.get("customer_symptoms", [])
    if customer_symptoms:
        for symptom_data in customer_symptoms:
            symptom = symptom_data.get("symptom", "Unknown symptom")
            confidence = symptom_data.get("confidence", "unknown")
            evidence_sources = symptom_data.get("evidence_sources", [])
            
            # Color code confidence
            confidence_colors = {
                "high": "#5DD9C1",
                "medium": "#FFB84D",
                "low": "#FF6B6B"
            }
            conf_color = confidence_colors.get(confidence.lower(), "#999")
            
            # Escape HTML in dynamic content
            symptom_escaped = html.escape(str(symptom))
            sources_text = "<br>".join([f"  • {html.escape(str(src))}" for src in evidence_sources]) if evidence_sources else "No sources"
            
            st.markdown(f"""
                <div style="
                    background-color: #2a2a2a;
                    padding: 1rem;
                    border-radius: 0.5rem;
                    border-left: 4px solid {conf_color};
                    margin-bottom: 1rem;
                    border: 1px solid #444;
                ">
                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                        <div style="color: #ffffff; font-weight: 600; flex: 1;">{symptom_escaped}</div>
                        <span style="
                            background-color: {conf_color};
                            color: #1a1a1a;
                            padding: 0.2rem 0.6rem;
                            border-radius: 0.25rem;
                            font-weight: 600;
                            font-size: 0.75rem;
                            text-transform: uppercase;
                        ">{confidence}</span>
                    </div>
                    <div style="color: #aaaaaa; font-size: 0.85rem; margin-top: 0.5rem;">
                        <strong>Evidence Sources:</strong><br>
                        {sources_text}
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No customer symptoms extracted")
    
    st.write("")
    
    # Investigation Status
    st.markdown('<h4 style="color: #ffffff;">🔍 Investigation Status</h4>', unsafe_allow_html=True)
    
    root_cause_identified = evidence_summary.get("root_cause_identified", False)
    diagnosis = evidence_summary.get("diagnosis", "Not yet identified")
    mitigation = evidence_summary.get("mitigation_action", "Investigating")
    
    # Root cause badge
    rc_color = "#5DD9C1" if root_cause_identified else "#FF6B6B"
    rc_text = "YES" if root_cause_identified else "NO"
    
    # Escape HTML in dynamic content and handle newlines
    diagnosis_escaped = html.escape(str(diagnosis)).replace('\n', '<br>') if diagnosis else "Not yet identified"
    mitigation_escaped = html.escape(str(mitigation)).replace('\n', '<br>') if mitigation else "Investigating"
    
    st.markdown(f"""
        <div style="background-color: #2a2a2a; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; border: 1px solid #444;">
            <div style="margin-bottom: 0.75rem;">
                <span style="color: #aaaaaa; font-size: 0.85rem;">Root Cause Identified: </span>
                <span style="
                    background-color: {rc_color};
                    color: #1a1a1a;
                    padding: 0.2rem 0.6rem;
                    border-radius: 0.25rem;
                    font-weight: 600;
                    font-size: 0.75rem;
                ">{rc_text}</span>
            </div>
            <div style="margin-bottom: 0.75rem;">
                <div style="color: #aaaaaa; font-size: 0.85rem; margin-bottom: 0.25rem;">Diagnosis:</div>
                <div style="color: #e0e0e0;">{diagnosis_escaped}</div>
            </div>
            <div>
                <div style="color: #aaaaaa; font-size: 0.85rem; margin-bottom: 0.25rem;">Mitigation Action:</div>
                <div style="color: #e0e0e0;">{mitigation_escaped}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    # Internal Terms Avoided
    st.markdown('<h4 style="color: #ffffff;">🚫 Internal Terms Avoided</h4>', unsafe_allow_html=True)
    
    internal_terms_count = evidence_summary.get("internal_terms_to_avoid_count", 0)
    
    if internal_terms_count > 0:
        st.markdown(f"""
            <div style="
                background-color: rgba(93, 217, 193, 0.2);
                padding: 1rem;
                border-radius: 0.5rem;
                border: 1px solid #5DD9C1;
            ">
                <div style="color: #ffffff; font-weight: 600;">
                    ✅ Successfully identified and avoided {internal_terms_count} internal term(s)
                </div>
                <div style="color: #e0e0e0; font-size: 0.85rem; margin-top: 0.5rem;">
                    These terms were automatically translated to customer-appropriate language.
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No internal terms needed to be avoided")


def render_deterministic_checks(checks: List[Dict[str, Any]]):
    """
    Render deterministic quality checks panel using Streamlit containers.
    
    Args:
        checks: List of deterministic check results
    """
    for check in checks:
        check_name = check.get("check_name", "Unknown Check")
        status = check.get("status", "unknown")
        details = check.get("details", "")
        actionable_fix = check.get("actionable_fix")
        
        # Status icons
        status_icons = {
            "pass": "✅",
            "warning": "⚠️",
            "fail": "❌"
        }
        icon = status_icons.get(status, "•")
        
        # Use Streamlit container with custom styling
        with st.container():
            # Header row
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"### {icon} {check_name}")
            with col2:
                if status == "pass":
                    st.success(status.upper(), icon="✅")
                elif status == "warning":
                    st.warning(status.upper(), icon="⚠️")
                else:
                    st.error(status.upper(), icon="❌")
            
            # Details - use st.text() to avoid ANY HTML rendering
            st.text(details)
            
            # Fix suggestion - use st.info() which auto-escapes
            if actionable_fix:
                st.info(f"💡 How to Fix: {actionable_fix}")
            
            st.markdown("---")


def render_llm_judge_dimensions(llm_judge_result: Dict[str, Any]):
    """
    Render LLM-as-Judge evaluation dimensions panel using Streamlit components.
    
    Args:
        llm_judge_result: LLM-as-Judge result with dimensions
    """
    # Overall score
    overall_score = llm_judge_result.get("overall_score", 0.0)
    confidence = llm_judge_result.get("confidence", "Unknown")
    overall_rationale = llm_judge_result.get("overall_rationale", "")
    
    # Display overall with container
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.metric("Overall Score", f"{overall_score:.2f}")
        with col2:
            if confidence == "High":
                st.success(confidence, icon="✅")
            elif confidence == "Medium":
                st.warning(confidence, icon="⚠️")
            else:
                st.error(confidence, icon="❌")
        
        # Use st.text() to prevent HTML rendering
        st.text(overall_rationale)
        st.markdown("---")
    
    st.subheader("Quality Dimensions")
    
    # Individual dimensions
    dimensions = llm_judge_result.get("dimensions", [])
    
    for dim in dimensions:
        dimension_name = dim.get("dimension", "Unknown Dimension")
        score = dim.get("score", 0.0)
        rationale = dim.get("rationale", "")
        status = dim.get("status", "unknown")
        improvement_suggestion = dim.get("improvement_suggestion")
        
        # Use expander for clean collapsible display
        with st.expander(f"{dimension_name} - **{score:.2f}**", expanded=False):
            # Status
            if status == "pass":
                st.success(f"Status: {status.upper()}", icon="✅")
            elif status == "warning":
                st.warning(f"Status: {status.upper()}", icon="⚠️")
            else:
                st.error(f"Status: {status.upper()}", icon="❌")
            
            # Progress bar
            st.progress(score)
            
            # Rationale - use st.text() to avoid HTML
            st.write("**Rationale:**")
            st.text(rationale)
            
            # Improvement suggestion
            if improvement_suggestion:
                st.info(f"💡 Improvement: {improvement_suggestion}")


def render_evidence_mappings(mappings: List[Dict[str, Any]]):
    """
    Render evidence mappings showing text-to-source traceability.
    
    Args:
        mappings: List of evidence mapping objects
    """
    st.markdown("""
        <div style="color: #e0e0e0; margin-bottom: 1rem; line-height: 1.6;">
            Evidence mappings show how each part of the generated draft traces back to specific source files,
            ensuring transparency and grounding in actual incident data.
        </div>
    """, unsafe_allow_html=True)
    
    if not mappings:
        st.info("No evidence mappings available")
        return
    
    for i, mapping in enumerate(mappings, 1):
        generated_text = mapping.get("generated_text", "N/A")
        evidence_field = mapping.get("evidence_field", "N/A")
        original_term = mapping.get("original_technical_term")
        customer_term = mapping.get("customer_facing_term")
        
        # Escape HTML in dynamic content
        generated_text_escaped = html.escape(str(generated_text))
        evidence_field_escaped = html.escape(str(evidence_field))
        
        # Render main mapping card
        st.markdown(f'''
            <div style="background-color: #2a2a2a; padding: 1.25rem; border-radius: 0.5rem; border-left: 4px solid #5DD9C1; margin-bottom: 1rem; border: 1px solid #444;">
                <div style="color: #aaaaaa; font-size: 0.75rem; margin-bottom: 0.5rem;">
                    Mapping #{i}
                </div>
                <div style="margin-bottom: 1rem;">
                    <div style="color: #aaaaaa; font-size: 0.85rem; margin-bottom: 0.25rem;">
                        Generated Text:
                    </div>
                    <div style="color: #ffffff; font-weight: 500; background-color: #1a1a1a; padding: 0.75rem; border-radius: 0.25rem; font-family: monospace;">
                        "{generated_text_escaped}"
                    </div>
                </div>
                <div style="margin-bottom: 0.75rem;">
                    <div style="color: #aaaaaa; font-size: 0.85rem; margin-bottom: 0.25rem;">
                        Source File:
                    </div>
                    <div style="color: #5DD9C1; font-family: monospace; font-size: 0.9rem;">
                        {evidence_field_escaped}
                    </div>
                </div>
            </div>
        ''', unsafe_allow_html=True)
        
        # Render translation separately if present
        if original_term and customer_term:
            original_term_escaped = html.escape(str(original_term))
            customer_term_escaped = html.escape(str(customer_term))
            st.markdown(f'''
                <div style="background-color: rgba(93, 217, 193, 0.2); padding: 0.75rem; border-radius: 0.25rem; margin-top: -0.5rem; margin-bottom: 1rem; border-left: 3px solid #5DD9C1;">
                    <div style="color: #ffffff; font-weight: 600; font-size: 0.8rem; margin-bottom: 0.25rem;">
                        🔄 Translation Applied:
                    </div>
                    <div style="color: #e0e0e0; font-size: 0.85rem;">
                        <span style="color: #FF6B6B;">{original_term_escaped}</span>
                        <span style="color: #aaaaaa;"> → </span>
                        <span style="color: #5DD9C1;">{customer_term_escaped}</span>
                    </div>
                </div>
            ''', unsafe_allow_html=True)


def render_confidence_badge(level: str, score: float):
    """
    Render a styled confidence badge using Abnormal AI colors.
    
    Args:
        level: Confidence level (High, Medium, Low)
        score: Confidence score (0.0 to 1.0)
    """
    # Use Abnormal teal for high, variations for medium/low
    colors = {
        "High": "#5DD9C1",      # Abnormal teal
        "Medium": "#FFB84D",    # Warm orange
        "Low": "#FF6B6B"        # Soft red
    }
    
    color = colors.get(level, "#6b7280")
    
    st.markdown(f"""
        <div style="
            display: inline-block;
            padding: 0.5rem 1rem;
            background-color: {color}30;
            border: 2px solid {color};
            border-radius: 0.5rem;
            color: #1a1a1a;
            font-weight: 600;
            margin-bottom: 1rem;
        ">
            Confidence: {level} ({score:.2f})
        </div>
    """, unsafe_allow_html=True)
