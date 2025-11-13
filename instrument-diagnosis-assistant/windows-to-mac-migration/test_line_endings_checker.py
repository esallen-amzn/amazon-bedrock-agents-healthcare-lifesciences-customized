"""
Test script for the line endings checker.

This script tests the LineEndingsChecker to ensure it correctly identifies
files with Windows line endings (CRLF) and generates appropriate fix commands.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from checkers.line_endings_checker import LineEndingsChecker


def main():
    """Run the line endings checker test."""
    print("=" * 70)
    print("Line Endings Checker Test")
    print("=" * 70)
    print()
    
    # Get the project root (parent of windows-to-mac-migration)
    project_root = Path(__file__).parent.parent
    
    print(f"Project root: {project_root}")
    print()
    
    # Create and run the checker
    print("Running line endings check...")
    print("-" * 70)
    checker = LineEndingsChecker(str(project_root))
    result = checker.check()
    
    # Display results
    print()
    print(f"Status: {result.status}")
    print(f"Files checked: {result.files_checked}")
    print(f"Message: {result.message}")
    print()
    
    if result.issues:
        print(f"Found {len(result.issues)} files with line ending issues:")
        print()
        
        # Group by severity
        critical = [i for i in result.issues if i.severity == "CRITICAL"]
        warnings = [i for i in result.issues if i.severity == "WARNING"]
        
        if critical:
            print(f"CRITICAL Issues ({len(critical)}):")
            print("-" * 70)
            for issue in critical:
                print(f"  File: {issue.file_path}")
                print(f"  Type: {issue.line_ending_type}")
                print(f"  Lines: {issue.total_lines} (CRLF count: {issue.crlf_count})")
                print(f"  Fix: {issue.fix_command}")
                print()
        
        if warnings:
            print(f"WARNING Issues ({len(warnings)}):")
            print("-" * 70)
            for issue in warnings:
                print(f"  File: {issue.file_path}")
                print(f"  Type: {issue.line_ending_type}")
                print(f"  Lines: {issue.total_lines} (CRLF count: {issue.crlf_count})")
                print(f"  Fix: {issue.fix_command}")
                print()
    else:
        print("✅ No line ending issues found!")
        print()
    
    # Display summary
    print("Summary:")
    print("-" * 70)
    summary = checker.get_summary()
    print(f"Total issues: {summary['total_issues']}")
    print(f"Critical issues: {summary['critical_issues']}")
    print(f"Warning issues: {summary['warning_issues']}")
    print()
    
    # Generate fix script if there are issues
    if result.issues:
        print("Generated Fix Script:")
        print("-" * 70)
        fix_script = checker.get_fix_script()
        print(fix_script)
        print()
        
        # Optionally save the fix script
        fix_script_path = Path(__file__).parent / "fix_line_endings.sh"
        with open(fix_script_path, 'w') as f:
            f.write(fix_script)
        print(f"Fix script saved to: {fix_script_path}")
        print()
    
    print("=" * 70)
    print("Test completed!")
    print("=" * 70)
    
    # Return exit code based on status
    if result.status == "FAIL":
        return 1
    elif result.status == "WARNING":
        return 0  # Warnings don't fail the test
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
