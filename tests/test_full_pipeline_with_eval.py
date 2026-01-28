"""
Test the full pipeline with integrated evaluation.

This tests the /api/generate-draft endpoint to verify that evaluation results
are properly included in the response.
"""

import requests
import json
from pathlib import Path

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


def test_generate_draft_with_evaluation():
    """Test the /generate-draft endpoint with evaluation."""
    print("=" * 80)
    print("Testing Full Pipeline with Integrated Evaluation")
    print("=" * 80)
    print()
    
    # Load incident data
    files_data = load_incident_files()
    
    # Prepare request payload
    payload = {
        "phase": "investigating",
        **files_data
    }
    
    print("Calling /api/generate-draft...")
    print()
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate-draft",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return
        
        result = response.json()
        
        # Display draft
        print("=" * 80)
        print("GENERATED DRAFT")
        print("=" * 80)
        print()
        print(f"Title: {result['title']}")
        print(f"Status: {result['status']}")
        print()
        print("Message:")
        print("-" * 80)
        print(result['message'])
        print("-" * 80)
        print()
        print(f"Next Update: {result['next_update']}")
        print()
        
        # Display legacy evaluation metrics
        print("=" * 80)
        print("LEGACY EVALUATION METRICS")
        print("=" * 80)
        print()
        print(f"Confidence Score: {result['confidence_score']:.2f}")
        print(f"Confidence Level: {result['confidence_level']}")
        print(f"Evidence Summary: {result['evidence_summary']}")
        print()
        
        if result.get('warnings'):
            print("⚠️ Warnings:")
            for warning in result['warnings']:
                print(f"  - {warning}")
            print()
        
        # Display new evaluation result
        if result.get('evaluation_result'):
            eval_result = result['evaluation_result']
            print("=" * 80)
            print("DETERMINISTIC EVALUATION RESULTS")
            print("=" * 80)
            print()
            print(f"Overall Status: {eval_result['overall_status'].upper()}")
            print(f"Passed: {eval_result['passed_checks']}, "
                  f"Failed: {eval_result['failed_checks']}, "
                  f"Warnings: {eval_result['warning_checks']}")
            print()
            
            for check in eval_result['deterministic_checks']:
                status_icon = "✅" if check['status'] == "pass" else ("⚠️" if check['status'] == "warning" else "❌")
                print(f"{status_icon} {check['check_name']}: {check['status'].upper()}")
                print(f"   {check['details']}")
                if check.get('actionable_fix'):
                    print(f"   💡 Fix: {check['actionable_fix']}")
                print()
        else:
            print("⚠️ No evaluation_result field found in response")
        
        print("=" * 80)
        print("Test Complete!")
        print("=" * 80)
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out (120s)")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend. Ensure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    test_generate_draft_with_evaluation()
