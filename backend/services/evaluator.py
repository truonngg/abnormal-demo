"""Quality evaluation and confidence scoring service."""
from typing import List
import os
import json
import re
import httpx
from openai import OpenAI
from pathlib import Path
from ..models.schemas import (
    DeterministicCheck,
    EvaluationResult,
    GeneratedDraft,
    ExtractedEvidence,
    LLMJudgeDimension,
    LLMJudgeResult
)


def _strip_html_from_text(text: str) -> str:
    """Remove any HTML tags and entities from text."""
    if not text:
        return text
    # Remove all HTML tags
    cleaned = re.sub(r'<[^>]+>', '', text)
    # Remove HTML entities
    cleaned = re.sub(r'&[a-zA-Z]+;', '', cleaned)
    return cleaned.strip()


def evaluate_draft_deterministic(
    draft: GeneratedDraft,
    evidence: ExtractedEvidence
) -> EvaluationResult:
    """
    Evaluate draft quality using deterministic checks.
    
    This function runs:
    1. Length validation (60-150 words)
    2. Internal term leakage detection
    3. Required fields present
    4. Phase-specific requirements
    
    Args:
        draft: Generated draft from Stage 2
        evidence: Extracted evidence from Stage 1
        
    Returns:
        EvaluationResult with check results and overall status
    """
    checks: List[DeterministicCheck] = []
    
    # Check 1: Length Validation
    checks.append(_check_length(draft.message))
    
    # Check 2: Internal Term Leakage Detection
    checks.append(_check_internal_leakage(draft, evidence))
    
    # Check 3: Required Fields Present
    checks.append(_check_required_fields(draft, evidence))
    
    # Check 4: Phase-Specific Requirements
    checks.append(_check_phase_requirements(draft, evidence))
    
    # Aggregate results
    passed = sum(1 for c in checks if c.status == "pass")
    failed = sum(1 for c in checks if c.status == "fail")
    warnings = sum(1 for c in checks if c.status == "warning")
    
    # Determine overall status
    if failed > 0:
        overall_status = "fail"
    elif warnings > 0:
        overall_status = "warning"
    else:
        overall_status = "pass"
    
    # Collect warning messages
    warning_messages = [
        f"{c.check_name}: {c.details}" 
        for c in checks 
        if c.status in ["warning", "fail"]
    ]
    
    # Strip any HTML from check fields
    for check in checks:
        check.check_name = _strip_html_from_text(check.check_name)
        check.details = _strip_html_from_text(check.details)
        if check.actionable_fix:
            check.actionable_fix = _strip_html_from_text(check.actionable_fix)
    
    return EvaluationResult(
        overall_status=overall_status,
        deterministic_checks=checks,
        warnings=warning_messages,
        passed_checks=passed,
        failed_checks=failed,
        warning_checks=warnings
    )


def _check_length(message: str) -> DeterministicCheck:
    """
    Check 1: Validate message length (60-150 words recommended).
    
    Status:
    - pass: 60-150 words
    - warning: 45-60 or 150-160 words
    - fail: < 45 or > 160 words
    """
    word_count = len(message.split())
    
    if 60 <= word_count <= 150:
        return DeterministicCheck(
            check_name="Length Validation",
            status="pass",
            details=f"Message length is appropriate ({word_count} words)",
            actionable_fix=None
        )
    elif 45 <= word_count < 60:
        return DeterministicCheck(
            check_name="Length Validation",
            status="warning",
            details=f"Message is slightly short ({word_count} words, recommended: 60-150)",
            actionable_fix=f"Consider adding more detail. Currently {word_count} words, recommended minimum is 60 words."
        )
    elif 150 < word_count <= 160:
        return DeterministicCheck(
            check_name="Length Validation",
            status="warning",
            details=f"Message is slightly long ({word_count} words, recommended: 60-150)",
            actionable_fix=f"Consider condensing the message. Currently {word_count} words, recommended maximum is 150 words."
        )
    elif word_count < 45:
        return DeterministicCheck(
            check_name="Length Validation",
            status="fail",
            details=f"Message is too short ({word_count} words, minimum: 45)",
            actionable_fix=f"Add more detail to the message. Currently {word_count} words, need at least 45 words (recommended: 60-150)."
        )
    else:  # > 160
        return DeterministicCheck(
            check_name="Length Validation",
            status="fail",
            details=f"Message is too long ({word_count} words, maximum: 160)",
            actionable_fix=f"Significantly condense the message. Currently {word_count} words, maximum is 160 words (recommended: 60-150)."
        )


