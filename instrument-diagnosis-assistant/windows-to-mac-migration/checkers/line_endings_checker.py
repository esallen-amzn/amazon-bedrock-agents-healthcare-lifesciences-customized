"""
Line endings checker for Windows-to-Mac migration.

This module scans for files with Windows line endings (CRLF) and reports them.
It generates fix commands using dos2unix or sed to convert to Unix line endings (LF).
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class LineEndingIssue:
    """Represents a file with Windows line endings."""
    file_path: str
    line_ending_type: str  # "CRLF", "LF", "MIXED"
    total_lines: int
    crlf_count: int
    fix_command: str
    severity: str = "CRITICAL"


@dataclass
class LineEndingsCheckResult:
    """Result of line endings check."""
    status: str  # "PASS", "FAIL", "WARNING"
    issues: List[LineEndingIssue] = field(default_factory=list)
    files_checked: int = 0
    message: str = ""


class LineEndingsChecker:
    """
    Checks for Windows line endings (CRLF) in shell scripts and Python files.
    
    Requirements addressed:
    - 1.2: Detect any files with Windows line endings (CRLF)
    """
    
    def __init__(self, project_root: str):
        """
        Initialize the line endings checker.
        
        Args:
            project_root: Path to the project root directory
        """
        self.project_root = Path(project_root)
        self.issues: List[LineEndingIssue] = []
        
        # File extensions to check
        self.extensions_to_check = {
            '.sh': 'CRITICAL',    # Shell scripts must have LF
            '.py': 'CRITICAL',    # Python files must have LF
            '.yaml': 'WARNING',   # Config files should have LF
            '.yml': 'WARNING',    # Config files should have LF
            '.json': 'WARNING',   # Config files should have LF
            '.txt': 'WARNING',    # Text files should have LF
            '.md': 'WARNING',     # Markdown files should have LF
        }
        
    def check(self) -> LineEndingsCheckResult:
        """
        Run the line endings check on relevant files.
        
        Returns:
            LineEndingsCheckResult with status and any issues found
        """
        self.issues = []
        files_checked = 0
        
        # Find all relevant files
        files_to_check = self._find_files_to_check()
        
        # Check each file for line endings
        for file_path in files_to_check:
            files_checked += 1
            line_ending_info = self._check_line_endings(file_path)
            
            if line_ending_info and line_ending_info['has_crlf']:
                issue = self._create_line_ending_issue(file_path, line_ending_info)
                self.issues.append(issue)
        
        # Determine overall status
        critical_issues = [i for i in self.issues if i.severity == "CRITICAL"]
        
        if len(self.issues) == 0:
            status = "PASS"
            message = f"All {files_checked} files have Unix line endings (LF)"
        elif len(critical_issues) > 0:
            status = "FAIL"
            message = f"Found {len(critical_issues)} critical files with Windows line endings (CRLF)"
        else:
            status = "WARNING"
            message = f"Found {len(self.issues)} files with Windows line endings (CRLF)"
        
        return LineEndingsCheckResult(
            status=status,
            issues=self.issues,
            files_checked=files_checked,
            message=message
        )
    
    def _find_files_to_check(self) -> List[Path]:
        """
        Find all files that should be checked for line endings.
        
        Returns:
            List of Path objects for files to check
        """
        files_to_check = []
        
        # Iterate through the project directory
        for ext in self.extensions_to_check.keys():
            # Use rglob to find files recursively
            for file_path in self.project_root.rglob(f"*{ext}"):
                if file_path.is_file():
                    # Skip hidden directories and common exclusions
                    if self._should_check_file(file_path):
                        files_to_check.append(file_path)
        
        return sorted(set(files_to_check))
    
    def _should_check_file(self, file_path: Path) -> bool:
        """
        Determine if a file should be checked.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file should be checked, False otherwise
        """
        # Skip files in hidden directories
        if any(part.startswith('.') for part in file_path.parts):
            # But allow .kiro directory
            if '.kiro' not in file_path.parts:
                return False
        
        # Skip common exclusions
        exclusions = [
            '__pycache__',
            'node_modules',
            'venv',
            '.venv',
            'build',
            'dist',
            '.git',
        ]
        
        for exclusion in exclusions:
            if exclusion in file_path.parts:
                return False
        
        return True
    
    def _check_line_endings(self, file_path: Path) -> Dict[str, Any]:
        """
        Check the line endings in a file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            Dictionary with line ending information, or None if file can't be read
        """
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Count different line ending types
            crlf_count = content.count(b'\r\n')
            lf_only_count = content.count(b'\n') - crlf_count  # Subtract CRLF occurrences
            cr_only_count = content.count(b'\r') - crlf_count  # Old Mac style (rare)
            
            total_lines = content.count(b'\n') + content.count(b'\r')
            
            # Determine line ending type
            if crlf_count > 0 and lf_only_count > 0:
                line_ending_type = "MIXED"
                has_crlf = True
            elif crlf_count > 0:
                line_ending_type = "CRLF"
                has_crlf = True
            elif lf_only_count > 0:
                line_ending_type = "LF"
                has_crlf = False
            elif cr_only_count > 0:
                line_ending_type = "CR"
                has_crlf = True  # Old Mac, also needs fixing
            else:
                line_ending_type = "NONE"
                has_crlf = False
            
            return {
                'line_ending_type': line_ending_type,
                'total_lines': total_lines,
                'crlf_count': crlf_count,
                'lf_count': lf_only_count,
                'cr_count': cr_only_count,
                'has_crlf': has_crlf
            }
            
        except (OSError, PermissionError, UnicodeDecodeError) as e:
            # Skip files that can't be read or are binary
            return None
    
    def _create_line_ending_issue(self, file_path: Path, line_ending_info: Dict[str, Any]) -> LineEndingIssue:
        """
        Create a LineEndingIssue object for a file with Windows line endings.
        
        Args:
            file_path: Path to the file with line ending issues
            line_ending_info: Dictionary with line ending information
            
        Returns:
            LineEndingIssue object with details and fix command
        """
        # Generate relative path for cleaner output
        try:
            relative_path = file_path.relative_to(self.project_root)
        except ValueError:
            relative_path = file_path
        
        # Determine severity based on file extension
        file_ext = file_path.suffix
        severity = self.extensions_to_check.get(file_ext, "WARNING")
        
        # Generate fix command
        # Try dos2unix first, fall back to sed
        fix_command = self._generate_fix_command(relative_path)
        
        return LineEndingIssue(
            file_path=str(relative_path),
            line_ending_type=line_ending_info['line_ending_type'],
            total_lines=line_ending_info['total_lines'],
            crlf_count=line_ending_info['crlf_count'],
            fix_command=fix_command,
            severity=severity
        )
    
    def _generate_fix_command(self, file_path: Path) -> str:
        """
        Generate a fix command for converting line endings.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Fix command string
        """
        # Provide both dos2unix and sed alternatives
        # dos2unix is cleaner but may not be installed
        # sed is available on all Unix systems
        return f"dos2unix {file_path} || sed -i '' 's/\\r$//' {file_path}"
    
    def get_fix_script(self) -> str:
        """
        Generate a shell script to fix all line ending issues.
        
        Returns:
            Shell script content as a string
        """
        if not self.issues:
            return "# No line ending issues to fix\n"
        
        script_lines = [
            "#!/bin/bash",
            "#",
            "# Auto-generated script to fix line endings",
            "# Generated by Windows-to-Mac migration checker",
            "#",
            "",
            "set -e  # Exit on error",
            "",
            "echo 'Fixing line endings (CRLF -> LF)...'",
            "",
            "# Check if dos2unix is available",
            "if command -v dos2unix &> /dev/null; then",
            "    echo 'Using dos2unix for conversion'",
            "    USE_DOS2UNIX=true",
            "else",
            "    echo 'dos2unix not found, using sed for conversion'",
            "    USE_DOS2UNIX=false",
            "fi",
            "",
        ]
        
        for issue in self.issues:
            script_lines.append(f"echo 'Fixing: {issue.file_path}'")
            script_lines.append(f"if [ \"$USE_DOS2UNIX\" = true ]; then")
            script_lines.append(f"    dos2unix {issue.file_path}")
            script_lines.append(f"else")
            script_lines.append(f"    sed -i '' 's/\\r$//' {issue.file_path}")
            script_lines.append(f"fi")
            script_lines.append("")
        
        script_lines.append("echo 'All line endings fixed successfully!'")
        
        return "\n".join(script_lines)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the line endings check results.
        
        Returns:
            Dictionary with summary information
        """
        critical_issues = [i for i in self.issues if i.severity == "CRITICAL"]
        warning_issues = [i for i in self.issues if i.severity == "WARNING"]
        
        return {
            "total_issues": len(self.issues),
            "critical_issues": len(critical_issues),
            "warning_issues": len(warning_issues),
            "files_with_crlf": [issue.file_path for issue in self.issues],
            "fix_commands": [issue.fix_command for issue in self.issues],
            "critical_files": [issue.file_path for issue in critical_issues],
            "warning_files": [issue.file_path for issue in warning_issues]
        }
