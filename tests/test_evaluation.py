"""
Test script for evaluation endpoint (Stage 3: Deterministic Quality Checks).

This script tests the /api/evaluate-draft endpoint with various test cases:
1. Good draft (should pass all checks)
2. Draft with internal term leak (should fail Check 2)
3. Draft that's too short (should fail Check 1)
4. Investigating draft claiming root cause (should fail Check 4)
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
            "title": "Test Incident",
            "severity": "SEV-1",
            "incident_start_time": "2024-01-27 10:00 AM PT",
            "affected_service": "API"
        },
        "customer_symptoms": [
            {
                "symptom": "High API latency",
                "confidence": "high",
                "evidence_sources": ["PagerDuty: p99 latency > 5s"]
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
    title: str = "Investigating: Service issue",
    status: str = "Investigating",
    message: str = None,
    next_update: str = "Within 30 minutes"
) -> Dict[str, Any]:
    """Create sample GeneratedDraft for testing."""
    if message is None:
        message = (
            "We are aware of an issue affecting some customers that may cause slower-than-normal "
            "responses or intermittent service disruptions. Our team is actively investigating and "
            "working to restore normal service. We will provide an update within 30 minutes or "
            "sooner if we have more information. Thank you for your patience."
        )
    
    return {
        "title": title,
        "status": status,
        "message": message,
        "next_update": next_update,
        "evidence_mappings": [
            {
                "generated_text": "We are aware of an issue",
                "evidence_field": "customer_symptoms[0]",
                "original_technical_term": "High API latency",
                "customer_facing_term": "slower-than-normal responses"
            }
        ],
        "internal_terms_avoided": [],
        "confidence_notes": None
    }


def test_evaluate_draft(test_name: str, draft: Dict[str, Any], evidence: Dict[str, Any]) -> None:
    """Test the /api/evaluate-draft endpoint."""
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}\n")
    
    try:
        # Prepare payload combining both draft and evidence
        # Since FastAPI expects two separate body parameters, we need to structure this properly
        payload = {
            "draft": draft,
            "evidence": evidence
        }
        
        # Make request with JSON body
        response = requests.post(
            f"{BASE_URL}/evaluate-draft",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return
        
        result = response.json()
        
        # Display results
        print(f"Overall Status: {result['overall_status'].upper()}")
        print(f"Passed: {result['passed_checks']}, Failed: {result['failed_checks']}, Warnings: {result['warning_checks']}")
        print()
        
        # Show each check
        for check in result['deterministic_checks']:
            status_icon = "✅" if check['status'] == "pass" else ("⚠️" if check['status'] == "warning" else "❌")
            print(f"{status_icon} {check['check_name']}: {check['status'].upper()}")
            print(f"   {check['details']}")
            if check.get('actionable_fix'):
                print(f"   💡 Fix: {check['actionable_fix']}")
            print()
        
        if result['warnings']:
            print("⚠️ Warnings:")
            for warning in result['warnings']:
                print(f"   - {warning}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the backend. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def main():
    """Run all evaluation tests."""
    print("="*80)
    print("Testing Evaluation Endpoint (Stage 3: Deterministic Quality Checks)")
    print("="*80)
    
    # Test 1: Good draft (should pass all checks)
    print("\n\n")
    test_evaluate_draft(
        "Test 1: Good Draft (should pass all checks)",
        draft=create_sample_draft(),
        evidence=create_sample_evidence()
    )
    
    # Test 2: Draft with internal term leak (should fail Check 2)
    print("\n\n")
    leaked_message = (
        "We are investigating an issue with our api-gateway service that is causing "
        "slower-than-normal responses. Our team is working to restore normal service. "
        "We will provide an update within 30 minutes."
    )
    test_evaluate_draft(
        "Test 2: Draft with Internal Term Leak (should fail Check 2)",
        draft=create_sample_draft(message=leaked_message),
        evidence=create_sample_evidence(internal_terms=["api-gateway", "k8s", "pod"])
    )
    
    # Test 3: Draft that's too short (should fail Check 1)
    print("\n\n")
    short_message = "We are investigating an issue. Update soon."
    test_evaluate_draft(
        "Test 3: Draft Too Short (should fail Check 1)",
        draft=create_sample_draft(message=short_message),
        evidence=create_sample_evidence()
    )
    
    # Test 4: Investigating draft claiming root cause (should fail Check 4)
    print("\n\n")
    root_cause_message = (
        "We are aware of an issue caused by a database connection pool exhaustion "
        "that is affecting some customers. The root cause has been identified and "
        "our team is working to restore normal service. We will provide an update "
        "within 30 minutes."
    )
    test_evaluate_draft(
        "Test 4: Investigating Draft Claiming Root Cause (should fail Check 4)",
        draft=create_sample_draft(message=root_cause_message),
        evidence=create_sample_evidence(phase="investigating")
    )
    
    # Test 5: Draft that's too long (should fail Check 1)
    print("\n\n")
    long_message = (
        "We are currently investigating reports of a service disruption that may be affecting "
        "some of our customers. The issue appears to be causing slower-than-normal response times "
        "and intermittent service disruptions across multiple regions. Our engineering team has been "
        "mobilized and is actively working to identify the root cause of this problem. We are monitoring "
        "all of our systems and infrastructure components to ensure we can quickly identify and resolve "
        "the issue. We understand the critical nature of this situation and are treating it with the "
        "highest priority. Our team is working around the clock to restore normal service as quickly as "
        "possible. We will continue to provide regular updates every 30 minutes or sooner as we have "
        "more information to share. We sincerely apologize for any inconvenience this may be causing "
        "to your operations and appreciate your patience as we work to resolve this matter. Thank you "
        "for your understanding and continued trust in our service."
    )
    test_evaluate_draft(
        "Test 5: Draft Too Long (should fail Check 1)",
        draft=create_sample_draft(message=long_message),
        evidence=create_sample_evidence()
    )
    
    print("\n" + "="*80)
    print("Testing Complete!")
    print("="*80)


if __name__ == "__main__":
    main()
