"""API endpoint definitions."""
from fastapi import APIRouter, HTTPException
from ..models.schemas import (
    IncidentData, 
    DraftResponse, 
    ParsedIncidentResponse,
    ExtractedEvidence,
    GeneratedDraft,
    EvaluationResult,
    QualityScore,
    LLMJudgeResult
)
from ..services.ingestion import parse_incident_data, extract_evidence_with_llm
from ..services.generator import generate_draft, generate_draft_with_llm
from ..services.evaluator import evaluate_draft_deterministic, evaluate_with_llm_judge
import os

router = APIRouter()


@router.post("/generate-draft", response_model=DraftResponse)
async def generate_draft_endpoint(incident_data: IncidentData):
    """
    Generate a status page draft from incident data.
    
    This orchestrates the full pipeline:
    1. LLM Evidence Extraction
    2. LLM Draft Generation (with evidence grounding)
    3. Quality Evaluation (Deterministic + LLM-as-Judge)
    """
    try:
        # Stage 1: Extract structured evidence
        extracted_evidence = extract_evidence_with_llm(
            incident_data=incident_data,
            phase=incident_data.phase,
            response_model=ExtractedEvidence
        )
        
        # Stage 2: Generate draft with evidence grounding
        generated_draft = generate_draft_with_llm(extracted_evidence)
        
        # Stage 3a: Evaluate quality with deterministic checks
        evaluation_result = evaluate_draft_deterministic(generated_draft, extracted_evidence)
        
        # Stage 3b: Evaluate quality with LLM-as-Judge
        llm_judge_result = evaluate_with_llm_judge(generated_draft, extracted_evidence)
        
        # Combine evaluations
        evaluation_result.llm_judge_result = llm_judge_result
        
        # Generate legacy quality scores for backward compatibility
        legacy_quality_scores = [
            QualityScore(
                dimension=check.check_name,
                score=1.0 if check.status == "pass" else (0.7 if check.status == "warning" else 0.3),
                rationale=check.details
            )
            for check in evaluation_result.deterministic_checks
        ]
        
        # Use LLM-as-Judge overall score as primary confidence metric
        if evaluation_result.llm_judge_result:
            confidence_score = evaluation_result.llm_judge_result.overall_score
            confidence_level = evaluation_result.llm_judge_result.confidence
        else:
            # Fallback to deterministic average if LLM judge not available
            avg_score = sum(s.score for s in legacy_quality_scores) / len(legacy_quality_scores) if legacy_quality_scores else 0.5
            confidence_score = avg_score
            confidence_level = "High" if avg_score >= 0.8 else ("Medium" if avg_score >= 0.6 else "Low")
        
        # Prepare extracted evidence summary for transparency
        extracted_evidence_summary = {
            "phase": extracted_evidence.phase,
            "incident_metadata": {
                "title": extracted_evidence.incident_metadata.title,
                "severity": extracted_evidence.incident_metadata.severity,
                "affected_service": extracted_evidence.incident_metadata.affected_service,
                "start_time": extracted_evidence.incident_metadata.incident_start_time
            },
            "customer_symptoms_count": len(extracted_evidence.customer_symptoms),
            "customer_symptoms": [
                {
                    "symptom": s.symptom,
                    "confidence": s.confidence,
                    "evidence_sources": s.evidence_sources
                }
                for s in extracted_evidence.customer_symptoms
            ],
            "root_cause_identified": extracted_evidence.investigation_status.root_cause_identified,
            "diagnosis": extracted_evidence.investigation_status.diagnosis_summary,
            "mitigation_action": extracted_evidence.investigation_status.mitigation_action,
            "internal_terms_to_avoid_count": len(extracted_evidence.internal_terms_to_avoid)
        }
        
        # Determine which data sources were used
        data_sources_used = []
        if incident_data.pagerduty_incident:
            data_sources_used.append("PagerDuty")
        if incident_data.incident_context:
            data_sources_used.append("Incident Context")
        if incident_data.cloudwatch_logs:
            data_sources_used.append("CloudWatch Logs")
        if incident_data.prometheus_metrics:
            data_sources_used.append("Prometheus Metrics")
        if incident_data.github_deployments:
            data_sources_used.append("GitHub Deployments")
        
        return DraftResponse(
            title=generated_draft.title,
            status=generated_draft.status,
            message=generated_draft.message,
            next_update=generated_draft.next_update,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            evidence_summary=f"Based on {len(extracted_evidence.customer_symptoms)} symptoms, {len(extracted_evidence.internal_terms_to_avoid)} internal terms identified",
            quality_scores=legacy_quality_scores,
            warnings=evaluation_result.warnings,
            evaluation_result=evaluation_result,
            # Transparency fields
            evidence_mappings=generated_draft.evidence_mappings,
            internal_terms_avoided=generated_draft.internal_terms_avoided,
            extracted_evidence_summary=extracted_evidence_summary,
            data_sources_used=data_sources_used
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating draft: {str(e)}")


@router.post("/extract-evidence", response_model=ExtractedEvidence)
async def extract_evidence_endpoint(incident_data: IncidentData):
    """
    Extract structured evidence from incident data using LLM.
    
    This endpoint runs only Stage 1 (LLM Evidence Extraction) and returns
    the structured evidence for debugging and validation purposes.
    """
    try:
        extracted_evidence = extract_evidence_with_llm(
            incident_data=incident_data,
            phase=incident_data.phase,
            response_model=ExtractedEvidence
        )
        return extracted_evidence
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting evidence: {str(e)}")


@router.post("/generate-from-evidence", response_model=GeneratedDraft)
async def generate_from_evidence_endpoint(evidence: ExtractedEvidence):
    """
    Generate draft from already-extracted evidence (for testing Stage 2 only).
    
    This endpoint is useful for debugging the generation stage independently
    by providing pre-extracted evidence directly.
    """
    try:
        return generate_draft_with_llm(evidence)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating draft: {str(e)}")


@router.post("/evaluate-draft", response_model=EvaluationResult)
async def evaluate_draft_endpoint(draft: GeneratedDraft, evidence: ExtractedEvidence):
    """
    Evaluate draft quality using deterministic checks (for testing Stage 3 only).
    
    This endpoint runs only Stage 3 (Deterministic Quality Evaluation) and returns
    detailed check results for debugging purposes.
    
    Args:
        draft: Generated draft from Stage 2
        evidence: Extracted evidence from Stage 1 (needed for internal term checking)
    
    Returns:
        EvaluationResult with all deterministic check results
    """
    try:
        return evaluate_draft_deterministic(draft, evidence)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error evaluating draft: {str(e)}")


@router.post("/evaluate-with-llm-judge", response_model=LLMJudgeResult)
async def evaluate_with_llm_judge_endpoint(draft: GeneratedDraft, evidence: ExtractedEvidence):
    """
    Evaluate draft quality using LLM-as-Judge (for testing Stage 3b only).
    
    This endpoint runs only the LLM-as-Judge evaluation and returns
    subjective quality scores across 5 dimensions for debugging purposes.
    
    Args:
        draft: Generated draft from Stage 2
        evidence: Extracted evidence from Stage 1 (for factual grounding check)
    
    Returns:
        LLMJudgeResult with dimension scores, rationales, and improvement suggestions
    """
    try:
        return evaluate_with_llm_judge(draft, evidence)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in LLM-as-Judge evaluation: {str(e)}")


@router.post("/parse-incident", response_model=ParsedIncidentResponse)
async def parse_incident_endpoint(incident_data: IncidentData):
    """
    Parse and display raw incident signals (legacy endpoint).
    
    This endpoint is useful for validating data ingestion and 
    understanding what signals are available before generating a draft.
    """
    try:
        parsed_data = parse_incident_data(incident_data)
        return ParsedIncidentResponse(
            incident_start=parsed_data.get("incident_start"),
            detected_symptoms=parsed_data.get("detected_symptoms", []),
            affected_services=parsed_data.get("affected_services", []),
            severity=parsed_data.get("severity"),
            data_sources_present=parsed_data.get("data_sources_present", []),
            raw_summary=parsed_data.get("raw_summary", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing incident data: {str(e)}")


@router.get("/status-examples")
async def get_status_examples():
    """
    Fetch example status page messages from the data directory.
    
    These examples serve as the style guide for draft generation.
    """
    try:
        examples_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data", "data", "status_page_examples.md"
        )
        
        if not os.path.exists(examples_path):
            raise HTTPException(status_code=404, detail="Status examples file not found")
        
        with open(examples_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {"examples": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading status examples: {str(e)}")
