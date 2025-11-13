"""Data models for Windows-to-Mac migration testing."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal, Optional


@dataclass
class Issue:
    """Represents a single migration issue found during testing."""
    severity: Literal["CRITICAL", "WARNING", "INFO"]
    category: str
    file_path: str
    line_number: Optional[int]
    description: str
    impact: str


@dataclass
class Fix:
    """Represents a fix for a migration issue."""
    issue_id: str
    command: str
    description: str
    auto_applicable: bool
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]


@dataclass
class TestResult:
    """Result from running a single checker."""
    checker_name: str
    status: Literal["PASS", "FAIL", "WARNING", "SKIP"]
    message: str
    issues: List[Issue] = field(default_factory=list)
    fixes: List[Fix] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ReportSummary:
    """Summary statistics for the test report."""
    total_checks: int
    passed: int
    failed: int
    warnings: int
    skipped: int
    critical_issues: int
    warning_issues: int
    info_issues: int


@dataclass
class ActionItem:
    """Prioritized action item for fixing issues."""
    priority: int
    description: str
    commands: List[str]
    category: str


@dataclass
class TestReport:
    """Complete test report for migration testing."""
    project_name: str
    test_date: datetime
    results: List[TestResult]
    summary: ReportSummary
    action_items: List[ActionItem]
