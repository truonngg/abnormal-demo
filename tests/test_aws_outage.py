"""Test script for AWS outage scenario with new examples in prompt."""
import json
import requests
from pathlib import Path

# Load AWS outage data
data_dir = Path("data/data")

def load_json_file(filename):
    """Load JSON file from data directory."""
    filepath = data_dir / filename
    if filepath.exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return None

def load_text_file(filename):
    """Load text file from data directory."""
    filepath = data_dir / filename
    if filepath.exists():
        with open(filepath, 'r') as f:
            return f.read()
    return None

# Prepare test payload for AWS outage
incident_data = {
    "phase": "investigating",
    "incident_context": load_text_file("aws_outage_context.txt"),
    "cloudwatch_logs": load_json_file("aws_outage_cloudwatch.json"),
    "prometheus_metrics": load_json_file("aws_outage_prometheus.json"),
    "pagerduty_incident": load_json_file("aws_outage_pagerduty.json"),
    "github_deployments": load_json_file("aws_outage_github.json")
}

print("=" * 80)
print("Testing AWS Outage Scenario - Full Pipeline")
print("=" * 80)
print(f"\nPhase: {incident_data['phase']}")
print(f"Scenario: AWS S3 regional outage affecting file uploads/downloads")
print(f"Data sources loaded:")
for key, value in incident_data.items():
    if key != "phase" and value is not None:
        print(f"  ✓ {key}")

print("\n" + "=" * 80)
print("STAGE 1: Extract Evidence...")
print("=" * 80)

try:
    # Stage 1: Extract evidence
    response = requests.post(
        "http://localhost:8000/api/extract-evidence",
        json=incident_data,
        timeout=60
    )
    
    if response.status_code == 200:
        evidence = response.json()
        print("\n✅ Evidence Extracted!")
        print(f"\nIncident: {evidence['incident_metadata']['title']}")
        print(f"Severity: {evidence['incident_metadata']['severity']}")
        print(f"Symptoms: {len(evidence['customer_symptoms'])} found")
        print(f"Internal terms to avoid: {len(evidence['internal_terms_to_avoid'])} found")
        
        print("\n" + "=" * 80)
        print("STAGE 2: Generate Draft...")
        print("=" * 80)
        
        # Stage 2: Generate draft from evidence
        gen_response = requests.post(
            "http://localhost:8000/api/generate-from-evidence",
            json=evidence,
            timeout=60
        )
        
        if gen_response.status_code == 200:
            draft = gen_response.json()
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
                print(f"\n  {i}. \"{mapping['generated_text'][:60]}...\"" if len(mapping['generated_text']) > 60 else f"\n  {i}. \"{mapping['generated_text']}\"")
                print(f"     Source: {mapping['evidence_field']}")
                if mapping.get('original_technical_term'):
                    print(f"     Translation: {mapping['original_technical_term']} → {mapping['customer_facing_term']}")
            
            if draft['internal_terms_avoided']:
                print(f"\n🚫 Internal Terms Avoided ({len(draft['internal_terms_avoided'])} found):")
                for term in draft['internal_terms_avoided']:
                    print(f"  - {term}")
            
            # Check for internal term leakage
            print("\n🔍 Internal Term Leakage Check:")
            leaked_terms = []
            for term in evidence['internal_terms_to_avoid']:
                if term.lower() in draft['message'].lower():
                    leaked_terms.append(term)
            
            if leaked_terms:
                print(f"  ⚠️  WARNING: {len(leaked_terms)} internal term(s) found in message:")
                for term in leaked_terms:
                    print(f"     - {term}")
            else:
                print("  ✅ No internal terms leaked into customer message!")
                
        else:
            print(f"\n❌ GENERATION ERROR: {gen_response.status_code}")
            print(f"Response: {gen_response.text}")
    else:
        print(f"\n❌ EXTRACTION ERROR: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"\n❌ EXCEPTION: {str(e)}")

print("\n" + "=" * 80)