def _check_internal_leakage(draft: GeneratedDraft, evidence: ExtractedEvidence) -> DeterministicCheck:
    """
    Check 2: Detect internal term leakage.
    
    Scans title and message for any terms from evidence.internal_terms_to_avoid.
    Status: pass (none found), fail (any found)
    """
    internal_terms = evidence.internal_terms_to_avoid
    if not internal_terms:
        return DeterministicCheck(
            check_name="Internal Term Leakage Detection",
            status="pass",
            details="No internal terms to check (list is empty)",
            actionable_fix=None
        )
    
    # Combine title and message for checking
    full_text = f"{draft.title} {draft.message}".lower()
    
    # Find leaked terms
    leaked_terms = []
    for term in internal_terms:
        if term.lower() in full_text:
            # Find position in text
            if term.lower() in draft.title.lower():
                leaked_terms.append(f"'{term}' in title")
            if term.lower() in draft.message.lower():
                leaked_terms.append(f"'{term}' in message")
    
    if not leaked_terms:
        return DeterministicCheck(
            check_name="Internal Term Leakage Detection",
            status="pass",
            details=f"No internal terms leaked (checked {len(internal_terms)} terms)",
            actionable_fix=None
        )
    else:
        leaked_list = ", ".join(set(leaked_terms))
        return DeterministicCheck(
            check_name="Internal Term Leakage Detection",
            status="fail",
            details=f"Internal terms detected: {leaked_list}",
            actionable_fix=f"Remove or rephrase the following internal terms: {leaked_list}. Use customer-facing language instead."
        )


def _check_required_fields(draft: GeneratedDraft, evidence: ExtractedEvidence) -> DeterministicCheck:
    """
    Check 3: Verify required fields are present.
    
    Required elements:
    - Customer impact statement
    - Affected service mentioned
    - Action statement
    - Next update timing
    
    Status: pass (all present), warning (1 missing), fail (2+ missing)
    """
    missing_elements = []
    message_lower = draft.message.lower()
    
    # Check 1: Customer impact statement
    impact_keywords = ["experiencing", "may experience", "reports of", "affecting", "impacting", "issue"]
    if not any(keyword in message_lower for keyword in impact_keywords):
        missing_elements.append("customer impact statement")
    
    # Check 2: Affected service mentioned
    affected_service = evidence.incident_metadata.affected_service.lower()
    # More lenient check - service might be described differently
    service_mentioned = (
        affected_service in message_lower or
        "service" in message_lower or
        "api" in message_lower or
        "system" in message_lower
    )
    if not service_mentioned:
        missing_elements.append(f"affected service ('{evidence.incident_metadata.affected_service}')")
    
    # Check 3: Action statement
    action_keywords = ["investigating", "working", "team", "deployed", "monitoring", "identified", "implementing", "resolved"]
    if not any(keyword in message_lower for keyword in action_keywords):
        missing_elements.append("action statement")
    
    # Check 4: Next update timing
    if not draft.next_update or draft.next_update.strip() == "":
        missing_elements.append("next update timing")
    
    # Determine status
    if len(missing_elements) == 0:
        return DeterministicCheck(
            check_name="Required Fields Present",
            status="pass",
            details="All required fields are present (impact, service, action, next update)",
            actionable_fix=None
        )
    elif len(missing_elements) == 1:
        return DeterministicCheck(
            check_name="Required Fields Present",
            status="warning",
            details=f"Missing element: {missing_elements[0]}",
            actionable_fix=f"Consider adding {missing_elements[0]} to the message for completeness."
        )
    else:
        missing_list = ", ".join(missing_elements)
        return DeterministicCheck(
            check_name="Required Fields Present",
            status="fail",
            details=f"Missing {len(missing_elements)} elements: {missing_list}",
            actionable_fix=f"Add the following elements to the message: {missing_list}"
        )


