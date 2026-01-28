"""Test script for LLM draft generation."""
import json
import requests

# Load evidence from previous extraction test
evidence = {
    "phase": "investigating",
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
            "evidence_sources": ["PagerDuty Alert PXXX123: p99 latency > 5s"]
        },
        {
            "symptom": "Connection timeouts",
            "confidence": "high",
            "evidence_sources": ["CloudWatch logs: Connection timeout to database"]
        }
    ],
    "investigation_status": {
        "root_cause_identified": False,
        "diagnosis_summary": None,
        "mitigation_action": None,
        "expected_resolution": None,
        "next_update_timing": "within 30 minutes"
    },
    "internal_terms_to_avoid": ["api-gateway", "rds-prod-main", "alice.engineer@example.com", "PR #12345"],
    "supporting_evidence": None,
    "timeline_events": []
}

print("=" * 80)
print("Testing Draft Generation - INVESTIGATING Phase")
print("=" * 80)
print(f"\nPhase: {evidence['phase']}")
print(f"Symptoms: {len(evidence['customer_symptoms'])} found")
print(f"Internal terms to avoid: {len(evidence['internal_terms_to_avoid'])} found")

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
        
        if draft.get('confidence_notes'):
            print(f"\n📝 Confidence Notes: {draft['confidence_notes']}")
            
    else:
        print(f"\n❌ ERROR: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"\n❌ EXCEPTION: {str(e)}")

print("\n" + "=" * 80)
