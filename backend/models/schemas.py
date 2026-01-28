"""Pydantic models for request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class IncidentData(BaseModel):
    """Input schema for incident data from multiple sources.
    
    This model accepts arbitrary data sources dynamically. You can include any combination of:
    - Text files (e.g., slack threads, incident notes)
    - JSON logs (e.g., CloudWatch, Datadog, Splunk)
    - JSON metrics (e.g., Prometheus, Grafana, New Relic)
    - JSON incidents (e.g., PagerDuty, Opsgenie, VictorOps)
    - JSON deployments (e.g., GitHub, GitLab, Jenkins)
    - Any other structured or unstructured incident data
    """
    
    model_config = {"extra": "allow"}  # Allow arbitrary additional fields
    
    phase: str = Field(
        ...,
        description="Current incident phase: investigating, identified, monitoring, or resolved"
    )
    
    # Common data sources (optional, for documentation)
    incident_context: Optional[str] = Field(
        None,
        description="Slack thread excerpts and engineer notes from incident_context.txt"
    )
    cloudwatch_logs: Optional[Dict[str, Any]] = Field(
        None,
        description="Structured logs from cloudwatch_logs.json"
    )
    prometheus_metrics: Optional[Dict[str, Any]] = Field(
        None,
        description="Time-series metrics from prometheus_metrics.json"
    )
    pagerduty_incident: Optional[Dict[str, Any]] = Field(
        None,
        description="PagerDuty incident metadata from pagerduty_incident.json"
    )
    github_deployments: Optional[Dict[str, Any]] = Field(
        None,
        description="Deployment history from github_deployments.json"
    )


class QualityScore(BaseModel):
    """Quality evaluation scores for a single dimension."""
    
    dimension: str = Field(..., description="Quality dimension name (e.g., 'clarity', 'completeness')")
    score: float = Field(..., ge=0.0, le=1.0, description="Score from 0.0 to 1.0")
    rationale: str = Field(..., description="Brief explanation of the score")


class DraftResponse(BaseModel):
    """Output schema for generated draft with evaluation results."""
    
    # Draft content
    title: str = Field(..., description="Incident title for status page")
    status: str = Field(..., description="Incident status (e.g., 'Investigating')")
    message: str = Field(..., description="Customer-facing message body")
    next_update: str = Field(..., description="When next update is expected (e.g., 'within 30 minutes')")
    
    # Evaluation results (legacy fields for backward compatibility)
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score (0.0-1.0)")
    confidence_level: str = Field(..., description="Confidence level: High, Medium, or Low")
    evidence_summary: str = Field(..., description="Summary of evidence that supports the draft")
    quality_scores: List[QualityScore] = Field(..., description="Detailed quality scores by dimension")
    warnings: List[str] = Field(default_factory=list, description="Any warnings or concerns about the draft")
    
    # New structured evaluation result
    evaluation_result: Optional['EvaluationResult'] = Field(None, description="Detailed evaluation with deterministic checks")
    
    # Transparency features (evidence grounding and data provenance)
    evidence_mappings: List['EvidenceMapping'] = Field(
        ..., 
        description="Maps each part of the message to source evidence"
    )
    internal_terms_avoided: List[str] = Field(
        default_factory=list,
        description="Internal terms that were properly excluded/translated"
    )
    extracted_evidence_summary: Dict[str, Any] = Field(
        ...,
        description="Summary of evidence that informed the draft"
    )
    data_sources_used: List[str] = Field(
        ...,
        description="Which data sources contributed to the draft"
    )


class ParsedIncidentResponse(BaseModel):
    """Output schema for parsed incident signals."""
    
    incident_start: Optional[str] = Field(None, description="Detected incident start time")
    detected_symptoms: List[str] = Field(default_factory=list, description="Customer-facing symptoms detected")
    affected_services: List[str] = Field(default_factory=list, description="Services affected by the incident")
    severity: Optional[str] = Field(None, description="Incident severity level")
    data_sources_present: List[str] = Field(default_factory=list, description="Which data sources were provided")
    raw_summary: str = Field(..., description="Human-readable summary of parsed data")


# ============================================================================
# Evidence Extraction Models (for LLM-powered extraction)
# ============================================================================

class IncidentMetadata(BaseModel):
    """Core incident metadata."""
    title: str = Field(..., description="Brief incident title")
    severity: str = Field(..., description="SEV-1, SEV-2, SEV-3, or unknown")
    incident_start_time: str = Field(..., description="Incident start time in PT timezone")
    affected_service: str = Field(..., description="Customer-facing service name (e.g., 'API', 'Email Notifications')")


class CustomerSymptom(BaseModel):
    """A customer-facing symptom with evidence and confidence."""
    symptom: str = Field(..., description="Technical description of what's happening (e.g., 'High API latency', '5xx errors')")
    confidence: str = Field(..., description="high, medium, or low")
    evidence_sources: List[str] = Field(..., description="List of sources supporting this (e.g., 'PagerDuty: p99 latency > 5s')")


class InvestigationStatus(BaseModel):
    """Current investigation and mitigation status."""
    root_cause_identified: bool = Field(..., description="Has root cause been identified?")
    diagnosis_summary: Optional[str] = Field(None, description="Technical diagnosis if root cause is known (raw technical details)")
    mitigation_action: Optional[str] = Field(None, description="What's being done to fix it (raw action description)")
    expected_resolution: Optional[str] = Field(None, description="Expected resolution time if mentioned")
    next_update_timing: str = Field(..., description="When next update is expected (e.g., 'within 30 minutes')")


class TimelineEvent(BaseModel):
    """A single event in the incident timeline."""
    time: str = Field(..., description="Time in PT timezone")
    event: str = Field(..., description="What happened")
    source: str = Field(..., description="Which data source this came from")


class SupportingEvidence(BaseModel):
    """Additional supporting evidence from various sources."""
    deployment_correlation: Optional[str] = Field(None, description="Deployments near incident time if relevant")
    error_patterns: Optional[str] = Field(None, description="Notable error patterns from logs")
    metrics_summary: Optional[str] = Field(None, description="Key metric changes")


class ExtractedEvidence(BaseModel):
    """Complete structured evidence extracted from incident data."""
    phase: str = Field(..., description="Incident phase: investigating, identified, monitoring, or resolved")
    incident_metadata: IncidentMetadata
    customer_symptoms: List[CustomerSymptom] = Field(..., description="Customer-facing symptoms with evidence")
    investigation_status: InvestigationStatus
    internal_terms_to_avoid: List[str] = Field(
        default_factory=list,
        description="Internal service names, technical terms that should not appear in customer communications"
    )
    supporting_evidence: Optional[SupportingEvidence] = Field(None, description="Additional supporting data")
    timeline_events: List[TimelineEvent] = Field(default_factory=list, description="Key events in chronological order")


# ============================================================================
# Generation Models (for LLM-powered draft generation)
# ============================================================================

class EvidenceMapping(BaseModel):
    """Maps a piece of generated text back to source evidence."""
    generated_text: str = Field(..., description="The text in the draft")
    evidence_field: str = Field(..., description="Which source file/data it came from (e.g., 'PagerDuty', 'CloudWatch Logs', 'Incident Context')")
    original_technical_term: Optional[str] = Field(None, description="Original technical term if translated")
    customer_facing_term: Optional[str] = Field(None, description="Customer-facing translation")


class GeneratedDraft(BaseModel):
    """LLM-generated status page draft with evidence grounding."""
    title: str = Field(..., description="Incident title for status page")
    status: str = Field(..., description="Incident status: Investigating, Identified, Monitoring, or Resolved")
    message: str = Field(..., description="Customer-facing message body")
    next_update: str = Field(..., description="When next update is expected")
    
    # Evidence grounding for evaluation phase
    evidence_mappings: List[EvidenceMapping] = Field(
        ..., 
        description="Maps each part of the message to source evidence"
    )
    internal_terms_avoided: List[str] = Field(
        default_factory=list,
        description="Internal terms from evidence that were properly excluded/translated"
    )
    confidence_notes: Optional[str] = Field(
        None,
        description="Any uncertainties or notes about the generation"
    )


# ============================================================================
# Evaluation Models (for deterministic quality checks)
# ============================================================================

class DeterministicCheck(BaseModel):
    """Result of a single deterministic quality check."""
    check_name: str = Field(..., description="Name of the check (e.g., 'Length Validation')")
    status: str = Field(..., description="Status: pass, warning, or fail")
    details: str = Field(..., description="Explanation of the check result")
    actionable_fix: Optional[str] = Field(None, description="Specific guidance on how to fix if failed")


class LLMJudgeDimension(BaseModel):
    """LLM evaluation for a single quality dimension."""
    dimension: str = Field(..., description="Quality dimension name")
    score: float = Field(..., ge=0.0, le=1.0, description="Score from 0.0 (poor) to 1.0 (excellent)")
    rationale: str = Field(..., description="LLM's reasoning for the score")
    status: str = Field(..., description="pass (>=0.8), warning (0.6-0.8), fail (<0.6)")
    improvement_suggestion: Optional[str] = Field(None, description="Specific suggestion if score < 0.8")


class LLMJudgeResult(BaseModel):
    """Complete LLM-as-Judge evaluation result."""
    dimensions: List[LLMJudgeDimension] = Field(..., description="Scores for each dimension")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Weighted average of all dimensions")
    confidence: str = Field(..., description="High (>=0.8), Medium (0.6-0.8), Low (<0.6)")
    overall_rationale: str = Field(..., description="Summary of evaluation")


class EvaluationResult(BaseModel):
    """Complete evaluation result with all deterministic checks."""
    overall_status: str = Field(..., description="Overall status: pass, warning, or fail")
    deterministic_checks: List[DeterministicCheck] = Field(..., description="Individual check results")
    warnings: List[str] = Field(default_factory=list, description="Aggregated warning messages")
    passed_checks: int = Field(..., description="Number of checks that passed")
    failed_checks: int = Field(..., description="Number of checks that failed")
    warning_checks: int = Field(..., description="Number of checks with warnings")
    llm_judge_result: Optional[LLMJudgeResult] = Field(None, description="LLM-as-Judge evaluation")


# Update forward references
DraftResponse.model_rebuild()
