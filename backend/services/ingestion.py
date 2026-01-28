"""Data ingestion and normalization service."""
from datetime import datetime
from typing import Dict, Any, List, Type, Tuple
import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


def parse_incident_data(incident_data) -> Dict[str, Any]:
    """
    Parse and normalize incident data from multiple sources.
    
    This function:
    1. Identifies which data sources are present
    2. Normalizes timestamps to UTC
    3. Extracts structured fields
    4. Detects customer-facing symptoms
    5. Correlates incident start time across sources
    
    Args:
        incident_data: IncidentData object with raw incident signals
        
    Returns:
        Dictionary with normalized incident information
    """
    parsed = {
        "data_sources_present": [],
        "incident_start": None,
        "detected_symptoms": [],
        "affected_services": [],
        "severity": None,
        "raw_summary": "",
    }
    
    # Track which data sources were provided
    if incident_data.pagerduty_incident:
        parsed["data_sources_present"].append("PagerDuty")
        parsed["severity"] = incident_data.pagerduty_incident.get("incident", {}).get("severity", "Unknown")
        parsed["incident_start"] = incident_data.pagerduty_incident.get("incident", {}).get("created_at")
    
    if incident_data.cloudwatch_logs:
        parsed["data_sources_present"].append("CloudWatch Logs")
        # Analyze logs for error patterns
        logs = incident_data.cloudwatch_logs.get("logs", [])
        error_count = sum(1 for log in logs if log.get("level") == "ERROR")
        if error_count > 0:
            parsed["detected_symptoms"].append(f"Service errors detected ({error_count} error logs)")
    
    if incident_data.prometheus_metrics:
        parsed["data_sources_present"].append("Prometheus Metrics")
        # Analyze metrics for performance degradation
        metrics = incident_data.prometheus_metrics.get("metrics", [])
        for metric in metrics:
            if "latency" in metric.get("metric_name", "").lower():
                parsed["detected_symptoms"].append("Increased API latency")
                break
    
    if incident_data.github_deployments:
        parsed["data_sources_present"].append("GitHub Deployments")
    
    if incident_data.incident_context:
        parsed["data_sources_present"].append("Incident Context")
        # Extract affected services from context
        # This is a simple placeholder - real implementation would use NLP
        context_lower = incident_data.incident_context.lower()
        if "api" in context_lower:
            parsed["affected_services"].append("API")
        if "database" in context_lower or "db" in context_lower:
            parsed["affected_services"].append("Database")
    
    # Generate summary
    summary_parts = [
        f"Data sources: {', '.join(parsed['data_sources_present'])}",
        f"Severity: {parsed['severity'] or 'Unknown'}",
        f"Detected symptoms: {len(parsed['detected_symptoms'])}",
    ]
    if parsed["incident_start"]:
        summary_parts.append(f"Incident start: {parsed['incident_start']}")
    
    parsed["raw_summary"] = " | ".join(summary_parts)
    
    return parsed


def normalize_timestamp(timestamp_str: str) -> datetime:
    """
    Normalize ISO 8601 timestamp to UTC datetime object.
    
    Args:
        timestamp_str: ISO 8601 formatted timestamp string
        
    Returns:
        datetime object in UTC
    """
    # Placeholder implementation
    return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))


def extract_customer_symptoms(logs: List[Dict], metrics: List[Dict]) -> List[str]:
    """
    Extract customer-facing symptoms from technical signals.
    
    Translates internal error messages and metric spikes into
    customer-appropriate language (e.g., "5xx errors" -> "intermittent errors").
    
    Args:
        logs: Parsed log entries
        metrics: Parsed metric data points
        
    Returns:
        List of customer-facing symptom descriptions
    """
    # Placeholder implementation
    symptoms = []
    
    # Check for error spikes in logs
    error_logs = [log for log in logs if log.get("level") == "ERROR"]
    if len(error_logs) > 10:
        symptoms.append("Intermittent service errors")
    
    # Check for latency increases in metrics
    for metric in metrics:
        if "latency" in metric.get("metric_name", ""):
            values = metric.get("values", [])
            if values and any(v.get("value", 0) > 5 for v in values):
                symptoms.append("Slower than normal response times")
                break
    
    return symptoms


# ============================================================================
# LLM-Powered Extraction Infrastructure
# ============================================================================

def prepare_files_for_extraction(incident_data) -> Tuple[str, List[str]]:
    """
    Preprocess incident files in a source-agnostic way.
    Works with any combination of uploaded files.
    
    Args:
        incident_data: IncidentData object with raw incident signals
    
    Returns:
        - Formatted context string for LLM
        - List of source names that were included
    """
    context_parts = []
    sources_included = []
    
    # Iterate through all fields dynamically
    for field_name, field_value in incident_data.model_dump().items():
        if field_value is None:
            continue
        
        # Convert field name to readable label
        source_label = field_name.replace('_', ' ').title()
        sources_included.append(source_label)
        
        # Add source delimiter
        context_parts.append(f"=== SOURCE: {source_label} ===")
        
        # Format based on type
        if isinstance(field_value, (dict, list)):
            context_parts.append(json.dumps(field_value, indent=2))
        else:
            context_parts.append(str(field_value))
        
        context_parts.append("")  # Blank line separator
    
    return "\n".join(context_parts), sources_included


def get_openai_client() -> OpenAI:
    """Initialize OpenAI client with API key and base URL."""
    import httpx
    
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    
    # Create httpx client with extended timeout for LLM calls
    http_client = httpx.Client(timeout=180.0)
    
    # Initialize client with minimal parameters
    client_params = {
        "api_key": api_key,
        "http_client": http_client
    }
    if base_url:
        client_params["base_url"] = base_url
    
    return OpenAI(**client_params)


