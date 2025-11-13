"""
Adapter for DependencyChecker to work with the migration test framework.

This adapter converts DependencyChecker results to the TestResult format
used by the main test orchestrator.
"""

from pathlib import Path
from datetime import datetime
from typing import List

try:
    from ..models import TestResult, Issue, Fix
    from .dependency_checker import DependencyChecker, DependencyCheckResult, DependencyIssue
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from models import TestResult, Issue, Fix
    from checkers.dependency_checker import DependencyChecker, DependencyCheckResult, DependencyIssue


class DependencyCheckerAdapter:
    """
    Adapter to integrate DependencyChecker with the migration test framework.
    """
    
    def __init__(self, project_root: str):
        """
        Initialize the adapter.
        
        Args:
            project_root: Path to the project root directory
        """
        self.checker = DependencyChecker(project_root)
    
    def check(self, quick_mode: bool = False) -> TestResult:
        """
        Run the dependency check and return a TestResult.
        
        Args:
            quick_mode: If True, skip package installation test
        
        Returns:
            TestResult compatible with the migration test framework
        """
        # Run the dependency check
        result = self.checker.check(quick_mode=quick_mode)
        
        # Convert to TestResult format
        issues = self._convert_issues(self.checker.issues)
        fixes = self._generate_fixes(self.checker.issues)
        
        return TestResult(
            checker_name="Dependency Checker",
            status=result.status,
            message=result.message,
            issues=issues,
            fixes=fixes,
            timestamp=datetime.now()
        )
    
    def _convert_issues(self, dependency_issues: List[DependencyIssue]) -> List[Issue]:
        """
        Convert DependencyIssue objects to Issue objects.
        
        Args:
            dependency_issues: List of DependencyIssue objects
        
        Returns:
            List of Issue objects
        """
        issues = []
        
        for dep_issue in dependency_issues:
            issue = Issue(
                severity=dep_issue.severity,
                category="Dependency",
                file_path=dep_issue.issue_type,
                line_number=None,
                description=dep_issue.description,
                impact=dep_issue.details
            )
            issues.append(issue)
        
        return issues
    
    def _generate_fixes(self, dependency_issues: List[DependencyIssue]) -> List[Fix]:
        """
        Generate Fix objects from DependencyIssue objects.
        
        Args:
            dependency_issues: List of DependencyIssue objects
        
        Returns:
            List of Fix objects
        """
        fixes = []
        
        for idx, dep_issue in enumerate(dependency_issues):
            if dep_issue.fix_suggestion:
                fix = Fix(
                    issue_id=f"dep_{idx}",
                    command=self._extract_command(dep_issue.fix_suggestion),
                    description=dep_issue.fix_suggestion,
                    auto_applicable=self._is_auto_applicable(dep_issue.issue_type),
                    risk_level=self._determine_risk_level(dep_issue.issue_type)
                )
                fixes.append(fix)
        
        return fixes
    
    def _extract_command(self, fix_suggestion: str) -> str:
        """
        Extract executable command from fix suggestion.
        
        Args:
            fix_suggestion: Fix suggestion text
        
        Returns:
            Executable command or empty string
        """
        # Look for common command patterns
        if "pip install" in fix_suggestion:
            # Extract pip install command
            import re
            match = re.search(r'pip install[^:]*', fix_suggestion)
            if match:
                return match.group(0)
        
        if "python" in fix_suggestion.lower():
            # Extract python command
            import re
            match = re.search(r'python[3]?\s+-m\s+\S+', fix_suggestion)
            if match:
                return match.group(0)
        
        return ""
    
    def _is_auto_applicable(self, issue_type: str) -> bool:
        """
        Determine if a fix can be automatically applied.
        
        Args:
            issue_type: Type of dependency issue
        
        Returns:
            True if fix can be auto-applied, False otherwise
        """
        # Most dependency fixes require manual intervention
        auto_applicable_types = []
        
        return issue_type in auto_applicable_types
    
    def _determine_risk_level(self, issue_type: str) -> str:
        """
        Determine risk level for applying a fix.
        
        Args:
            issue_type: Type of dependency issue
        
        Returns:
            Risk level: "LOW", "MEDIUM", or "HIGH"
        """
        high_risk_types = ["PYTHON_VERSION"]
        medium_risk_types = ["PACKAGE_INSTALL", "VENV_CREATION"]
        
        if issue_type in high_risk_types:
            return "HIGH"
        elif issue_type in medium_risk_types:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_summary(self):
        """Get summary from the underlying checker."""
        return self.checker.get_summary()
    
    def get_recommendations(self):
        """Get recommendations from the underlying checker."""
        return self.checker.get_recommendations()
