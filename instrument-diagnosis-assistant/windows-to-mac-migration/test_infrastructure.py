#!/usr/bin/env python3
"""Test script to verify the infrastructure and data models."""

import sys
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from models import Issue, Fix, TestResult, ReportSummary, ActionItem, TestReport
from test_migration import MigrationTester
from checkers import BaseChecker


class DummyChecker(BaseChecker):
    """A dummy checker for testing purposes."""
    
    @property
    def name(self) -> str:
        return "Dummy Checker"
    
    def check(self) -> TestResult:
        """Run a dummy check."""
        return TestResult(
            checker_name=self.name,
            status="PASS",
            message="Dummy check completed successfully",
            issues=[],
            fixes=[]
        )


def test_data_models():
    """Test that all data models can be instantiated."""
    print("Testing data models...")
    
    # Test Issue
    issue = Issue(
        severity="CRITICAL",
        category="permissions",
        file_path="/path/to/file.sh",
        line_number=10,
        description="Missing execute permission",
        impact="Script cannot be executed"
    )
    assert issue.severity == "CRITICAL"
    print("✅ Issue model works")
    
    # Test Fix
    fix = Fix(
        issue_id="issue-1",
        command="chmod +x /path/to/file.sh",
        description="Add execute permission",
        auto_applicable=True,
        risk_level="LOW"
    )
    assert fix.auto_applicable is True
    print("✅ Fix model works")
    
    # Test TestResult
    result = TestResult(
        checker_name="Test Checker",
        status="PASS",
        message="All checks passed",
        issues=[issue],
        fixes=[fix]
    )
    assert result.status == "PASS"
    assert len(result.issues) == 1
    print("✅ TestResult model works")
    
    # Test ReportSummary
    summary = ReportSummary(
        total_checks=5,
        passed=3,
        failed=1,
        warnings=1,
        skipped=0,
        critical_issues=2,
        warning_issues=1,
        info_issues=0
    )
    assert summary.total_checks == 5
    print("✅ ReportSummary model works")
    
    # Test ActionItem
    action = ActionItem(
        priority=1,
        description="Fix permissions",
        commands=["chmod +x script.sh"],
        category="permissions"
    )
    assert action.priority == 1
    print("✅ ActionItem model works")
    
    # Test TestReport
    report = TestReport(
        project_name="test-project",
        test_date=datetime.now(),
        results=[result],
        summary=summary,
        action_items=[action]
    )
    assert report.project_name == "test-project"
    print("✅ TestReport model works")
    
    print("\n✅ All data models working correctly!\n")


def test_orchestrator():
    """Test the MigrationTester orchestrator."""
    print("Testing orchestrator...")
    
    # Create tester
    tester = MigrationTester(".")
    print("✅ MigrationTester instantiated")
    
    # Test file discovery
    files = tester.discover_files()
    assert 'shell_scripts' in files
    assert 'python_files' in files
    assert 'config_files' in files
    print(f"✅ File discovery works (found {len(files['shell_scripts'])} shell scripts)")
    
    # Register a dummy checker
    dummy_checker = DummyChecker(".")
    tester.register_checker(dummy_checker)
    assert len(tester.checkers) == 1
    print("✅ Checker registration works")
    
    # Run checks
    report = tester.run_all_checks()
    assert report is not None
    assert len(report.results) == 1
    print("✅ Check execution works")
    
    # Test console report generation
    console_report = tester.generate_report(report, "console")
    assert "Summary:" in console_report
    print("✅ Console report generation works")
    
    # Test markdown report generation
    markdown_report = tester.generate_report(report, "markdown")
    assert "# Migration Test Report" in markdown_report
    print("✅ Markdown report generation works")
    
    print("\n✅ All orchestrator functions working correctly!\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Windows-to-Mac Migration Infrastructure")
    print("=" * 60)
    print()
    
    try:
        test_data_models()
        test_orchestrator()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
