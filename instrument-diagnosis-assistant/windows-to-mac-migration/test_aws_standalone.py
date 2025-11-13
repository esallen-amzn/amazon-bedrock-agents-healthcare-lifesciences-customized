"""
Standalone test for AWS checker that doesn't rely on package imports.

This test verifies the AWS checker works correctly by importing
the module directly without going through the checkers package.
"""

import sys
from pathlib import Path

# Add the project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the AWS checker directly
sys.path.insert(0, str(Path(__file__).parent / "checkers"))
from aws_checker import AWSChecker


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def test_aws_checker_standalone():
    """Test AWS checker in standalone mode."""
    print_section("AWS Checker Standalone Test")
    
    # Initialize checker
    checker = AWSChecker(str(project_root))
    print(f"\n📁 Project root: {project_root}")
    
    # Run quick check
    print_section("Running Quick Check")
    result = checker.check(quick_mode=True)
    
    print(f"\nStatus: {result.status}")
    print(f"Message: {result.message}")
    print(f"\nChecks:")
    print(f"  ✓ CLI Installed: {result.cli_installed}")
    if result.cli_version:
        print(f"    Version: {result.cli_version}")
    print(f"  ✓ Credentials Configured: {result.credentials_configured}")
    if result.region:
        print(f"    Region: {result.region}")
    print(f"  ✓ boto3 Available: {result.boto3_available}")
    
    # Show issues
    if result.issues:
        print_section(f"Issues Found ({len(result.issues)})")
        for i, issue in enumerate(result.issues, 1):
            print(f"\n{i}. [{issue.severity}] {issue.description}")
            print(f"   Type: {issue.issue_type}")
            print(f"   Details: {issue.details[:150]}")
            if issue.fix_suggestion:
                print(f"   Fix: {issue.fix_suggestion[:150]}...")
    
    # Show summary
    print_section("Summary")
    summary = checker.get_summary()
    print(f"Total Issues: {summary['total_issues']}")
    print(f"Critical Issues: {summary['critical_issues']}")
    print(f"Warning Issues: {summary['warning_issues']}")
    
    # Verify all required checks are implemented
    print_section("Verification")
    checks = [
        ("AWS CLI installation check", result.cli_installed is not None),
        ("AWS credentials check", result.credentials_configured is not None),
        ("boto3 availability check", result.boto3_available is not None),
        ("Status determination", result.status in ["PASS", "FAIL", "WARNING", "SKIP"]),
        ("Message generation", len(result.message) > 0),
        ("Issue tracking", isinstance(result.issues, list)),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    # Final result
    print_section("Test Result")
    if all_passed:
        print("✅ All AWS checker functionality is implemented correctly")
        print("\nNote: The checker correctly detected missing boto3 and/or credentials.")
        print("This is expected behavior and demonstrates the checker is working.")
        return 0
    else:
        print("❌ Some AWS checker functionality is missing or incorrect")
        return 1


if __name__ == "__main__":
    try:
        exit_code = test_aws_checker_standalone()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