def _check_phase_requirements(draft: GeneratedDraft, evidence: ExtractedEvidence) -> DeterministicCheck:
    """
    Check 4: Verify phase-specific requirements.
    
    Phase requirements:
    - Investigating: Should NOT claim root cause
    - Identified: SHOULD mention root cause
    - Monitoring: SHOULD mention deployed fix
    - Resolved: SHOULD contain summary/apology
    
    Status: pass/fail based on phase
    """
    phase = evidence.phase.lower()
    message_lower = draft.message.lower()
    title_lower = draft.title.lower()
    
    if phase == "investigating":
        # Should NOT claim root cause
        root_cause_claims = ["caused by", "due to", "root cause", "the cause is", "because of"]
        problematic_claims = [claim for claim in root_cause_claims if claim in message_lower or claim in title_lower]
        
        if problematic_claims:
            return DeterministicCheck(
                check_name="Phase-Specific Requirements",
                status="fail",
                details=f"Investigating phase should not claim root cause. Found: {', '.join(problematic_claims)}",
                actionable_fix="Remove root cause claims. During investigation, use phrases like 'investigating the issue' or 'working to understand the problem' instead."
            )
        else:
            return DeterministicCheck(
                check_name="Phase-Specific Requirements",
                status="pass",
                details="Investigating phase: correctly avoids root cause claims",
                actionable_fix=None
            )
    
    elif phase == "identified":
        # SHOULD mention root cause or explanation
        cause_keywords = ["identified", "cause", "issue", "problem", "due to", "related to", "resulted from"]
        has_cause_mention = any(keyword in message_lower for keyword in cause_keywords)
        
        if has_cause_mention:
            return DeterministicCheck(
                check_name="Phase-Specific Requirements",
                status="pass",
                details="Identified phase: includes cause/explanation",
                actionable_fix=None
            )
        else:
            return DeterministicCheck(
                check_name="Phase-Specific Requirements",
                status="fail",
                details="Identified phase should explain the root cause or issue",
                actionable_fix="Add an explanation of what caused the issue (in customer-friendly terms)."
            )
    
    elif phase == "monitoring":
        # SHOULD mention deployed fix
        fix_keywords = ["deployed", "fix", "implemented", "applied", "rolled out", "changes"]
        has_fix_mention = any(keyword in message_lower for keyword in fix_keywords)
        
        if has_fix_mention:
            return DeterministicCheck(
                check_name="Phase-Specific Requirements",
                status="pass",
                details="Monitoring phase: mentions deployed fix",
                actionable_fix=None
            )
        else:
            return DeterministicCheck(
                check_name="Phase-Specific Requirements",
                status="fail",
                details="Monitoring phase should mention that a fix has been deployed",
                actionable_fix="Add a statement about the fix that was deployed (e.g., 'We have deployed a fix and are monitoring the results')."
            )
    
    elif phase == "resolved":
        # SHOULD contain summary and/or apology
        summary_keywords = ["resolved", "restored", "normal", "completed"]
        apology_keywords = ["apologize", "sorry", "regret", "inconvenience"]
        
        has_summary = any(keyword in message_lower for keyword in summary_keywords)
        has_apology = any(keyword in message_lower for keyword in apology_keywords)
        
        if has_summary and has_apology:
            return DeterministicCheck(
                check_name="Phase-Specific Requirements",
                status="pass",
                details="Resolved phase: includes both resolution summary and apology",
                actionable_fix=None
            )
        elif has_summary or has_apology:
            missing = "apology" if has_summary else "resolution summary"
            return DeterministicCheck(
                check_name="Phase-Specific Requirements",
                status="warning",
                details=f"Resolved phase: has {'summary' if has_summary else 'apology'} but missing {missing}",
                actionable_fix=f"Consider adding {missing} to provide complete closure."
            )
        else:
            return DeterministicCheck(
                check_name="Phase-Specific Requirements",
                status="fail",
                details="Resolved phase should include resolution summary and apology",
                actionable_fix="Add a summary of the resolution and an apology for the inconvenience caused to customers."
            )
    
    else:
        # Unknown phase
        return DeterministicCheck(
            check_name="Phase-Specific Requirements",
            status="warning",
            details=f"Unknown phase: '{phase}' (expected: investigating, identified, monitoring, resolved)",
            actionable_fix=None
        )


# ============================================================================
# LLM-as-Judge Evaluation (Subjective Quality Assessment)
# ============================================================================

