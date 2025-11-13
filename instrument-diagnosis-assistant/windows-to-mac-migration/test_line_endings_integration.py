#!/usr/bin/env python3
"""
Integration test for the line endings checker with the test infrastructure.
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from test_migration import MigrationTester
from checkers import LineEndingsChecker


def main():
    """Run the line endings checker integration test."""
    print("=" * 70)
    print("Line Endings Checker Integration Test")
    print("=" * 70)
    print()
    
    # Get the project root (parent of windows-to-mac-migration)
    project_root = Path(__file__).parent.parent
    
    print(f"Project root: {project_root}")
    print()
    
    # Create tester and register the line endings checker
    tester = MigrationTester(str(project_root))
    checker = LineEndingsChecker(str(project_root))
    tester.register_checker(checker)
    
    print(f"Registered checker: {checker.name}")
    print()
    
    # Run the test
    print("Running migration test with line endings checker...")
    print("-" * 70)
    report = tester.run_all_checks()
    
    # Display console report
    console_report = tester.generate_report(report, "console")
    print(console_report)
    print()
    
    # Display detailed results
    if report.results:
        result = report.results[0]
        print("\nDetailed Results:")
        print("-" * 70)
        print(f"Checker: {result.checker_name}")
        print(f"Status: {result.status}")
        print(f"Message: {result.message}")
        print(f"Issues found: {len(result.issues)}")
        print(f"Fixes available: {len(result.fixes)}")
        
        if result.issues:
            print("\nIssues by severity:")
            critical = [i for i in result.issues if i.severity == "CRITICAL"]
            warnings = [i for i in result.issues if i.severity == "WARNING"]
            
            if critical:
                print(f"\n  CRITICAL ({len(critical)}):")
                for issue in critical[:5]:  # Show first 5
                    print(f"    - {issue.file_path}")
                    print(f"      {issue.description}")
                if len(critical) > 5:
                    print(f"    ... and {len(critical) - 5} more")
            
            if warnings:
                print(f"\n  WARNING ({len(warnings)}):")
                for issue in warnings[:5]:  # Show first 5
                    print(f"    - {issue.file_path}")
                    print(f"      {issue.description}")
                if len(warnings) > 5:
                    print(f"    ... and {len(warnings) - 5} more")
        
        if result.fixes:
            print("\nAvailable fixes:")
            print("-" * 70)
            for fix in result.fixes[:3]:  # Show first 3
                print(f"  {fix.command}")
            if len(result.fixes) > 3:
                print(f"  ... and {len(result.fixes) - 3} more")
    
    # Generate markdown report
    print("\n" + "=" * 70)
    print("Generating markdown report...")
    markdown_report = tester.generate_report(report, "markdown")
    
    # Save markdown report
    report_path = Path(__file__).parent / "reports"
    report_path.mkdir(exist_ok=True)
    report_file = report_path / "line_endings_report.md"
    report_file.write_text(markdown_report)
    print(f"Markdown report saved to: {report_file}")
    
    print("\n" + "=" * 70)
    print("Integration test completed!")
    print("=" * 70)
    
    # Return exit code based on status
    if report.summary.critical_issues > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