def build_extraction_prompt(phase: str, formatted_context: str, sources: List[str]) -> str:
    """
    Build phase-specific extraction prompt with guidance.
    
    Args:
        phase: Incident phase (investigating/identified/monitoring/resolved)
        formatted_context: Preprocessed incident data
        sources: List of data sources included
        
    Returns:
        Complete extraction prompt
    """
    # Phase definitions from status_page_examples.md
    phase_definitions = {
        "investigating": "We are aware of the issue and working to identify the cause",
        "identified": "We know what's wrong and are implementing a fix",
        "monitoring": "Fix is deployed, we're watching to ensure it's working",
        "resolved": "Issue is fixed and system is stable"
    }
    
    # Phase-specific extraction guidance
    phase_guidance = {
        "investigating": """
REQUIRED EXTRACTIONS FOR INVESTIGATING PHASE:
- Technical symptoms (e.g., "High API latency", "Connection timeouts") - REQUIRED with high confidence
- Affected service/functionality areas - REQUIRED
- Investigation status from Slack (e.g., "Checking logs", "Looking at metrics") - REQUIRED
- Next update timing - REQUIRED

DO NOT EXTRACT (not relevant yet):
- Root cause details (set root_cause_identified: false)
- Diagnosis or conclusions
- Deployment correlations (unless mentioned as active investigation area)

""",
        "identified": """
REQUIRED EXTRACTIONS FOR IDENTIFIED PHASE:
- Technical symptoms - REQUIRED
- Affected areas - REQUIRED
- Root cause / diagnosis - REQUIRED (extract raw technical diagnosis from Slack/investigation)
- Mitigation action being taken - REQUIRED
- Expected resolution time - OPTIONAL (include if mentioned)

NOW RELEVANT:
- Set root_cause_identified: true
- Extract diagnosis_summary (e.g., "Connection pool exhausted due to PR #12345 timeout change")
- Include deployment correlations if they are the cause
- Extract specific technical details about the fix being implemented

""",
        "monitoring": """
REQUIRED EXTRACTIONS FOR MONITORING PHASE:
- Fix deployment confirmation - REQUIRED
- Recovery status indicators - REQUIRED
- Monitoring duration - OPTIONAL
- Remaining impact details - OPTIONAL

FOCUS: Extract confirmation that fix was deployed and metrics are improving. Note how long monitoring will continue.
""",
        "resolved": """
REQUIRED EXTRACTIONS FOR RESOLVED PHASE:
- Complete timeline of events - REQUIRED
- Total incident duration - REQUIRED
- Final impact summary - REQUIRED
- Resolution confirmation with stability period - REQUIRED

FOCUS: Extract complete incident story from start to finish. Calculate duration. Summarize overall customer impact.
"""
    }
    
    prompt = f"""You are extracting structured evidence from incident data to generate a status page update.

CURRENT PHASE: {phase}
PHASE DEFINITION: {phase_definitions.get(phase, "Unknown phase")}

{phase_guidance.get(phase, "")}

SOURCES AVAILABLE: {', '.join(sources)}

<incident_data>
{formatted_context}
</incident_data>

EXTRACTION INSTRUCTIONS:
1. Extract information relevant to the "{phase}" phase using the guidance above
2. For EACH extracted piece of information, cite the specific source where you found it
3. Assign confidence level (high/medium/low) based on:
   - HIGH: Explicitly stated in source data, or multiple sources corroborate
   - MEDIUM: Implied but not explicit, or single source mentions it
   - LOW: Weak signals or requires significant interpretation
4. Extract RAW TECHNICAL INFORMATION as-is from the sources - do NOT translate to customer language
5. Identify internal terms to flag for avoidance (service names like "api-gateway", database IDs, employee names/emails, PR numbers, etc.)
6. If required information is not present in the data, use reasonable defaults or mark as "unknown"
7. Cross-reference sources to improve confidence - if multiple sources say the same thing, that's HIGH confidence

IMPORTANT CONSTRAINTS:
- Do NOT invent or hallucinate information not present in the sources
- Extract technical details AS-IS - translation will happen in a later generation phase
- For timestamps, convert to PT timezone format (e.g., "January 15, 2:23 PM PT")
- Flag internal system names for the internal_terms_to_avoid list (e.g., "api-gateway", "rds-prod-main", "alice.engineer@example.com")

Extract structured evidence now."""

    return prompt


def extract_evidence_with_llm(
    incident_data,
    phase: str,
    response_model: Type[BaseModel]
) -> BaseModel:
    """
    Extract structured evidence from incident data using LLM.
    
    Args:
        incident_data: Raw incident data from multiple sources
        phase: Incident phase (investigating/identified/monitoring/resolved)
        response_model: Pydantic model for structured output
        
    Returns:
        Extracted evidence as Pydantic model instance
    """
    # Preprocess files
    formatted_context, sources = prepare_files_for_extraction(incident_data)
    
    # Initialize client
    client = get_openai_client()
    
    # Build phase-specific extraction prompt
    extraction_prompt = build_extraction_prompt(phase, formatted_context, sources)
    
    # Call OpenAI with structured output
    response = client.beta.chat.completions.parse(
        model="gpt-5-mini",
        messages=[
            {
                "role": "system",
                "content": "You are extracting structured evidence from incident data."
            },
            {
                "role": "user",
                "content": extraction_prompt
            }
        ],
        response_format=response_model
    )
    
    # Return parsed result
    return response.choices[0].message.parsed
