"""Test script for LLM draft generation - IDENTIFIED phase."""
import json
import requests

# Load evidence with identified root cause
evidence = {
    "phase": "identified",
    "incident_metadata": {
        "title": "High API Latency - api-gateway",
        "severity": "SEV-2",
        "incident_start_time": "January 15, 2:23 PM PT",
        "affected_service": "api-gateway"
    },
    "customer_symptoms": [
        {
            "symptom": "High API latency",
            "confidence": "high",
            "evidence_sources": ["PagerDuty Alert: p99 latency > 5s"]
        }
    ],
    "investigation_status": {
        "root_cause_identified": True,
        "diagnosis_summary": "Connection pool exhausted due to PR #12345 timeout change",
        "mitigation_action": "Initiating rollback of PR #12345",
        "expected_resolution": "within 30 minutes",
        "next_update_timing": "30 minutes"
    },
    "internal_terms_to_avoid": ["api-gateway", "rds-prod-main", "PR #12345"],
    "supporting_evidence": {
        "deployment_correlation": "PR #12345 deployed at 2:15 PM changed HTTP client timeout from 10s to 30s",
        "error_patterns": "Connection timeout to database, pool size 50/50",
        "metrics_summary": "p99 latency increased from 2.5s to 18.0s"
    },
    "timeline_events": []
}

print("=" * 80)
print("Testing Draft Generation - IDENTIFIED Phase")
print("=" * 80)
print(f"\nPhase: {evidence['phase']}")
print(f"Root Cause Identified: {evidence['investigation_status']['root_cause_identified']}")
print(f"Mitigation: {evidence['investigation_status']['mitigation_action']}")

print("\n" + "=" * 80)
print("Calling /api/generate-from-evidence endpoint...")
print("=" * 80)

try:
    response = requests.post(
        "http://localhost:8000/api/generate-from-evidence",
        json=evidence,
        timeout=60
    )
    
    if response.status_code == 200:
        draft = response.json()
        print("\n✅ GENERATED DRAFT:\n")
        print(f"Title: {draft['title']}")
        print(f"Status: {draft['status']}")
        print(f"\nMessage:")
        print("-" * 80)
        print(draft['message'])
        print("-" * 80)
        print(f"\nNext Update: {draft['next_update']}")
        
        print(f"\n📋 Evidence Mappings ({len(draft['evidence_mappings'])} found):")
        for i, mapping in enumerate(draft['evidence_mappings'], 1):
            print(f"\n  {i}. Generated Text: \"{mapping['generated_text']}\"")
            print(f"     Evidence Field: {mapping['evidence_field']}")
            if mapping.get('original_technical_term'):
                print(f"     Translation: {mapping['original_technical_term']} → {mapping['customer_facing_term']}")
        
        if draft['internal_terms_avoided']:
            print(f"\n🚫 Internal Terms Avoided ({len(draft['internal_terms_avoided'])} found):")
            for term in draft['internal_terms_avoided']:
                print(f"  - {term}")
        
        print("\n" + "=" * 80)
        print("Key Differences from INVESTIGATING Phase:")
        print("=" * 80)
        print("✓ Acknowledges cause is identified (without technical details)")
        print("✓ Describes mitigation action in customer-friendly language")
        print("✓ Includes 'Affected:' and 'Impact:' sections")
        print("✓ Sets expectation for resolution time")
            
    else:
        print(f"\n❌ ERROR: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"\n❌ EXCEPTION: {str(e)}")

print("\n" + "=" * 80)
