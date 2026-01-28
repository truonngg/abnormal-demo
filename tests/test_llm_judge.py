"""
Test script for LLM-as-Judge evaluation endpoint.

This script tests the /api/evaluate-with-llm-judge endpoint with various test cases:
1. Good draft (should score high across all dimensions)
2. Draft with poor tone (should score low on tone consistency)
3. Draft with unsupported claims (should score low on factual grounding)
4. Draft with wrong phase messaging (should score low on phase appropriateness)
"""

import requests
import json
from typing import Dict, Any

# Base URL for the API
BASE_URL = "http://localhost:8000/api"


def create_sample_evidence(phase: str = "investigating", internal_terms: list = None) -> Dict[str, Any]:
    """Create sample ExtractedEvidence for testing."""
    if internal_terms is None:
        internal_terms = []
    
    return {
        "phase": phase,
        "incident_metadata": {
            "title": "API Performance Issue",
            "severity": "SEV-2",
            "incident_start_time": "2024-01-27 2:30 PM PT",
            "affected_service": "API"
        },
        "customer_symptoms": [
            {
                "symptom": "Slow API response times",
                "confidence": "high",
                "evidence_sources": ["PagerDuty: p99 latency increased to 8 seconds"]
            }
        ],
        "investigation_status": {
            "root_cause_identified": False,
            "diagnosis_summary": None,
            "mitigation_action": "Investigating the issue",
            "expected_resolution": None,
            "next_update_timing": "within 30 minutes"
        },
        "internal_terms_to_avoid": internal_terms,
        "supporting_evidence": None,
        "timeline_events": []
    }


def create_sample_draft(
    title: str,
    status: str,
    message: str,
    next_update: str = "Within 30 minutes"
) -> Dict[str, Any]:
    """Create sample GeneratedDraft for testing."""
    return {
        "title": title,
        "status": status,
        "message": message,
        "next_update": next_update,
        "evidence_mappings": [
            {
                "generated_text": "Sample mapping",
                "evidence_field": "customer_symptoms[0]",
                "original_technical_term": "Slow API response times",
                "customer_facing_term": "slower than normal response"
            }
        ],
        "internal_terms_avoided": [],
        "confidence_notes": None
    }


def test_llm_judge(test_name: str, draft: Dict[str, Any], evidence: Dict[str, Any]) -> None:
    """Test the /api/evaluate-with-llm-judge endpoint."""
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}\n")
    
    print(f"Draft Message:\n{'-'*80}")
    print(draft['message'])
    print(f"{'-'*80}\n")
    
    try:
        # Prepare payload
        payload = {
            "draft": draft,
            "evidence": evidence
        }
        
        # Make request
        response = requests.post(
            f"{BASE_URL}/evaluate-with-llm-judge",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return
        
        result = response.json()
        
        # Display results
        print(f"Overall Score: {result['overall_score']:.2f}/1.0")
        print(f"Confidence: {result['confidence']}")
        print(f"\nOverall Rationale: {result['overall_rationale']}")
        print()
        
        # Show each dimension
        print("Dimension Scores:")
        print("-" * 80)
        for dim in result['dimensions']:
            status_icon = "✅" if dim['status'] == "pass" else ("⚠️" if dim['status'] == "warning" else "❌")
            print(f"{status_icon} {dim['dimension']}: {dim['score']:.2f} ({dim['status'].upper()})")
            print(f"   Rationale: {dim['rationale']}")
            if dim.get('improvement_suggestion'):
                print(f"   💡 Improvement: {dim['improvement_suggestion']}")
            print()
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out (120s)")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the backend. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def main():
    """Run all LLM-as-Judge tests."""
    print("="*80)
    print("Testing LLM-as-Judge Evaluation Endpoint")
    print("="*80)
    
    # Test 1: Good draft (should score high)
    print("\n\n")
    good_draft = create_sample_draft(
        title="API Performance Degradation",
        status="Investigating",
        message=(
            "We are currently investigating reports of slower than normal API response times. "
            "Some customers may experience delays when making API calls. Our engineering team "
            "is actively investigating the issue and working to restore normal performance. "
            "We will provide an update within 30 minutes or as soon as we have more information. "
            "Thank you for your patience."
        )
    )
    test_llm_judge(
        "Test 1: Good Draft (should score high across all dimensions)",
        draft=good_draft,
        evidence=create_sample_evidence()
    )
    
    # Test 2: Draft with poor tone (should score low on tone)
    print("\n\n")
    poor_tone_draft = create_sample_draft(
        title="System Issues",
        status="Investigating",
        message=(
            "Our systems are down. We're working on it. Check back later."
        )
    )
    test_llm_judge(
        "Test 2: Draft with Poor Tone (should score low on tone consistency)",
        draft=poor_tone_draft,
        evidence=create_sample_evidence()
    )
    
    # Test 3: Draft with unsupported claims (should score low on factual grounding)
    print("\n\n")
    hallucination_draft = create_sample_draft(
        title="Network Configuration Issue",
        status="Identified",
        message=(
            "We've identified the root cause as a network misconfiguration in our AWS us-east-1 "
            "region affecting the kubernetes ingress controller. The issue originated from a recent "
            "deployment to our api-gateway service which caused connection pool exhaustion. We are "
            "rolling back the deployment and expect resolution within 15 minutes."
        )
    )
    test_llm_judge(
        "Test 3: Draft with Unsupported Technical Claims (should score low on factual grounding)",
        draft=hallucination_draft,
        evidence=create_sample_evidence(phase="identified")
    )
    
    # Test 4: Wrong phase messaging (should score low on phase appropriateness)
    print("\n\n")
    wrong_phase_draft = create_sample_draft(
        title="API Performance Issue - Resolved",
        status="Investigating",
        message=(
            "The API performance issue has been fully resolved and all systems are operating "
            "normally. This incident lasted 2 hours and was caused by increased load. We "
            "apologize for any inconvenience. Thank you for your patience."
        )
    )
    test_llm_judge(
        "Test 4: Wrong Phase Messaging (resolved message during investigating)",
        draft=wrong_phase_draft,
        evidence=create_sample_evidence(phase="investigating")
    )
    
    # Test 5: Draft with excessive technical jargon
    print("\n\n")
    jargon_draft = create_sample_draft(
        title="API Service Degradation",
        status="Investigating",
        message=(
            "We are experiencing degraded p99 latency metrics across our RESTful API endpoints. "
            "The issue appears correlated with elevated heap memory utilization on our application "
            "servers. Our SRE team is analyzing JVM garbage collection logs and thread dumps to "
            "identify potential memory leaks or blocked threads in the connection pool."
        )
    )
    test_llm_judge(
        "Test 5: Draft with Excessive Technical Jargon (should score low on technical balance)",
        draft=jargon_draft,
        evidence=create_sample_evidence()
    )
    
    print("\n" + "="*80)
    print("Testing Complete!")
    print("="*80)


if __name__ == "__main__":
    main()
