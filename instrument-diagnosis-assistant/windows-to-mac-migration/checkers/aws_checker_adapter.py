"""
Adapter for AWS checker to integrate with the main test infrastructure.

This adapter converts AWSCheckResult to TestResult format for use
with the main test orchestrator.
"""

import sys
from pathlib import Path

# Add parent directory to path for models import
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from models import TestResult, Issue, Fix
from .aws_checker import AWSChecker, AWSCheckResult


class AWSCheckerAdapter:
    """
    Adapter for AWS checker that converts results to TestResult format.
    """
    
    def __init__(self, project_root: str):
        """
        Initialize the AWS checker adapter.
        
        Args:
            project_root: Path to the project root directory
        """
        self.checker = AWSChecker(project_root)
        self.project_root = project_root
    
    @property
    def name(self) -> str:
        """Return the name of this checker."""
        return "AWS Connectivity"
    
    def check(self, quick_mode: bool = False) -> TestResult:
        """
        Run the AWS connectivity check and return TestResult.
        
        Args:
            quick_mode: If True, skip service connectivity tests
        
        Returns:
            TestResult compatible with main test orchestrator
        """
        # Run AWS check
        aws_result = self.checker.check(quick_mode=quick_mode)
        
        # Convert to TestResult
        return self._convert_to_test_result(aws_result)
    
    def _convert_to_test_result(self, aws_result: AWSCheckResult) -> TestResult:
        """
        Convert AWSCheckResult to TestResult format.
        
        Args:
            aws_result: Result from AWS checker
        
        Returns:
            TestResult compatible with main test orchestrator
        """
        # Convert AWS issues to standard Issue format
        issues = []
        fixes = []
        
        for aws_issue in aws_result.issues:
            # Map severity
            if aws_issue.severity == "CRITICAL":
                severity = "CRITICAL"
            elif aws_issue.severity == "WARNING":
                severity = "WARNING"
            else:
                severity = "INFO"
            
            # Create Issue
            issue = Issue(
                severity=severity,
                category="AWS Configuration",
                file_path="N/A",
                line_number=None,
                description=aws_issue.description,
                impact=aws_issue.details
            )
            issues.append(issue)
            
            # Create Fix if suggestion provided
            if aws_issue.fix_suggestion:
                # Extract first line as command, full text as description
                lines = aws_issue.fix_suggestion.split('\n')
                command = lines[0] if lines else aws_issue.fix_suggestion
                
                fix = Fix(
                    issue_id=f"aws_{aws_issue.issue_type.lower()}",
                    command=command,
                    description=aws_issue.fix_suggestion,
                    auto_applicable=False,  # AWS fixes require manual intervention
                    risk_level="LOW"
                )
                fixes.append(fix)
        
        # Build message with details
        details = []
        if aws_result.cli_installed:
            details.append(f"CLI: {aws_result.cli_version}")
        if aws_result.credentials_configured:
            details.append(f"Region: {aws_result.region}")
        if aws_result.boto3_available:
            details.append("boto3: ✓")
        
        message = aws_result.message
        if details:
            message += f" ({', '.join(details)})"
        
        # Create TestResult
        return TestResult(
            checker_name=self.name,
            status=aws_result.status,
            message=message,
            issues=issues,
            fixes=fixes
        )
