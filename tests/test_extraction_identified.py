"""Test script for LLM evidence extraction - IDENTIFIED phase."""
import json
import requests
from pathlib import Path

# Load sample data
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

# Prepare test payload for IDENTIFIED phase
incident_data = {
    "phase": "identified",  # Changed to identified
    "incident_context": load_text_file("incident_context.txt"),
    "cloudwatch_logs": load_json_file("cloudwatch_logs.json"),
    "prometheus_metrics": load_json_file("prometheus_metrics.json"),
    "pagerduty_incident": load_json_file("pagerduty_incident.json"),
    "github_deployments": load_json_file("github_deployments.json")
}

print("=" * 80)
print("Testing LLM Evidence Extraction - IDENTIFIED PHASE")
print("=" * 80)
print(f"\nPhase: {incident_data['phase']} (Root cause should be identified)")
print(f"Data sources loaded:")
for key, value in incident_data.items():
    if key != "phase" and value is not None:
        print(f"  ✓ {key}")

print("\n" + "=" * 80)
print("Calling /api/extract-evidence endpoint...")
print("=" * 80)

try:
    response = requests.post(
        "http://localhost:8000/api/extract-evidence",
        json=incident_data,
        timeout=60
    )
    
    if response.status_code == 200:
        evidence = response.json()
        print("\n✅ SUCCESS! Evidence extracted:\n")
        print(json.dumps(evidence, indent=2))
        
        print("\n" + "=" * 80)
        print("Key Differences from INVESTIGATING Phase:")
        print("=" * 80)
        
        print(f"\n🔍 Root Cause Analysis:")
        print(f"  Root Cause Identified: {evidence['investigation_status']['root_cause_identified']}")
        if evidence['investigation_status']['diagnosis_summary']:
            print(f"  ✓ Diagnosis: {evidence['investigation_status']['diagnosis_summary']}")
        
        if evidence['investigation_status']['mitigation_action']:
            print(f"\n🔧 Mitigation:")
            print(f"  ✓ Action: {evidence['investigation_status']['mitigation_action']}")
        
        if evidence['investigation_status']['expected_resolution']:
            print(f"  ✓ Expected Resolution: {evidence['investigation_status']['expected_resolution']}")
        
        print(f"\n📊 Customer Symptoms ({len(evidence['customer_symptoms'])} found):")
        for symptom in evidence['customer_symptoms']:
            print(f"  - {symptom['symptom']} (confidence: {symptom['confidence']})")
            
    else:
        print(f"\n❌ ERROR: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"\n❌ EXCEPTION: {str(e)}")

print("\n" + "=" * 80)
