#!/usr/bin/env python3
"""Main test orchestrator for Windows-to-Mac migration testing."""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List

from models import TestReport, TestResult, ReportSummary, ActionItem, Issue
from checkers import BaseChecker


class MigrationTester:
    """Orchestrates all migration tests and generates reports."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.checkers: List[BaseChecker] = []
        
    def register_checker(self, checker: BaseChecker):
        """Register a checker to be run during testing."""
        self.checkers.append(checker)
    
    def discover_files(self) -> dict:
        """Discover relevant files in the project."""
        files = {
            'shell_scripts': [],
            'python_files': [],
            'config_files': []
        }
        
        # Find shell scripts
        for pattern in ['**/*.sh']:
            files['shell_scripts'].extend(self.project_root.glob(pattern))
        
        # Find Python files
        for pattern in ['**/*.py']:
            files['python_files'].extend(self.project_root.glob(pattern))
        
        # Find config files
        for pattern in ['**/*.yaml', '**/*.yml', '**/*.json', '**/*.txt']:
            files['config_files'].extend(self.project_root.glob(pattern))
        
        # Filter out common directories to skip
        skip_dirs = {'.git', '.venv', '__pycache__', 'node_modules', '.kiro'}
        
        for key in files:
            files[key] = [
                f for f in files[key]
                if not any(skip_dir in f.parts for skip_dir in skip_dirs)
            ]
        
        return files
    
    def run_all_checks(self) -> TestReport:
        """Run all registered checkers and return a complete report."""
        print("🔍 Windows-to-Mac Migration Test")
        print("=" * 50)
        print()
        
        results = []
        
        for i, checker in enumerate(self.checkers, 1):
            print(f"[{i}/{len(self.checkers)}] Running {checker.name}...", end=" ", flush=True)
            
            try:
                result = checker.check()
                results.append(result)
                
                # Print status
                if result.status == "PASS":
                    print("✅ PASS")
                elif result.status == "FAIL":
                    print(f"❌ FAIL ({len(result.issues)} issues)")
                elif result.status == "WARNING":
                    print(f"⚠️  WARNING ({len(result.issues)} issues)")
                elif result.status == "SKIP":
                    print("⏭️  SKIP")
                    
            except Exception as e:
                print(f"❌ ERROR: {str(e)}")
                results.append(TestResult(
                    checker_name=checker.name,
                    status="SKIP",
                    message=f"Checker failed with error: {str(e)}",
                    issues=[],
                    fixes=[]
                ))
        
        print()
        
        # Generate summary
        summary = self._generate_summary(results)
        
        # Generate action items
        action_items = self._generate_action_items(results)
        
        # Create report
        report = TestReport(
            project_name=self.project_root.name,
            test_date=datetime.now(),
            results=results,
            summary=summary,
            action_items=action_items
        )
        
        return report
    
    def _generate_summary(self, results: List[TestResult]) -> ReportSummary:
        """Generate summary statistics from test results."""
        passed = sum(1 for r in results if r.status == "PASS")
        failed = sum(1 for r in results if r.status == "FAIL")
        warnings = sum(1 for r in results if r.status == "WARNING")
        skipped = sum(1 for r in results if r.status == "SKIP")
        
        # Count issues by severity
        all_issues = [issue for result in results for issue in result.issues]
        critical = sum(1 for i in all_issues if i.severity == "CRITICAL")
        warning_issues = sum(1 for i in all_issues if i.severity == "WARNING")
        info = sum(1 for i in all_issues if i.severity == "INFO")
        
        return ReportSummary(
            total_checks=len(results),
            passed=passed,
            failed=failed,
            warnings=warnings,
            skipped=skipped,
            critical_issues=critical,
            warning_issues=warning_issues,
            info_issues=info
        )
    
    def _generate_action_items(self, results: List[TestResult]) -> List[ActionItem]:
        """Generate prioritized action items from test results."""
        action_items = []
        priority = 1
        
        # Group fixes by category
        fix_groups = {}
        for result in results:
            for fix in result.fixes:
                category = result.checker_name
                if category not in fix_groups:
                    fix_groups[category] = []
                fix_groups[category].append(fix)
        
        # Create action items for each category
        for category, fixes in fix_groups.items():
            if not fixes:
                continue
            
            # Determine priority based on risk level
            has_critical = any(f.risk_level == "HIGH" for f in fixes)
            
            commands = [f.command for f in fixes if f.auto_applicable]
            
            if commands:
                action_items.append(ActionItem(
                    priority=priority if has_critical else priority + 1,
                    description=f"Fix {len(fixes)} issue(s) in {category}",
                    commands=commands,
                    category=category
                ))
                priority += 1
        
        # Sort by priority
        action_items.sort(key=lambda x: x.priority)
        
        return action_items
    
    def generate_report(self, report: TestReport, output_format: str = "console") -> str:
        """Generate a formatted report."""
        if output_format == "console":
            return self._generate_console_report(report)
        elif output_format == "markdown":
            return self._generate_markdown_report(report)
        else:
            raise ValueError(f"Unknown output format: {output_format}")
    
    def _generate_console_report(self, report: TestReport) -> str:
        """Generate console-formatted report."""
        lines = []
        
        lines.append("\nSummary:")
        lines.append("-" * 50)
        lines.append(f"Total Checks: {report.summary.total_checks}")
        lines.append(f"Passed: {report.summary.passed}")
        lines.append(f"Failed: {report.summary.failed}")
        lines.append(f"Warnings: {report.summary.warnings}")
        lines.append(f"Skipped: {report.summary.skipped}")
        lines.append("")
        lines.append(f"Critical Issues: {report.summary.critical_issues}")
        lines.append(f"Warnings: {report.summary.warning_issues}")
        lines.append(f"Info: {report.summary.info_issues}")
        
        if report.action_items:
            lines.append("\nNext Steps:")
            lines.append("-" * 50)
            for item in report.action_items:
                lines.append(f"{item.priority}. {item.description}")
                for cmd in item.commands[:3]:  # Show first 3 commands
                    lines.append(f"   {cmd}")
                if len(item.commands) > 3:
                    lines.append(f"   ... and {len(item.commands) - 3} more")
        
        return "\n".join(lines)
    
    def _generate_markdown_report(self, report: TestReport) -> str:
        """Generate markdown-formatted report."""
        lines = []
        
        lines.append(f"# Migration Test Report: {report.project_name}")
        lines.append(f"\n**Date**: {report.test_date.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("\n## Summary\n")
        lines.append(f"- **Total Checks**: {report.summary.total_checks}")
        lines.append(f"- **Passed**: {report.summary.passed}")
        lines.append(f"- **Failed**: {report.summary.failed}")
        lines.append(f"- **Warnings**: {report.summary.warnings}")
        lines.append(f"- **Skipped**: {report.summary.skipped}")
        lines.append(f"\n### Issues by Severity\n")
        lines.append(f"- **Critical**: {report.summary.critical_issues}")
        lines.append(f"- **Warning**: {report.summary.warning_issues}")
        lines.append(f"- **Info**: {report.summary.info_issues}")
        
        lines.append("\n## Test Results\n")
        for result in report.results:
            status_icon = {
                "PASS": "✅",
                "FAIL": "❌",
                "WARNING": "⚠️",
                "SKIP": "⏭️"
            }.get(result.status, "❓")
            
            lines.append(f"### {status_icon} {result.checker_name}")
            lines.append(f"\n**Status**: {result.status}")
            lines.append(f"**Message**: {result.message}")
            
            if result.issues:
                lines.append(f"\n**Issues Found**: {len(result.issues)}")
                for issue in result.issues[:5]:  # Show first 5 issues
                    lines.append(f"\n- **{issue.severity}**: {issue.description}")
                    lines.append(f"  - File: `{issue.file_path}`")
                    if issue.line_number:
                        lines.append(f"  - Line: {issue.line_number}")
                    lines.append(f"  - Impact: {issue.impact}")
                
                if len(result.issues) > 5:
                    lines.append(f"\n*... and {len(result.issues) - 5} more issues*")
        
        if report.action_items:
            lines.append("\n## Action Items\n")
            for item in report.action_items:
                lines.append(f"\n### {item.priority}. {item.description}")
                lines.append(f"\n**Category**: {item.category}")
                if item.commands:
                    lines.append("\n**Commands**:")
                    lines.append("```bash")
                    for cmd in item.commands:
                        lines.append(cmd)
                    lines.append("```")
        
        return "\n".join(lines)
    
    def apply_fixes(self, auto_fix: bool = False) -> dict:
        """Apply automated fixes for issues."""
        if not auto_fix:
            print("Auto-fix not enabled. Use --auto-fix to apply fixes automatically.")
            return {"applied": 0, "skipped": 0}
        
        print("\n🔧 Applying automated fixes...")
        applied = 0
        skipped = 0
        
        # This will be implemented when we have actual fixes to apply
        # For now, just return counts
        
        return {"applied": applied, "skipped": skipped}


def main():
    """Main entry point for the migration tester."""
    parser = argparse.ArgumentParser(
        description="Test Windows-to-Mac migration compatibility"
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Root directory of the project to test (default: current directory)"
    )
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Automatically apply safe fixes"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run only quick diagnostic checks"
    )
    parser.add_argument(
        "--output",
        choices=["console", "markdown"],
        default="console",
        help="Output format for the report"
    )
    parser.add_argument(
        "--output-file",
        help="Write report to file instead of stdout"
    )
    
    args = parser.parse_args()
    
    # Create tester
    tester = MigrationTester(args.project_root)
    
    # Register checkers (will be added in subsequent tasks)
    # For now, the tester is ready but has no checkers
    
    if not tester.checkers:
        print("⚠️  No checkers registered yet.")
        print("Checkers will be added in subsequent implementation tasks.")
        return 0
    
    # Run tests
    report = tester.run_all_checks()
    
    # Generate report
    report_text = tester.generate_report(report, args.output)
    
    if args.output_file:
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_text)
        print(f"\n📄 Report written to: {output_path}")
    else:
        print(report_text)
    
    # Apply fixes if requested
    if args.auto_fix:
        fix_results = tester.apply_fixes(auto_fix=True)
        print(f"\n✅ Applied {fix_results['applied']} fixes")
        print(f"⏭️  Skipped {fix_results['skipped']} fixes")
    
    # Return exit code based on results
    if report.summary.critical_issues > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
