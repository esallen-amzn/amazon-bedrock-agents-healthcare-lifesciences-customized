"""
Tests for the path checker module.

This module tests the PathChecker's ability to detect Windows-specific
path patterns in Python code.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from checkers.path_checker import PathChecker
from checkers.path_checker_adapter import PathCheckerAdapter


def test_path_checker():
    """Test the path checker on the project."""
    print("=" * 70)
    print("Testing Path Checker for Windows-specific patterns")
    print("=" * 70)
    print()
    
    # Get project root (parent of windows-to-mac-migration directory)
    project_root = Path(__file__).parent.parent
    
    print(f"Project root: {project_root}")
    print()
    
    # Create and run the checker
    checker = PathChecker(str(project_root))
    result = checker.check()
    
    # Display results
    print(f"Status: {result.status}")
    print(f"Files checked: {result.files_checked}")
    print(f"Message: {result.message}")
    print()
    
    if result.issues:
        print(f"Found {len(result.issues)} path issues:")
        print("-" * 70)
        
        # Group issues by type
        issues_by_type = {}
        for issue in result.issues:
            if issue.issue_type not in issues_by_type:
                issues_by_type[issue.issue_type] = []
            issues_by_type[issue.issue_type].append(issue)
        
        # Display issues by type
        for issue_type, issues in sorted(issues_by_type.items()):
            print(f"\n{issue_type} ({len(issues)} issues):")
            print("-" * 70)
            
            for issue in issues[:5]:  # Show first 5 of each type
                print(f"  File: {issue.file_path}:{issue.line_number}")
                print(f"  Pattern: {issue.pattern_found}")
                print(f"  Line: {issue.line_content[:80]}...")
                print(f"  Severity: {issue.severity}")
                print(f"  Suggestion: {issue.suggestion}")
                print()
            
            if len(issues) > 5:
                print(f"  ... and {len(issues) - 5} more {issue_type} issues")
                print()
    else:
        print("✅ No Windows-specific path patterns found!")
    
    # Display summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    summary = checker.get_summary()
    print(f"Total issues: {summary['total_issues']}")
    print(f"Critical issues: {summary['critical_issues']}")
    print(f"Warning issues: {summary['warning_issues']}")
    print(f"Info issues: {summary['info_issues']}")
    print()
    
    if summary['issues_by_type']:
        print("Issues by type:")
        for issue_type, count in sorted(summary['issues_by_type'].items()):
            print(f"  {issue_type}: {count}")
        print()
    
    if summary['files_with_issues']:
        print(f"Files with issues: {len(summary['files_with_issues'])}")
        for file_path in sorted(summary['files_with_issues'])[:10]:
            issue_count = summary['issues_by_file'][file_path]
            print(f"  {file_path}: {issue_count} issue(s)")
        if len(summary['files_with_issues']) > 10:
            print(f"  ... and {len(summary['files_with_issues']) - 10} more files")
    
    # Display recommendations
    print("\n" + "=" * 70)
    print("Recommendations for Cross-Platform Path Handling")
    print("=" * 70)
    recommendations = checker.get_recommendations()
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    print("\n" + "=" * 70)
    print("Path Checker Test Complete")
    print("=" * 70)
    
    return result


def test_path_checker_adapter():
    """Test the path checker adapter integration."""
    print("\n\n")
    print("=" * 70)
    print("Testing Path Checker Adapter")
    print("=" * 70)
    print()
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Create and run the adapter
    adapter = PathCheckerAdapter(str(project_root))
    test_result = adapter.run()
    
    # Display TestResult
    print(f"Checker: {test_result.checker_name}")
    print(f"Status: {test_result.status}")
    print(f"Message: {test_result.message}")
    print(f"Timestamp: {test_result.timestamp}")
    print()
    
    print(f"Issues found: {len(test_result.issues)}")
    if test_result.issues:
        print("\nSample issues:")
        for issue in test_result.issues[:3]:
            print(f"  - [{issue.severity}] {issue.file_path}:{issue.line_number}")
            print(f"    {issue.description}")
            print(f"    Impact: {issue.impact}")
            print()
    
    print(f"Fixes available: {len(test_result.fixes)}")
    if test_result.fixes:
        print("\nRecommended fixes:")
        for fix in test_result.fixes:
            print(f"  - {fix.description}")
            print(f"    Risk: {fix.risk_level}, Auto-applicable: {fix.auto_applicable}")
            if fix.command and not fix.command.startswith('#'):
                print(f"    Command: {fix.command}")
            print()
    
    print("=" * 70)
    print("Path Checker Adapter Test Complete")
    print("=" * 70)
    
    return test_result


if __name__ == "__main__":
    # Run both tests
    result = test_path_checker()
    adapter_result = test_path_checker_adapter()
    
    # Exit with appropriate code
    if result.status == "FAIL":
        sys.exit(1)
    else:
        sys.exit(0)
