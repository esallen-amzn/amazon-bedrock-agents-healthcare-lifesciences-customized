"""
Integration test for path checker with the test infrastructure.

This test demonstrates the path checker integrated with the migration tester.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from test_migration import MigrationTester
from checkers.path_checker_adapter import PathCheckerAdapter


def main():
    """Run integration test for path checker."""
    print("=" * 70)
    print("Path Checker Integration Test")
    print("=" * 70)
    print()
    
    # Get project root (parent of windows-to-mac-migration directory)
    project_root = Path(__file__).parent.parent
    
    print(f"Project root: {project_root}")
    print()
    
    # Create migration tester
    tester = MigrationTester(str(project_root))
    
    # Register the path checker
    path_checker = PathCheckerAdapter(str(project_root))
    tester.register_checker(path_checker)
    
    # Run all checks
    report = tester.run_all_checks()
    
    # Generate and display console report
    report_text = tester.generate_report(report, output_format="console")
    print(report_text)
    
    # Display detailed results for path checker
    print("\n" + "=" * 70)
    print("Detailed Path Checker Results")
    print("=" * 70)
    
    for result in report.results:
        if result.checker_name == "Path Checker":
            print(f"\nStatus: {result.status}")
            print(f"Message: {result.message}")
            print(f"\nIssues found: {len(result.issues)}")
            
            if result.issues:
                # Group by severity
                critical = [i for i in result.issues if i.severity == "CRITICAL"]
                warnings = [i for i in result.issues if i.severity == "WARNING"]
                info = [i for i in result.issues if i.severity == "INFO"]
                
                if critical:
                    print(f"\nCritical issues ({len(critical)}):")
                    for issue in critical[:5]:
                        print(f"  - {issue.file_path}:{issue.line_number}")
                        print(f"    {issue.description}")
                        print(f"    {issue.impact}")
                
                if warnings:
                    print(f"\nWarning issues ({len(warnings)}):")
                    for issue in warnings[:5]:
                        print(f"  - {issue.file_path}:{issue.line_number}")
                        print(f"    {issue.description}")
                
                if info:
                    print(f"\nInfo issues ({len(info)}):")
                    for issue in info[:3]:
                        print(f"  - {issue.file_path}:{issue.line_number}")
                        print(f"    {issue.description}")
            
            print(f"\nFixes available: {len(result.fixes)}")
            if result.fixes:
                print("\nRecommended actions:")
                for fix in result.fixes:
                    print(f"  - {fix.description}")
    
    # Also generate markdown report
    print("\n" + "=" * 70)
    print("Generating Markdown Report")
    print("=" * 70)
    
    markdown_report = tester.generate_report(report, output_format="markdown")
    
    # Save to file
    report_file = Path(__file__).parent / "reports" / "path_check_report.md"
    report_file.parent.mkdir(exist_ok=True)
    report_file.write_text(markdown_report)
    
    print(f"\n✅ Markdown report saved to: {report_file}")
    
    print("\n" + "=" * 70)
    print("Integration Test Complete")
    print("=" * 70)
    
    # Return exit code based on critical issues
    if report.summary.critical_issues > 0:
        print(f"\n⚠️  Found {report.summary.critical_issues} critical issues")
        return 1
    else:
        print("\n✅ No critical issues found")
        return 0


if __name__ == "__main__":
    sys.exit(main())
