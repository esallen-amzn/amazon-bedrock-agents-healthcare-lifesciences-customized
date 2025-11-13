"""
Tests for the dependency checker module.

This module tests the DependencyChecker class to ensure it correctly:
- Checks Python version
- Tests virtual environment creation
- Validates package installation
- Verifies critical package imports
"""

import sys
import pytest
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from windows_to_mac_migration.checkers.dependency_checker import (
    DependencyChecker,
    DependencyCheckResult,
    DependencyIssue
)


def test_dependency_checker_initialization():
    """Test that DependencyChecker initializes correctly."""
    checker = DependencyChecker(str(project_root))
    
    assert checker.project_root == project_root
    assert checker.dev_requirements_path == project_root / "dev-requirements.txt"
    assert len(checker.issues) == 0


def test_python_version_check():
    """Test Python version checking."""
    checker = DependencyChecker(str(project_root))
    
    version_string, is_ok = checker._check_python_version()
    
    # Should return current Python version
    assert version_string is not None
    assert "." in version_string
    
    # Current Python should meet minimum requirements (3.9+)
    version_parts = version_string.split(".")
    major = int(version_parts[0])
    minor = int(version_parts[1])
    
    assert major >= 3
    if major == 3:
        assert minor >= 9


def test_quick_mode_check():
    """Test dependency check in quick mode."""
    checker = DependencyChecker(str(project_root))
    
    result = checker.check(quick_mode=True)
    
    assert isinstance(result, DependencyCheckResult)
    assert result.python_version is not None
    assert result.status in ["PASS", "WARNING", "FAIL"]


def test_venv_creation_check():
    """Test virtual environment creation check."""
    checker = DependencyChecker(str(project_root))
    
    venv_ok = checker._check_venv_creation()
    
    # Should be able to create venv on a properly configured system
    assert isinstance(venv_ok, bool)
    
    # If it fails, there should be an issue recorded
    if not venv_ok:
        assert len(checker.issues) > 0
        assert any(issue.issue_type == "VENV_CREATION" for issue in checker.issues)


def test_critical_imports_check():
    """Test critical package import checking."""
    checker = DependencyChecker(str(project_root))
    
    all_ok, successful, failed = checker._check_critical_imports()
    
    assert isinstance(all_ok, bool)
    assert isinstance(successful, list)
    assert isinstance(failed, list)
    
    # At least some packages should be checked
    total_checked = len(successful) + len(failed)
    assert total_checked == len(DependencyChecker.CRITICAL_PACKAGES)


def test_parse_installation_errors():
    """Test parsing of pip installation error output."""
    checker = DependencyChecker(str(project_root))
    
    # Test with sample error output
    error_output = """
    ERROR: Could not find a version that satisfies the requirement nonexistent-package
    ERROR: No matching distribution found for nonexistent-package
    """
    
    failed_packages = checker._parse_installation_errors(error_output)
    
    assert isinstance(failed_packages, list)
    assert len(failed_packages) > 0


def test_get_summary():
    """Test summary generation."""
    checker = DependencyChecker(str(project_root))
    
    # Add some test issues
    checker._add_issue(
        issue_type="TEST_ISSUE",
        description="Test issue",
        details="Test details",
        severity="WARNING",
        fix_suggestion="Test fix"
    )
    
    summary = checker.get_summary()
    
    assert isinstance(summary, dict)
    assert "total_issues" in summary
    assert "critical_issues" in summary
    assert "warning_issues" in summary
    assert "python_version" in summary
    assert summary["total_issues"] == 1


def test_get_recommendations():
    """Test recommendations generation."""
    checker = DependencyChecker(str(project_root))
    
    recommendations = checker.get_recommendations()
    
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0
    assert all(isinstance(rec, str) for rec in recommendations)


def test_dev_requirements_exists():
    """Test that dev-requirements.txt exists."""
    checker = DependencyChecker(str(project_root))
    
    assert checker.dev_requirements_path.exists(), \
        f"dev-requirements.txt not found at {checker.dev_requirements_path}"


def test_critical_packages_defined():
    """Test that critical packages are defined."""
    assert len(DependencyChecker.CRITICAL_PACKAGES) > 0
    assert "boto3" in DependencyChecker.CRITICAL_PACKAGES
    assert "streamlit" in DependencyChecker.CRITICAL_PACKAGES
    assert "bedrock_agentcore" in DependencyChecker.CRITICAL_PACKAGES


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
