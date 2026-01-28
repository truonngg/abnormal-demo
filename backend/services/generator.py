"""Draft generation service using LLM."""
from typing import Dict, Any, List
import os
import httpx
from openai import OpenAI
from ..models.schemas import ExtractedEvidence, GeneratedDraft


def get_style_guidelines() -> Dict[str, str]:
    """Return the specific style guidelines from status_page_examples.md."""
    return {
        "tone": """- Professional and empathetic
- Direct and honest without over-sharing
- Avoid technical jargon
- Focus on customer impact, not internal details""",
        
        "must_contain": """- What is happening (customer-observable symptoms)
- What is affected
- What we are doing about it
- When to expect next update or resolution""",
        
        "must_exclude": """- Internal system names (unless customer-facing)
- Technical root cause details ("connection pool exhaustion", "Redis cache miss")
- Blame or specific engineer names
- Speculation or unconfirmed information
- Overly technical metrics ("p99 latency 15s" → "significantly slower response times")""",
        
        "update_frequency": "Regular updates: Every 30-60 minutes during active incidents"
    }


def build_generation_prompt(evidence: ExtractedEvidence) -> str:
    """
    Build phase-specific generation prompt with evidence and style guidelines.
    
    Args:
        evidence: Extracted evidence from Stage 1
        
    Returns:
        Complete generation prompt
    """
    guidelines = get_style_guidelines()
    phase = evidence.phase.lower()
    
    # Phase-specific instructions with examples
    phase_instructions = {
        "investigating": """
INVESTIGATING PHASE REQUIREMENTS:
- Acknowledge awareness of the issue
- Describe customer-observable symptoms (translate technical terms)
- State that investigation is underway
- Set expectation for next update (typically 30 minutes)
- DO NOT mention root cause (not known yet)
- DO NOT mention specific fixes

EXAMPLE (demonstrates appropriate tone, structure, and level of detail):
"We are currently investigating reports of slower than normal API response times. Some customers may experience delays when making API calls. Our engineering team is actively investigating the issue.

We will provide an update within 30 minutes or as soon as we have more information."
""",
        "identified": """
IDENTIFIED PHASE REQUIREMENTS:
- Acknowledge the cause has been identified (WITHOUT technical details)
- State that work is in progress to resolve the issue (customer-friendly language)
- DO NOT describe HOW you are fixing it or specific mitigation steps
- Describe ongoing customer impact during the fix
- Set expectation for resolution time
- Include "Affected:" and "Impact:" sections
- Translate technical diagnosis to customer impact

EXAMPLE (demonstrates appropriate tone, structure, and level of detail):
"We have identified the cause of the API performance issues. Our engineering team is working to resolve it. API calls may continue to experience increased response times during this work.

Affected: API endpoints
Impact: Increased response times, some timeouts may occur

We expect to have this resolved within 30 minutes and will provide updates as we make progress."
""",
        "monitoring": """
MONITORING PHASE REQUIREMENTS:
- Confirm fix has been deployed
- State that metrics are returning to normal
- Mention ongoing monitoring period
- Set expectation for when incident will be marked resolved

EXAMPLE (demonstrates appropriate tone, structure, and level of detail):
"We have implemented a fix and API response times are returning to normal. We are monitoring the system to ensure stability.

Most customers should see normal performance resuming. We will continue monitoring for the next hour before marking this incident as fully resolved."
""",
        "resolved": """
RESOLVED PHASE REQUIREMENTS:
- Confirm incident is resolved and system is stable
- Include SUMMARY section with:
  - Incident start time
  - Resolution time
  - Total duration
  - Impact description (what was affected, for how long)
- Apologize for inconvenience
- Offer support contact if issues persist

EXAMPLE (demonstrates appropriate tone, structure, and level of detail):
"This incident has been resolved. API performance has returned to normal and has remained stable for over 90 minutes.

**Summary**:
- Incident start: ~2:20 PM PT
- Incident resolution: ~3:00 PM PT
- Total duration: ~40 minutes
- Impact: Increased API response times, some requests experienced timeouts

We apologize for any inconvenience this may have caused. If you continue to experience issues, please contact our support team."
"""
    }
    
    # Format evidence for prompt
    symptoms_text = "\n".join([
        f"  - {s.symptom} (confidence: {s.confidence})\n    Sources: {', '.join(s.evidence_sources)}"
        for s in evidence.customer_symptoms
    ])
    
    internal_terms_text = ", ".join(evidence.internal_terms_to_avoid)
    
    prompt = f"""You are an expert at writing customer-appropriate incident status page communications.

PHASE: {evidence.phase.upper()}

{phase_instructions.get(phase, "")}

=== EXTRACTED EVIDENCE ===

INCIDENT METADATA:
- Title: {evidence.incident_metadata.title}
- Severity: {evidence.incident_metadata.severity}
- Start Time: {evidence.incident_metadata.incident_start_time}
- Affected Service: {evidence.incident_metadata.affected_service}

CUSTOMER SYMPTOMS:
{symptoms_text}

INVESTIGATION STATUS:
- Root Cause Identified: {evidence.investigation_status.root_cause_identified}
- Diagnosis: {evidence.investigation_status.diagnosis_summary or "Not yet identified"}
- Mitigation Action: {evidence.investigation_status.mitigation_action or "Investigating"}
- Next Update: {evidence.investigation_status.next_update_timing}

INTERNAL TERMS TO AVOID (must translate or exclude):
{internal_terms_text}

=== STYLE GUIDELINES ===

TONE:
{guidelines['tone']}

MUST CONTAIN:
{guidelines['must_contain']}

MUST EXCLUDE:
{guidelines['must_exclude']}

=== GENERATION INSTRUCTIONS ===

1. Generate a status page message for the {evidence.phase.upper()} phase
2. Translate ALL technical symptoms to customer-facing language:
   - "High API latency" → "slower than normal response times"
   - "Connection timeouts" → "intermittent service disruptions"
   - "5xx errors" → "service unavailability"
3. DO NOT include any internal terms from the list above
4. For EACH piece of information in your message, track which SOURCE FILE/DATA it came from
   - Use the source names from evidence_sources (e.g., "PagerDuty", "CloudWatch Logs", "Incident Context")
   - NOT technical field paths like "customer_symptoms[0]"
   - Example: If symptom came from PagerDuty, use "PagerDuty" as the evidence_field
5. Follow the phase-specific structure and requirements
6. Keep message concise but complete (typically 45-100 words, longer for Resolved phase)

Generate the draft now with proper evidence mappings using source filenames."""

    return prompt


def generate_draft_with_llm(evidence: ExtractedEvidence) -> GeneratedDraft:
    """
    Generate customer-appropriate status page draft using LLM.
    
    Args:
        evidence: Extracted evidence from Stage 1
        
    Returns:
        Generated draft with evidence grounding
    """
    # Build prompt
    prompt = build_generation_prompt(evidence)
    
    # Initialize OpenAI client with extended timeout for LLM calls
    http_client = httpx.Client(timeout=180.0)
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
        http_client=http_client
    )
    
    # Call LLM with structured output
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        temperature=0.3,
        messages=[
            {
                "role": "system",
                "content": "You are an expert at writing clear, empathetic customer incident communications."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format=GeneratedDraft
    )
    
    return response.choices[0].message.parsed


# Keep old function for backward compatibility during migration
def generate_draft(parsed_data: Dict[str, Any]) -> Dict[str, str]:
    """Legacy function - kept for backward compatibility."""
    return {
        "title": "API Performance Degradation",
        "status": "Investigating",
        "message": "We are currently investigating reports of slower than normal response times. "
                   "Our engineering team is actively working to identify the root cause. "
                   "We will provide an update within 30 minutes.",
        "next_update": "within 30 minutes"
    }
