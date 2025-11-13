"""
Adapter for LineEndingsChecker to work with the BaseChecker interface.
"""

from typing import TYPE_CHECKING
from . import BaseChecker
from .line_endings_checker import LineEndingsChecker as LineEndingsCheckerImpl
from ..models import TestResult, Issue, Fix

if TYPE_CHECKING:
    from ..models import TestResult


class LineEndingsChecker(BaseChecker):
    """
    Adapter for LineEndingsChecker that implements BaseChecker interface.
    
    Requirements addressed:
    - 1.2: Detect any files with Windows line endings (CRLF)
    """
    
    @property
    def name(self) -> str:
        return "Line Endings Checker"
    
    def check(self) -> TestResult:
        """
        Run the line endings check and convert results to TestResult format.
        
        Returns:
            TestResult with status and any issues found
        """
        # Create and run the actual checker
        checker = LineEndingsCheckerImpl(self.project_root)
        result = checker.check()
        
        # Convert issues to the standard Issue format
        issues = []
        fixes = []
        
        for idx, line_issue in enumerate(result.issues):
            # Create Issue object
            issue = Issue(
                severity=line_issue.severity,
                category="line_endings",
                file_path=line_issue.file_path,
                line_number=None,  # Line endings affect the whole file
                description=f"File has {line_issue.line_ending_type} line endings ({line_issue.crlf_count} CRLF sequences)",
                impact="Shell scripts with CRLF may fail to execute on macOS"
            )
            issues.append(issue)
            
            # Create Fix object
            fix = Fix(
                issue_id=f"line_endings_{idx}",
                command=line_issue.fix_command,
                description=f"Convert {line_issue.file_path} to Unix line endings (LF)",
                auto_applicable=True,
                risk_level="LOW"  # Converting line endings is generally safe
            )
            fixes.append(fix)
        
        # Return TestResult
        return TestResult(
            checker_name=self.name,
            status=result.status,
            message=result.message,
            issues=issues,
            fixes=fixes
        )
