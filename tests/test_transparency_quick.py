"""
Quick test to verify transparency fields are in the schema.
Tests the schema without calling the full LLM pipeline.
"""

import sys
sys.path.insert(0, 'backend')

from backend.models.schemas import DraftResponse, EvidenceMapping
from pydantic import ValidationError


def test_schema():
    """Test that DraftResponse has all required transparency fields."""
    print("=" * 80)
    print("Quick Schema Verification Test")
    print("=" * 80)
    print()
    
    # Check that DraftResponse has the new fields
    print("Checking DraftResponse schema...")
    schema = DraftResponse.model_json_schema()
    
    required_transparency_fields = [
        'evidence_mappings',
        'internal_terms_avoided', 
        'extracted_evidence_summary',
        'data_sources_used'
    ]
    
    properties = schema.get('properties', {})
    
    all_present = True
    for field in required_transparency_fields:
        if field in properties:
            print(f"  ✅ {field}: Present in schema")
        else:
            print(f"  ❌ {field}: MISSING from schema!")
            all_present = False
    
    print()
    
    if all_present:
        print("✅ All transparency fields are present in DraftResponse schema!")
        print()
        print("Field details:")
        for field in required_transparency_fields:
            field_schema = properties[field]
            print(f"  - {field}:")
            print(f"    Type: {field_schema.get('type', field_schema.get('anyOf', 'complex'))}")
            if 'description' in field_schema:
                print(f"    Description: {field_schema['description']}")
        print()
        print("✅ Schema verification PASSED")
        print()
        print("Note: To test with real data, run test_transparency_output.py")
        print("(Warning: Takes 2-3 minutes due to GPT-5 in generation stage)")
        return True
    else:
        print("❌ Schema verification FAILED - missing fields")
        return False


if __name__ == "__main__":
    success = test_schema()
    sys.exit(0 if success else 1)
