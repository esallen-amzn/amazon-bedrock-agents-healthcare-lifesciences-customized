"""
Test script for AWS connectivity checker.

This script tests the AWS checker module to verify it correctly:
- Detects AWS CLI installation
- Checks AWS credentials configuration
- Tests boto3 client creation
- Verifies SSM parameter access
- Provides appropriate error messages and fix suggestions
"""

import sys
import os
from pathlib import Path

# Add the checkers directory to the path
checkers_dir = Path(__file__).parent / "checkers"
sys.path.insert(0, str(checkers_dir))

# Import directly from the module file
from aws_checker import AWSChecker

# Set project root
project_root = Path(__file__).parent.parent


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def print_result(label: str, value: any, status: str = ""):
    """Print a result line."""
    status_icon = ""
    if status == "PASS":
        status_icon = "✅"
    elif status == "FAIL":
        status_icon = "❌"
    elif status == "WARNING":
        status_icon = "⚠️"
    
    print(f"{status_icon} {label}: {value}")


def test_aws_checker():
    """Test the AWS checker."""
    print_section("AWS Connectivity Checker Test")
    
    # Initialize checker
    checker = AWSChecker(project_root)
    print(f"\n📁 Project root: {project_root}")
    
    # Run quick check first
    print_section("Quick Check (CLI and Credentials Only)")
    quick_result = checker.check(quick_mode=True)
    
    print_result("Status", quick_result.status, quick_result.status)
    print_result("Message", quick_result.message)
    print_result("CLI Installed", quick_result.cli_installed, "PASS" if quick_result.cli_installed else "FAIL")
    if quick_result.cli_version:
        print_result("CLI Version", quick_result.cli_version)
    print_result("Credentials Configured", quick_result.credentials_configured, "PASS" if quick_result.credentials_configured else "WARNING")
    if quick_result.region:
        print_result("Region", quick_result.region)
    print_result("boto3 Available", quick_result.boto3_available, "PASS" if quick_result.boto3_available else "FAIL")
    
    # Show issues from quick check
    if quick_result.issues:
        print_section("Issues Found (Quick Check)")
        for i, issue in enumerate(quick_result.issues, 1):
            print(f"\n{i}. [{issue.severity}] {issue.description}")
            print(f"   Type: {issue.issue_type}")
            print(f"   Details: {issue.details[:200]}...")
            print(f"   Fix: {issue.fix_suggestion[:200]}...")
    
    # If credentials are configured, run full check
    if quick_result.credentials_configured:
        print_section("Full Check (Including Service Connectivity)")
        full_result = checker.check(quick_mode=False)
        
        print_result("Status", full_result.status, full_result.status)
        print_result("Message", full_result.message)
        print_result("Bedrock Client OK", full_result.bedrock_client_ok, "PASS" if full_result.bedrock_client_ok else "FAIL")
        print_result("SSM Access OK", full_result.ssm_access_ok, "PASS" if full_result.ssm_access_ok else "WARNING")
        print_result("S3 Access OK", full_result.s3_access_ok, "PASS" if full_result.s3_access_ok else "WARNING")
        
        # Show issues from full check
        if full_result.issues:
            print_section("Issues Found (Full Check)")
            for i, issue in enumerate(full_result.issues, 1):
                print(f"\n{i}. [{issue.severity}] {issue.description}")
                print(f"   Type: {issue.issue_type}")
                print(f"   Details: {issue.details[:200]}")
                if len(issue.fix_suggestion) > 200:
                    print(f"   Fix: {issue.fix_suggestion[:200]}...")
                else:
                    print(f"   Fix: {issue.fix_suggestion}")
    else:
        print("\n⚠️  Skipping full check because credentials are not configured")
    
    # Show summary
    print_section("Summary")
    summary = checker.get_summary()
    print(f"Total Issues: {summary['total_issues']}")
    print(f"Critical Issues: {summary['critical_issues']}")
    print(f"Warning Issues: {summary['warning_issues']}")
    
    if summary['issues_by_type']:
        print("\nIssues by Type:")
        for issue_type, count in summary['issues_by_type'].items():
            print(f"  - {issue_type}: {count}")
    
    # Show recommendations
    print_section("Recommendations")
    recommendations = checker.get_recommendations()
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    # Final status
    print_section("Test Complete")
    if quick_result.status == "PASS":
        print("✅ AWS connectivity check PASSED")
        return 0
    elif quick_result.status == "WARNING":
        print("⚠️  AWS connectivity check completed with WARNINGS")
        print("   (This is expected if AWS credentials are not configured)")
        return 0
    else:
        print("❌ AWS connectivity check FAILED")
        print("   Please review the issues above and apply suggested fixes")
        return 1


if __name__ == "__main__":
    try:
        exit_code = test_aws_checker()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
