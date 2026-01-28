"""
Test script to verify transparency features in the final output.

This script tests that the /api/generate-draft endpoint includes:
1. Evidence mappings (what evidence supported each claim)
2. Internal terms avoided
3. Extracted evidence summary
4. Data sources used
5. Quality evaluation results (deterministic + LLM-as-Judge)
"""

import requests
import json
from pathlib import Path
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api"
DATA_DIR = Path("data/data")


def load_incident_files():
    """Load AWS outage incident files."""
    files_data = {}
    
    # Load all test data files
    test_files = [
        "test_data/aws_outage_pagerduty.json",
        "test_data/aws_outage_context.txt",
        "test_data/aws_outage_cloudwatch.json",
        "test_data/aws_outage_prometheus.json",
        "test_data/aws_outage_github.json"
    ]
    
    for file_path in test_files:
        full_path = DATA_DIR / file_path
        if full_path.exists():
            if file_path.endswith('.json'):
                with open(full_path, 'r') as f:
                    content = json.load(f)
                    if 'pagerduty' in file_path:
                        files_data['pagerduty_incident'] = content
                    elif 'cloudwatch' in file_path:
                        files_data['cloudwatch_logs'] = content
                    elif 'prometheus' in file_path:
                        files_data['prometheus_metrics'] = content
                    elif 'github' in file_path:
                        files_data['github_deployments'] = content
            else:
                with open(full_path, 'r') as f:
                    files_data['incident_context'] = f.read()
    
    return files_data


