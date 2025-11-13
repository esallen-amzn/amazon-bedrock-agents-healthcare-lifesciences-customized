"""
Integration test for AWS checker with the main test infrastructure.

This test verifies that the AWS checker integrates properly with
the TestResult and Issue models used by the main test orchestrator.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from models import TestResult, Issue, Fix
from checkers.aws_checker_adapter import AWSCheckerAdapter


def test_aws_checker_integration():
    """Test AWS checker integration with main test infrastructure."""
    print("=" * 60)
    print("AWS Checker Integration Test")
    print("=" * 60)
    
    # Initialize checker adapter
    project_root = Path(__file__).parent.parent
    checker = AWSCheckerAdapter(str(project_root))
    
    # Run check
    print("\n1. Running AWS connectivity check...")
    test_result = checker.check(quick_mode=True)
    
    # Display results
    print("\n2. Test Result:")
    print(f"   Checker: {test_result.checker_name}")
    print(f"   Status: {test_result.status}")
    print(f"   Message: {test_result.message}")
    print(f"   Issues: {len(test_result.issues)}")
    print(f"   Fixes: {len(test_result.fixes)}")
    
    if test_result.issues:
        print("\n3. Issues Found:")
        for i, issue in enumerate(test_result.issues, 1):
            print(f"\n   Issue {i}:")
            print(f"   - Severity: {issue.severity}")
            print(f"   - Category: {issue.category}")
            print(f"   - Description: {issue.description}")
            print(f"   - Impact: {issue.impact[:100]}...")
    
    if test_result.fixes:
        print("\n4. Suggested Fixes:")
        for i, fix in enumerate(test_result.fixes, 1):
            print(f"\n   Fix {i}:")
            print(f"   - ID: {fix.issue_id}")
            print(f"   - Command: {fix.command}")
            print(f"   - Risk Level: {fix.risk_level}")
    
    print("\n" + "=" * 60)
    print("Integration Test Complete")
    print("=" * 60)
    
    # Return success if no critical issues or if status is WARNING (expected without credentials)
    if test_result.status in ["PASS", "WARNING"]:
        print("✅ Integration test PASSED")
        return 0
    else:
        print("❌ Integration test FAILED")
        return 1


if __name__ == "__main__":
    try:
        exit_code = test_aws_checker_integration()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
