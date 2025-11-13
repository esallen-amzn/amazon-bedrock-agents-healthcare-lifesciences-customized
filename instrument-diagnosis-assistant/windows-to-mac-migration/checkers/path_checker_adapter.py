"""
Adapter for PathChecker to integrate with the test infrastructure.

This module adapts the PathChecker to work with the TestResult model
used by the migration test orchestrator.
"""

from datetime import datetime
from typing import List
from pathlib import Path

from .path_checker import PathChecker, PathCheckResult, PathIssue
from ..models import TestResult, Issue, Fix


class PathCheckerAdapter:
    """Adapter to integrate PathChecker with the test infrastructure."""
    
    def __init__(self, project_root: str):
        """
        Initialize the adapter.
        
        Args:
            project_root: Path to the project root directory
        """
        self.checker = PathChecker(project_root)
        self.project_root = Path(project_root)
    
    def run(self) -> TestResult:
        """
        Run the path checker and return a TestResult.
        
        Returns:
            TestResult object with path check results
        """
        # Run the checker
        result = self.checker.check()
        
        # Convert to TestResult format
        issues = self._convert_issues(result.issues)
        fixes = self._generate_fixes(result.issues)
        
        return TestResult(
            checker_name="Path Checker",
            status=result.status,
            message=result.message,
            issues=issues,
            fixes=fixes,
            timestamp=datetime.now()
        )
    
    def _convert_issues(self, path_issues: List[PathIssue]) -> List[Issue]:
        """
        Convert PathIssue objects to Issue objects.
        
        Args:
            path_issues: List of PathIssue objects
            
        Returns:
            List of Issue objects
        """
        issues = []
        
        for path_issue in path_issues:
            issue = Issue(
                severity=path_issue.severity,
                category="Path Compatibility",
                file_path=path_issue.file_path,
                line_number=path_issue.line_number,
                description=f"{path_issue.issue_type}: {path_issue.pattern_found}",
                impact=path_issue.suggestion
            )
            issues.append(issue)
        
        return issues
    
    def _generate_fixes(self, path_issues: List[PathIssue]) -> List[Fix]:
        """
        Generate Fix objects for path issues.
        
        Args:
            path_issues: List of PathIssue objects
            
        Returns:
            List of Fix objects
        """
        fixes = []
        
        # Group issues by file for batch fixes
        files_with_issues = set(issue.file_path for issue in path_issues)
        
        if files_with_issues:
            # General recommendation fix
            fix = Fix(
                issue_id="path_patterns",
                command="# Manual review required - see recommendations below",
                description="Review and refactor Windows-specific path patterns",
                auto_applicable=False,
                risk_level="MEDIUM"
            )
            fixes.append(fix)
        
        # Add specific recommendations
        recommendations = self.checker.get_recommendations()
        for i, recommendation in enumerate(recommendations[:3]):  # Top 3 recommendations
            fix = Fix(
                issue_id=f"path_recommendation_{i}",
                command=f"# {recommendation}",
                description=recommendation,
                auto_applicable=False,
                risk_level="LOW"
            )
            fixes.append(fix)
        
        return fixes
    
    def get_summary(self):
        """Get summary from the checker."""
        return self.checker.get_summary()
    
    def get_recommendations(self):
        """Get recommendations from the checker."""
        return self.checker.get_recommendations()
