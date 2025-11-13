"""
Dependency checker for Python environment and packages.

This module verifies that:
- Python 3.12.12 or compatible version is available
- Virtual environment can be created
- Packages from dev-requirements.txt can be installed
- Critical packages (boto3, streamlit, bedrock-agentcore) are importable

Requirements addressed:
- 3.1: Verify Python 3.9 or higher is available
- 3.2: Attempt to create a virtual environment using python3 -m venv
- 3.3: Install all dependencies from dev-requirements.txt
- 3.4: Report specific package and error if any dependency fails to install
- 3.5: Verify critical packages (boto3, streamlit, bedrock-agentcore) are importable
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class DependencyIssue:
    """Represents a dependency-related issue."""
    issue_type: str  # "PYTHON_VERSION", "VENV_CREATION", "PACKAGE_INSTALL", "IMPORT_ERROR"
    description: str
    details: str
    severity: str = "CRITICAL"
    fix_suggestion: str = ""


@dataclass
class DependencyCheckResult:
    """Result of dependency check."""
    status: str  # "PASS", "FAIL", "WARNING"
    issues: List[DependencyIssue] = field(default_factory=list)
    python_version: Optional[str] = None
    venv_created: bool = False
    packages_installed: int = 0
    packages_failed: int = 0
    imports_successful: List[str] = field(default_factory=list)
    imports_failed: List[str] = field(default_factory=list)
    message: str = ""


class DependencyChecker:
    """
    Checks Python environment and package dependencies.
    
    This checker verifies that the development environment is properly
    configured for macOS, including Python version, virtual environment
    support, and package installation.
    """
    
    # Critical packages that must be importable
    CRITICAL_PACKAGES = [
        'boto3',
        'streamlit',
        'bedrock_agentcore',
    ]
    
    # Minimum Python version (3.9.0)
    MIN_PYTHON_VERSION = (3, 9, 0)
    
    # Recommended Python version (3.12.12)
    RECOMMENDED_PYTHON_VERSION = (3, 12, 12)
    
    def __init__(self, project_root: str):
        """
        Initialize the dependency checker.
        
        Args:
            project_root: Path to the project root directory
        """
        self.project_root = Path(project_root)
        self.issues: List[DependencyIssue] = []
        self.dev_requirements_path = self.project_root / "dev-requirements.txt"
        
    def check(self, quick_mode: bool = False) -> DependencyCheckResult:
        """
        Run the dependency check.
        
        Args:
            quick_mode: If True, skip package installation test (faster)
        
        Returns:
            DependencyCheckResult with status and any issues found
        """
        self.issues = []
        result = DependencyCheckResult(status="PASS")
        
        # Check Python version
        python_version, version_ok = self._check_python_version()
        result.python_version = python_version
        
        if not version_ok:
            result.status = "FAIL"
            result.message = f"Python version {python_version} is below minimum required version"
            return result
        
        # Check if dev-requirements.txt exists
        if not self.dev_requirements_path.exists():
            self._add_issue(
                issue_type="MISSING_REQUIREMENTS",
                description="dev-requirements.txt not found",
                details=f"Expected file at: {self.dev_requirements_path}",
                severity="CRITICAL",
                fix_suggestion="Ensure dev-requirements.txt exists in the project root"
            )
            result.status = "FAIL"
            result.message = "dev-requirements.txt not found"
            return result
        
        # In quick mode, only check Python version and skip installation tests
        if quick_mode:
            result.message = f"Python {python_version} is available (quick check only)"
            return result
        
        # Check virtual environment creation
        venv_ok = self._check_venv_creation()
        result.venv_created = venv_ok
        
        if not venv_ok:
            result.status = "FAIL"
            result.message = "Failed to create virtual environment"
            return result
        
        # Check package installation (in a temporary venv)
        packages_ok, installed, failed = self._check_package_installation()
        result.packages_installed = installed
        result.packages_failed = failed
        
        if failed > 0:
            result.status = "FAIL"
            result.message = f"Failed to install {failed} package(s)"
            return result
        
        # Check critical package imports
        imports_ok, successful, failed_imports = self._check_critical_imports()
        result.imports_successful = successful
        result.imports_failed = failed_imports
        
        if not imports_ok:
            result.status = "FAIL"
            result.message = f"Failed to import {len(failed_imports)} critical package(s)"
            return result
        
        # All checks passed
        if len(self.issues) == 0:
            result.status = "PASS"
            result.message = f"Python {python_version} with all dependencies available"
        else:
            result.status = "WARNING"
            result.message = f"Python environment OK with {len(self.issues)} warning(s)"
        
        return result
    
    def _check_python_version(self) -> Tuple[str, bool]:
        """
        Check if Python version meets requirements.
        
        Returns:
            Tuple of (version_string, is_acceptable)
        """
        version_info = sys.version_info
        version_string = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
        
        # Check minimum version
        current_version = (version_info.major, version_info.minor, version_info.micro)
        
        if current_version < self.MIN_PYTHON_VERSION:
            self._add_issue(
                issue_type="PYTHON_VERSION",
                description=f"Python version {version_string} is below minimum required",
                details=f"Minimum required: {'.'.join(map(str, self.MIN_PYTHON_VERSION))}, Found: {version_string}",
                severity="CRITICAL",
                fix_suggestion=f"Install Python {'.'.join(map(str, self.RECOMMENDED_PYTHON_VERSION))} or higher"
            )
            return version_string, False
        
        # Check if it's the recommended version
        if current_version < self.RECOMMENDED_PYTHON_VERSION:
            self._add_issue(
                issue_type="PYTHON_VERSION",
                description=f"Python version {version_string} is below recommended version",
                details=f"Recommended: {'.'.join(map(str, self.RECOMMENDED_PYTHON_VERSION))}, Found: {version_string}",
                severity="WARNING",
                fix_suggestion=f"Consider upgrading to Python {'.'.join(map(str, self.RECOMMENDED_PYTHON_VERSION))}"
            )
        
        return version_string, True
    
    def _check_venv_creation(self) -> bool:
        """
        Test if virtual environment can be created.
        
        Returns:
            True if venv creation succeeds, False otherwise
        """
        # Create a temporary directory for testing
        temp_dir = tempfile.mkdtemp(prefix="venv_test_")
        venv_path = Path(temp_dir) / "test_venv"
        
        try:
            # Try to create a virtual environment
            result = subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self._add_issue(
                    issue_type="VENV_CREATION",
                    description="Failed to create virtual environment",
                    details=f"Error: {result.stderr}",
                    severity="CRITICAL",
                    fix_suggestion="Ensure venv module is available: python3 -m ensurepip"
                )
                return False
            
            # Verify venv was created
            if not venv_path.exists():
                self._add_issue(
                    issue_type="VENV_CREATION",
                    description="Virtual environment directory not created",
                    details=f"Expected directory: {venv_path}",
                    severity="CRITICAL",
                    fix_suggestion="Check Python installation and venv module"
                )
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            self._add_issue(
                issue_type="VENV_CREATION",
                description="Virtual environment creation timed out",
                details="Creation took longer than 30 seconds",
                severity="CRITICAL",
                fix_suggestion="Check system resources and Python installation"
            )
            return False
            
        except Exception as e:
            self._add_issue(
                issue_type="VENV_CREATION",
                description="Unexpected error creating virtual environment",
                details=str(e),
                severity="CRITICAL",
                fix_suggestion="Check Python installation and permissions"
            )
            return False
            
        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass
    
    def _check_package_installation(self) -> Tuple[bool, int, int]:
        """
        Test package installation in a temporary virtual environment.
        
        Returns:
            Tuple of (success, packages_installed, packages_failed)
        """
        # Create a temporary directory for testing
        temp_dir = tempfile.mkdtemp(prefix="pkg_test_")
        venv_path = Path(temp_dir) / "test_venv"
        
        try:
            # Create virtual environment
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)],
                capture_output=True,
                timeout=30,
                check=True
            )
            
            # Determine pip executable path
            if sys.platform == "win32":
                pip_executable = venv_path / "Scripts" / "pip"
            else:
                pip_executable = venv_path / "bin" / "pip"
            
            # Upgrade pip first
            subprocess.run(
                [str(pip_executable), "install", "--upgrade", "pip"],
                capture_output=True,
                timeout=60
            )
            
            # Try to install packages from dev-requirements.txt
            result = subprocess.run(
                [str(pip_executable), "install", "-r", str(self.dev_requirements_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode != 0:
                # Parse error output to identify failed packages
                error_output = result.stderr
                failed_packages = self._parse_installation_errors(error_output)
                
                for package_name, error_msg in failed_packages:
                    self._add_issue(
                        issue_type="PACKAGE_INSTALL",
                        description=f"Failed to install package: {package_name}",
                        details=error_msg,
                        severity="CRITICAL",
                        fix_suggestion=f"Check package availability and compatibility: pip install {package_name}"
                    )
                
                return False, 0, len(failed_packages)
            
            # Count installed packages
            list_result = subprocess.run(
                [str(pip_executable), "list", "--format=freeze"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if list_result.returncode == 0:
                installed_count = len([line for line in list_result.stdout.split('\n') if line.strip()])
            else:
                installed_count = 0
            
            return True, installed_count, 0
            
        except subprocess.TimeoutExpired:
            self._add_issue(
                issue_type="PACKAGE_INSTALL",
                description="Package installation timed out",
                details="Installation took longer than 5 minutes",
                severity="CRITICAL",
                fix_suggestion="Check network connectivity and package repository availability"
            )
            return False, 0, 1
            
        except Exception as e:
            self._add_issue(
                issue_type="PACKAGE_INSTALL",
                description="Unexpected error during package installation",
                details=str(e),
                severity="CRITICAL",
                fix_suggestion="Check pip installation and network connectivity"
            )
            return False, 0, 1
            
        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass
    
    def _check_critical_imports(self) -> Tuple[bool, List[str], List[str]]:
        """
        Test if critical packages can be imported.
        
        Returns:
            Tuple of (all_successful, successful_imports, failed_imports)
        """
        successful = []
        failed = []
        
        for package_name in self.CRITICAL_PACKAGES:
            try:
                # Try to import the package
                __import__(package_name)
                successful.append(package_name)
                
            except ImportError as e:
                failed.append(package_name)
                self._add_issue(
                    issue_type="IMPORT_ERROR",
                    description=f"Failed to import critical package: {package_name}",
                    details=str(e),
                    severity="CRITICAL",
                    fix_suggestion=f"Install the package: pip install {package_name}"
                )
            except Exception as e:
                failed.append(package_name)
                self._add_issue(
                    issue_type="IMPORT_ERROR",
                    description=f"Unexpected error importing {package_name}",
                    details=str(e),
                    severity="CRITICAL",
                    fix_suggestion=f"Check package installation: pip install --force-reinstall {package_name}"
                )
        
        return len(failed) == 0, successful, failed
    
    def _parse_installation_errors(self, error_output: str) -> List[Tuple[str, str]]:
        """
        Parse pip installation error output to identify failed packages.
        
        Args:
            error_output: stderr from pip install command
        
        Returns:
            List of (package_name, error_message) tuples
        """
        failed_packages = []
        
        # Common error patterns
        error_patterns = [
            r"ERROR: Could not find a version that satisfies the requirement (\S+)",
            r"ERROR: No matching distribution found for (\S+)",
            r"ERROR: Failed building wheel for (\S+)",
            r"error: subprocess-exited-with-error.*?× pip subprocess to install build dependencies.*?(\S+)",
        ]
        
        import re
        for pattern in error_patterns:
            matches = re.finditer(pattern, error_output, re.MULTILINE | re.DOTALL)
            for match in matches:
                package_name = match.group(1)
                # Extract relevant error context
                error_context = error_output[max(0, match.start() - 200):match.end() + 200]
                failed_packages.append((package_name, error_context.strip()))
        
        # If no specific packages identified, report general failure
        if not failed_packages and "ERROR" in error_output:
            failed_packages.append(("unknown", error_output[:500]))
        
        return failed_packages
    
    def _add_issue(self, issue_type: str, description: str, details: str,
                   severity: str, fix_suggestion: str) -> None:
        """
        Add a dependency issue to the list.
        
        Args:
            issue_type: Type of issue
            description: Short description
            details: Detailed information
            severity: Issue severity
            fix_suggestion: Suggested fix
        """
        issue = DependencyIssue(
            issue_type=issue_type,
            description=description,
            details=details,
            severity=severity,
            fix_suggestion=fix_suggestion
        )
        
        self.issues.append(issue)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the dependency check results.
        
        Returns:
            Dictionary with summary information
        """
        critical_issues = [i for i in self.issues if i.severity == "CRITICAL"]
        warning_issues = [i for i in self.issues if i.severity == "WARNING"]
        
        # Group issues by type
        issues_by_type = {}
        for issue in self.issues:
            if issue.issue_type not in issues_by_type:
                issues_by_type[issue.issue_type] = []
            issues_by_type[issue.issue_type].append(issue)
        
        return {
            "total_issues": len(self.issues),
            "critical_issues": len(critical_issues),
            "warning_issues": len(warning_issues),
            "issues_by_type": {k: len(v) for k, v in issues_by_type.items()},
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        }
    
    def get_recommendations(self) -> List[str]:
        """
        Get general recommendations for dependency management.
        
        Returns:
            List of recommendation strings
        """
        recommendations = [
            f"Use Python {'.'.join(map(str, self.RECOMMENDED_PYTHON_VERSION))} or higher for best compatibility",
            "Create a virtual environment before installing packages: python3 -m venv .venv",
            "Activate the virtual environment: source .venv/bin/activate (macOS/Linux)",
            "Install dependencies: pip install -r dev-requirements.txt",
            "Keep pip updated: pip install --upgrade pip",
            "Use 'pip list' to verify installed packages",
            "Test critical imports after installation",
            "Consider using 'uv' for faster package installation on macOS",
        ]
        
        return recommendations
