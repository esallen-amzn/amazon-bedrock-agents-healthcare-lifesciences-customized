"""
File permissions checker for Windows-to-Mac migration.

This module scans for shell scripts and verifies they have execute permissions.
It generates fix commands for any permission issues found.
"""

import os
import stat
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class PermissionIssue:
    """Represents a file permission issue."""
    file_path: str
    current_mode: str
    expected_mode: str
    fix_command: str
    severity: str = "CRITICAL"


@dataclass
class PermissionsCheckResult:
    """Result of permissions check."""
    status: str  # "PASS", "FAIL", "WARNING"
    issues: List[PermissionIssue] = field(default_factory=list)
    files_checked: int = 0
    message: str = ""


class PermissionsChecker:
    """
    Checks file permissions on shell scripts for macOS compatibility.
    
    Requirements addressed:
    - 2.1: Set execute permissions on all .sh files in scripts directory
    - 2.2: Set execute permissions on start.sh in root directory
    - 2.3: Verify shell scripts execute without permission errors
    - 2.4: Verify deployment scripts execute without permission errors
    """
    
    def __init__(self, project_root: str):
        """
        Initialize the permissions checker.
        
        Args:
            project_root: Path to the project root directory
        """
        self.project_root = Path(project_root)
        self.issues: List[PermissionIssue] = []
        
    def check(self) -> PermissionsCheckResult:
        """
        Run the permissions check on all shell scripts.
        
        Returns:
            PermissionsCheckResult with status and any issues found
        """
        self.issues = []
        files_checked = 0
        
        # Find all .sh files in the project
        shell_scripts = self._find_shell_scripts()
        
        # Check each shell script for execute permissions
        for script_path in shell_scripts:
            files_checked += 1
            if not self._has_execute_permission(script_path):
                issue = self._create_permission_issue(script_path)
                self.issues.append(issue)
        
        # Determine overall status
        if len(self.issues) == 0:
            status = "PASS"
            message = f"All {files_checked} shell scripts have execute permissions"
        else:
            status = "FAIL"
            message = f"Found {len(self.issues)} shell scripts without execute permissions"
        
        return PermissionsCheckResult(
            status=status,
            issues=self.issues,
            files_checked=files_checked,
            message=message
        )
    
    def _find_shell_scripts(self) -> List[Path]:
        """
        Find all .sh files in the project.
        
        Returns:
            List of Path objects for shell scripts
        """
        shell_scripts = []
        
        # Check for start.sh in root (Requirement 2.2)
        start_sh = self.project_root / "start.sh"
        if start_sh.exists():
            shell_scripts.append(start_sh)
        
        # Check for all .sh files in scripts directory (Requirement 2.1)
        scripts_dir = self.project_root / "scripts"
        if scripts_dir.exists() and scripts_dir.is_dir():
            for script in scripts_dir.glob("*.sh"):
                if script.is_file():
                    shell_scripts.append(script)
        
        # Also check for .sh files in other common locations
        for pattern in ["*.sh", "**/*.sh"]:
            for script in self.project_root.glob(pattern):
                if script.is_file() and script not in shell_scripts:
                    # Skip hidden directories and common exclusions
                    if not any(part.startswith('.') for part in script.parts):
                        shell_scripts.append(script)
        
        return sorted(set(shell_scripts))
    
    def _has_execute_permission(self, file_path: Path) -> bool:
        """
        Check if a file has execute permission for the owner.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file has execute permission, False otherwise
        """
        try:
            file_stat = file_path.stat()
            # Check if owner has execute permission
            return bool(file_stat.st_mode & stat.S_IXUSR)
        except (OSError, PermissionError) as e:
            # If we can't read the file, treat it as not executable
            return False
    
    def _create_permission_issue(self, file_path: Path) -> PermissionIssue:
        """
        Create a PermissionIssue object for a file without execute permissions.
        
        Args:
            file_path: Path to the file with permission issues
            
        Returns:
            PermissionIssue object with details and fix command
        """
        try:
            file_stat = file_path.stat()
            current_mode = oct(file_stat.st_mode)[-3:]
            current_mode_str = f"-rw-r--r-- ({current_mode})"
        except (OSError, PermissionError):
            current_mode_str = "unknown"
        
        expected_mode_str = "-rwxr-xr-x (755)"
        
        # Generate relative path for cleaner output
        try:
            relative_path = file_path.relative_to(self.project_root)
        except ValueError:
            relative_path = file_path
        
        # Generate fix command (Requirement 2.3, 2.4)
        fix_command = f"chmod +x {relative_path}"
        
        return PermissionIssue(
            file_path=str(relative_path),
            current_mode=current_mode_str,
            expected_mode=expected_mode_str,
            fix_command=fix_command,
            severity="CRITICAL"
        )
    
    def get_fix_script(self) -> str:
        """
        Generate a shell script to fix all permission issues.
        
        Returns:
            Shell script content as a string
        """
        if not self.issues:
            return "# No permission issues to fix\n"
        
        script_lines = [
            "#!/bin/bash",
            "#",
            "# Auto-generated script to fix shell script permissions",
            "# Generated by Windows-to-Mac migration checker",
            "#",
            "",
            "set -e  # Exit on error",
            "",
            "echo 'Fixing shell script permissions...'",
            ""
        ]
        
        for issue in self.issues:
            script_lines.append(f"echo 'Fixing: {issue.file_path}'")
            script_lines.append(issue.fix_command)
            script_lines.append("")
        
        script_lines.append("echo 'All permissions fixed successfully!'")
        
        return "\n".join(script_lines)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the permissions check results.
        
        Returns:
            Dictionary with summary information
        """
        return {
            "total_issues": len(self.issues),
            "critical_issues": len([i for i in self.issues if i.severity == "CRITICAL"]),
            "files_with_issues": [issue.file_path for issue in self.issues],
            "fix_commands": [issue.fix_command for issue in self.issues]
        }