def format_transparency_report(response: Dict[str, Any]) -> str:
    """Format transparency features into a readable report."""
    report = []
    
    report.append("=" * 80)
    report.append("TRANSPARENCY REPORT")
    report.append("=" * 80)
    report.append("")
    
    # Draft Content
    report.append("DRAFT MESSAGE")
    report.append("-" * 80)
    report.append(f"Title: {response['title']}")
    report.append(f"Status: {response['status']}")
    report.append(f"Next Update: {response['next_update']}")
    report.append("")
    report.append("Message:")
    report.append(response['message'])
    report.append("")
    
    # Data Sources Used
    report.append("=" * 80)
    report.append("DATA SOURCES USED")
    report.append("-" * 80)
    for source in response.get('data_sources_used', []):
        report.append(f"  ✓ {source}")
    report.append("")
    
    # Extracted Evidence Summary
    report.append("=" * 80)
    report.append("EXTRACTED EVIDENCE SUMMARY")
    report.append("-" * 80)
    evidence = response.get('extracted_evidence_summary', {})
    report.append(f"Phase: {evidence.get('phase', 'N/A')}")
    report.append(f"Severity: {evidence.get('incident_metadata', {}).get('severity', 'N/A')}")
    report.append(f"Affected Service: {evidence.get('incident_metadata', {}).get('affected_service', 'N/A')}")
    report.append(f"Start Time: {evidence.get('incident_metadata', {}).get('start_time', 'N/A')}")
    report.append(f"Customer Symptoms: {evidence.get('customer_symptoms_count', 0)}")
    report.append(f"Root Cause Identified: {evidence.get('root_cause_identified', False)}")
    report.append(f"Internal Terms to Avoid: {evidence.get('internal_terms_to_avoid_count', 0)}")
    
    if evidence.get('customer_symptoms'):
        report.append("")
        report.append("Customer Symptoms Details:")
        for i, symptom in enumerate(evidence['customer_symptoms'], 1):
            report.append(f"  {i}. {symptom['symptom']} (confidence: {symptom['confidence']})")
            report.append(f"     Sources: {', '.join(symptom['evidence_sources'])}")
    report.append("")
    
    # Evidence Mappings
    report.append("=" * 80)
    report.append("EVIDENCE MAPPINGS (Message → Evidence)")
    report.append("-" * 80)
    mappings = response.get('evidence_mappings', [])
    report.append(f"Total mappings: {len(mappings)}")
    report.append("")
    for i, mapping in enumerate(mappings, 1):
        report.append(f"{i}. Generated Text:")
        report.append(f"   \"{mapping['generated_text']}\"")
        report.append(f"   → Evidence Field: {mapping['evidence_field']}")
        if mapping.get('original_technical_term'):
            report.append(f"   → Translation: \"{mapping['original_technical_term']}\"")
            report.append(f"      → \"{mapping.get('customer_facing_term', 'N/A')}\"")
        report.append("")
    
    # Internal Terms Avoided
    report.append("=" * 80)
    report.append("INTERNAL TERMS AVOIDED")
    report.append("-" * 80)
    internal_terms = response.get('internal_terms_avoided', [])
    if internal_terms:
        report.append(f"Successfully avoided {len(internal_terms)} internal terms:")
        for term in internal_terms:
            report.append(f"  • {term}")
    else:
        report.append("No internal terms were identified or all were properly translated.")
    report.append("")
    
    # Quality Evaluation
    report.append("=" * 80)
    report.append("QUALITY EVALUATION")
    report.append("-" * 80)
    report.append(f"Overall Confidence: {response.get('confidence_score', 0):.2f} ({response.get('confidence_level', 'N/A')})")
    report.append("")
    
    # Deterministic Checks
    eval_result = response.get('evaluation_result', {})
    if eval_result:
        report.append("Deterministic Checks:")
        report.append(f"  Passed: {eval_result.get('passed_checks', 0)}")
        report.append(f"  Failed: {eval_result.get('failed_checks', 0)}")
        report.append(f"  Warnings: {eval_result.get('warning_checks', 0)}")
        report.append(f"  Overall: {eval_result.get('overall_status', 'N/A').upper()}")
        
        if eval_result.get('deterministic_checks'):
            report.append("")
            for check in eval_result['deterministic_checks']:
                status_icon = "✅" if check['status'] == "pass" else ("⚠️" if check['status'] == "warning" else "❌")
                report.append(f"  {status_icon} {check['check_name']}: {check['status'].upper()}")
        
        # LLM-as-Judge Results
        llm_judge = eval_result.get('llm_judge_result')
        if llm_judge:
            report.append("")
            report.append("LLM-as-Judge Evaluation:")
            report.append(f"  Overall Score: {llm_judge.get('overall_score', 0):.2f}")
            report.append(f"  Confidence: {llm_judge.get('confidence', 'N/A')}")
            
            if llm_judge.get('dimensions'):
                report.append("")
                report.append("  Dimension Scores:")
                for dim in llm_judge['dimensions']:
                    status_icon = "✅" if dim['status'] == "pass" else ("⚠️" if dim['status'] == "warning" else "❌")
                    report.append(f"    {status_icon} {dim['dimension']}: {dim['score']:.2f}")
    
    report.append("")
    report.append("=" * 80)
    
    return "\n".join(report)


def test_transparency():
    """Test the transparency features in the API response."""
    print("=" * 80)
    print("Testing Transparency Features in /api/generate-draft")
    print("=" * 80)
    print()
    
    # Load incident data
    print("Loading AWS outage test data...")
    files_data = load_incident_files()
    
    # Prepare request payload
    payload = {
        "phase": "investigating",
        **files_data
    }
    
    print(f"Loaded {len(files_data)} data sources")
    print()
    print("Calling /api/generate-draft (this may take 2-3 minutes with GPT-5 + GPT-5-mini)...")
    print()
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate-draft",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300  # 5 minutes timeout for GPT-5
        )
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return
        
        result = response.json()
        
        # Verify all transparency fields are present
        print("✅ Request successful!")
        print()
        
        required_fields = [
            'evidence_mappings',
            'internal_terms_avoided',
            'extracted_evidence_summary',
            'data_sources_used'
        ]
        
        print("Verifying transparency fields...")
        for field in required_fields:
            if field in result:
                print(f"  ✅ {field}: Present")
            else:
                print(f"  ❌ {field}: MISSING!")
        print()
        
        # Display formatted transparency report
        report = format_transparency_report(result)
        print(report)
        
        # Save full response to file for inspection
        output_file = "transparency_output.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print()
        print(f"💾 Full response saved to: {output_file}")
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out (5 minutes)")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend. Ensure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    test_transparency()