def get_openai_client() -> OpenAI:
    """Initialize OpenAI client with API key."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    # Extended timeout for LLM evaluation calls
    http_client = httpx.Client(timeout=180.0)
    return OpenAI(api_key=api_key, http_client=http_client)


def load_examples() -> tuple[str, str]:
    """
    Load positive and negative examples for LLM-as-Judge.
    
    Returns:
        Tuple of (positive_examples, negative_examples)
    """
    # Get the data directory path
    current_dir = Path(__file__).parent.parent.parent
    data_dir = current_dir / "data" / "data"
    
    # Load positive examples
    positive_path = data_dir / "status_page_examples.md"
    if positive_path.exists():
        with open(positive_path, 'r', encoding='utf-8') as f:
            positive_examples = f.read()
    else:
        positive_examples = "No positive examples found"
    
    # Load negative examples
    negative_path = data_dir / "negative_examples.md"
    if negative_path.exists():
        with open(negative_path, 'r', encoding='utf-8') as f:
            negative_examples = f.read()
    else:
        negative_examples = "No negative examples found"
    
    return positive_examples, negative_examples


def build_llm_judge_prompt(draft: GeneratedDraft, evidence: ExtractedEvidence) -> str:
    """
    Build the prompt for LLM-as-Judge evaluation.
    
    Args:
        draft: Generated draft to evaluate
        evidence: Extracted evidence for fact-checking
        
    Returns:
        Complete prompt for LLM evaluation
    """
    positive_examples, negative_examples = load_examples()
    
    # Create evidence JSON (simplified for prompt)
    evidence_json = {
        "phase": evidence.phase,
        "customer_symptoms": [
            {"symptom": s.symptom, "evidence": s.evidence_sources}
            for s in evidence.customer_symptoms
        ],
        "root_cause_identified": evidence.investigation_status.root_cause_identified,
        "diagnosis": evidence.investigation_status.diagnosis_summary,
        "mitigation_action": evidence.investigation_status.mitigation_action
    }
    
    prompt = f"""You are an expert evaluator assessing status page messages for customer incident communications.

IMPORTANT: Provide all responses as PLAIN TEXT ONLY. Do NOT include HTML tags, markdown formatting, or any markup in your responses. All rationale and suggestions should be plain text.

EVALUATION RUBRIC - Score each dimension from 0.0 (poor) to 1.0 (excellent):

1. **Clarity and Customer Focus** (0.0-1.0)
   - 1.0: Crystal clear impact statement, customer perspective, no jargon, easy to understand
   - 0.7: Mostly clear but some vagueness or minor jargon
   - 0.4: Somewhat unclear, mixed focus between internal and customer perspective
   - 0.0: Vague, internal focus, heavy technical jargon, unclear impact

2. **Tone Consistency with Brand Voice** (0.0-1.0)
   - 1.0: Professional, empathetic, direct, honest - matches example tone perfectly
   - 0.7: Generally appropriate tone with minor inconsistencies
   - 0.4: Tone issues - too casual or too stiff, lacking empathy
   - 0.0: Completely inappropriate - dismissive, too casual, or cold

3. **Appropriate Technical Detail Balance** (0.0-1.0)
   - 1.0: Perfect balance - just enough detail, technical terms translated to customer language
   - 0.7: Mostly appropriate level with minor over/under-explanation
   - 0.4: Significant imbalance - either too technical or too vague
   - 0.0: Far too technical (exposes internals) or uselessly vague

4. **Factual Grounding / No Hallucinations** (0.0-1.0)
   - 1.0: Every claim is directly supported by evidence, no speculation
   - 0.7: Mostly supported, minor inference that's reasonable
   - 0.4: Some unsupported claims or speculation presented as fact
   - 0.0: Major hallucinations, contradicts evidence, or makes completely unsupported claims

5. **Phase Appropriateness** (0.0-1.0)
   - 1.0: Message perfectly matches incident lifecycle stage expectations
   - 0.7: Generally appropriate with minor misalignment
   - 0.4: Noticeable issues - wrong messaging for the phase
   - 0.0: Completely wrong phase messaging (e.g., claiming resolution during investigation)

POSITIVE EXAMPLES (these score 0.9-1.0):
{positive_examples[:2000]}

NEGATIVE EXAMPLES (these score 0.0-0.3):
{negative_examples}

EVIDENCE PROVIDED (use this to verify factual grounding):
{json.dumps(evidence_json, indent=2)}

DRAFT TO EVALUATE:
Phase: {evidence.phase}
Title: {draft.title}
Status: {draft.status}
Message: {draft.message}
Next Update: {draft.next_update}

Evaluate this draft across all 5 dimensions. For each dimension:
- Assign a precise score from 0.0 to 1.0
- Provide specific rationale explaining the score (PLAIN TEXT ONLY - NO HTML, NO MARKUP)
- Determine status: pass (>=0.8), warning (0.6-0.8), fail (<0.6)
- If score < 0.8, provide a specific improvement suggestion (PLAIN TEXT ONLY - NO HTML, NO MARKUP)

CRITICAL FORMATTING RULES:
- All text fields must be plain text only
- Do NOT use HTML tags like <div>, <span>, or any other tags
- Do NOT include CSS styling or inline styles
- Do NOT use markdown formatting
- Use simple sentences and line breaks only

Focus especially on:
- Factual grounding: Does every claim match the evidence?
- Phase appropriateness: Does the message fit the "{evidence.phase}" phase?
- Customer language: Are technical terms properly translated?"""

    return prompt


def evaluate_with_llm_judge(
    draft: GeneratedDraft,
    evidence: ExtractedEvidence
) -> LLMJudgeResult:
    """
    Use LLM to evaluate subjective quality dimensions.
    
    Args:
        draft: Generated draft from Stage 2
        evidence: Extracted evidence from Stage 1
        
    Returns:
        LLMJudgeResult with scores and rationales
    """
    client = get_openai_client()
    prompt = build_llm_judge_prompt(draft, evidence)
    
    # Call LLM with JSON mode (allows custom temperature, unlike structured outputs)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.1,
        messages=[
            {
                "role": "system",
                "content": "You are an expert evaluator of customer communication quality. Provide detailed, honest assessments. CRITICAL: All text fields (rationale, improvement_suggestion, overall_rationale) must be PLAIN TEXT ONLY - absolutely NO HTML tags (<div>, <span>, etc.), NO markdown formatting, NO markup whatsoever. Write as if writing a simple text email. Return your response as valid JSON."
            },
            {
                "role": "user",
                "content": prompt + "\n\nCRITICAL INSTRUCTION: Write all text in PLAIN TEXT format as if writing a simple text email. DO NOT include any HTML tags (no <div>, <span>, <p>, etc.), NO markdown, NO formatting codes. Just write natural sentences.\n\nReturn your evaluation as JSON with this structure: {\"dimensions\": [{\"dimension\": str, \"score\": float, \"rationale\": str, \"status\": str, \"improvement_suggestion\": str}], \"overall_score\": float, \"confidence\": str, \"overall_rationale\": str}"
            }
        ],
        response_format={"type": "json_object"}
    )
    
    # Parse the JSON response
    import json as json_lib
    response_json = json_lib.loads(response.choices[0].message.content)
    
    # Convert to LLMJudgeResult object
    llm_result = LLMJudgeResult(**response_json)
    
    # Strip any HTML that might have snuck through
    llm_result.overall_rationale = _strip_html_from_text(llm_result.overall_rationale)
    for dim in llm_result.dimensions:
        dim.rationale = _strip_html_from_text(dim.rationale)
        if dim.improvement_suggestion:
            dim.improvement_suggestion = _strip_html_from_text(dim.improvement_suggestion)
    
    # Calculate weighted overall score
    dimension_weights = {
        "Clarity and Customer Focus": 0.25,
        "Tone Consistency with Brand Voice": 0.20,
        "Appropriate Technical Detail Balance": 0.15,
        "Factual Grounding / No Hallucinations": 0.30,
        "Phase Appropriateness": 0.10
    }
    
    # Calculate weighted average
    weighted_sum = 0.0
    for dim in llm_result.dimensions:
        weight = dimension_weights.get(dim.dimension, 0.2)  # Default weight if not found
        weighted_sum += dim.score * weight
    
    llm_result.overall_score = round(weighted_sum, 2)
    
    # Determine confidence level
    if llm_result.overall_score >= 0.8:
        llm_result.confidence = "High"
    elif llm_result.overall_score >= 0.6:
        llm_result.confidence = "Medium"
    else:
        llm_result.confidence = "Low"
    
    return llm_result
