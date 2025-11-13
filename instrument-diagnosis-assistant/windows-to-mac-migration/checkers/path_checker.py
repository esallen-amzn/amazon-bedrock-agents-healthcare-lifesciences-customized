"""
Path checker for Windows-specific patterns.

This module scans Python files for Windows-specific path patterns including:
- Hardcoded backslashes in paths
- Windows drive letters (C:, D:, etc.)
- Incorrect path concatenation patterns
- Non-cross-platform path operations

It suggests cross-platform alternatives using pathlib.
"""

import os
import re
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class PathIssue:
    """Represents a Windows-specific path pattern issue."""
    file_path: str
    line_number: int
    line_content: str
    issue_type: str  # "BACKSLASH", "DRIVE_LETTER", "PATH_CONCAT", "OS_SEP"
    pattern_found: str
    suggestion: str
    severity: str = "WARNING"


@dataclass
class PathCheckResult:
    """Result of path pattern check."""
    status: str  # "PASS", "FAIL", "WARNING"
    issues: List[PathIssue] = field(default_factory=list)
    files_checked: int = 0
    message: str = ""


class PathChecker:
    """
    Checks for Windows-specific path patterns in Python files.
    
    Requirements addressed:
    - 1.3: Identify any hardcoded Windows-style paths
    - 5.1: Scan for Windows path separators (backslash) in Python code
    - 5.2: Identify os.system() calls with Windows-specific commands
    - 5.3: Detect subprocess calls using Windows executables (.exe, .bat)
    - 5.4: Suggest cross-platform alternatives
    - 5.5: Verify all file I/O operations use os.path.join() or pathlib
    """
    
    def __init__(self, project_root: str):
        """
        Initialize the path checker.
        
        Args:
            project_root: Path to the project root directory
        """
        self.project_root = Path(project_root)
        self.issues: List[PathIssue] = []
        
        # Patterns to detect Windows-specific paths
        self.patterns = {
            # Windows drive letters: C:, D:, etc.
            'DRIVE_LETTER': re.compile(r'["\']([A-Za-z]:[\\/])', re.IGNORECASE),
            
            # Hardcoded backslashes in strings (but not escape sequences)
            'BACKSLASH': re.compile(r'["\']([^"\']*\\+[^"\'nrtbfv\\][^"\']*)'),
            
            # Windows executables
            'WINDOWS_EXE': re.compile(r'["\']([^"\']*\.(exe|bat|cmd|ps1))["\']', re.IGNORECASE),
            
            # Path concatenation with + operator
            'PATH_CONCAT': re.compile(r'(\w+)\s*\+\s*["\'][/\\]'),
        }
        
    def check(self) -> PathCheckResult:
        """
        Run the path pattern check on Python files.
        
        Returns:
            PathCheckResult with status and any issues found
        """
        self.issues = []
        files_checked = 0
        
        # Find all Python files
        python_files = self._find_python_files()
        
        # Check each file for path issues
        for file_path in python_files:
            files_checked += 1
            self._check_file(file_path)
        
        # Determine overall status
        critical_issues = [i for i in self.issues if i.severity == "CRITICAL"]
        
        if len(self.issues) == 0:
            status = "PASS"
            message = f"No Windows-specific path patterns found in {files_checked} Python files"
        elif len(critical_issues) > 0:
            status = "FAIL"
            message = f"Found {len(critical_issues)} critical path issues in Python files"
        else:
            status = "WARNING"
            message = f"Found {len(self.issues)} potential path issues in Python files"
        
        return PathCheckResult(
            status=status,
            issues=self.issues,
            files_checked=files_checked,
            message=message
        )
    
    def _find_python_files(self) -> List[Path]:
        """
        Find all Python files in the project.
        
        Returns:
            List of Path objects for Python files
        """
        python_files = []
        
        for file_path in self.project_root.rglob("*.py"):
            if file_path.is_file() and self._should_check_file(file_path):
                python_files.append(file_path)
        
        return sorted(python_files)
    
    def _should_check_file(self, file_path: Path) -> bool:
        """
        Determine if a file should be checked.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file should be checked, False otherwise
        """
        # Skip common exclusions
        exclusions = [
            '__pycache__',
            'node_modules',
            'venv',
            '.venv',
            'build',
            'dist',
            '.git',
            '.pytest_cache',
            '.mypy_cache',
            'site-packages',
        ]
        
        for exclusion in exclusions:
            if exclusion in file_path.parts:
                return False
        
        return True
    
    def _check_file(self, file_path: Path) -> None:
        """
        Check a single Python file for path issues.
        
        Args:
            file_path: Path to the Python file to check
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Check each line for patterns
            for line_num, line in enumerate(lines, start=1):
                self._check_line(file_path, line_num, line)
            
            # Also parse the AST for more sophisticated checks
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                tree = ast.parse(content, filename=str(file_path))
                self._check_ast(file_path, tree, lines)
            except SyntaxError:
                # Skip files with syntax errors
                pass
                
        except (OSError, PermissionError, UnicodeDecodeError):
            # Skip files that can't be read
            pass
    
    def _check_line(self, file_path: Path, line_num: int, line: str) -> None:
        """
        Check a single line for path issues.
        
        Args:
            file_path: Path to the file
            line_num: Line number
            line: Line content
        """
        # Skip comments and docstrings
        stripped = line.strip()
        if stripped.startswith('#'):
            return
        
        # Check for drive letters
        drive_match = self.patterns['DRIVE_LETTER'].search(line)
        if drive_match:
            self._add_issue(
                file_path=file_path,
                line_number=line_num,
                line_content=line.strip(),
                issue_type="DRIVE_LETTER",
                pattern_found=drive_match.group(1),
                suggestion="Use pathlib.Path() or os.path.join() for cross-platform paths",
                severity="CRITICAL"
            )
        
        # Check for hardcoded backslashes (excluding escape sequences)
        backslash_match = self.patterns['BACKSLASH'].search(line)
        if backslash_match:
            # Additional validation: make sure it's not a regex or escape sequence
            matched_text = backslash_match.group(1)
            if self._is_likely_path(matched_text):
                self._add_issue(
                    file_path=file_path,
                    line_number=line_num,
                    line_content=line.strip(),
                    issue_type="BACKSLASH",
                    pattern_found=matched_text,
                    suggestion="Use forward slashes or pathlib.Path() for cross-platform compatibility",
                    severity="WARNING"
                )
        
        # Check for Windows executables
        exe_match = self.patterns['WINDOWS_EXE'].search(line)
        if exe_match:
            self._add_issue(
                file_path=file_path,
                line_number=line_num,
                line_content=line.strip(),
                issue_type="WINDOWS_EXE",
                pattern_found=exe_match.group(1),
                suggestion="Use cross-platform executable names or check platform with sys.platform",
                severity="CRITICAL"
            )
        
        # Check for path concatenation with +
        concat_match = self.patterns['PATH_CONCAT'].search(line)
        if concat_match:
            self._add_issue(
                file_path=file_path,
                line_number=line_num,
                line_content=line.strip(),
                issue_type="PATH_CONCAT",
                pattern_found=line.strip(),
                suggestion="Use os.path.join() or pathlib.Path() / operator instead of string concatenation",
                severity="WARNING"
            )
    
    def _check_ast(self, file_path: Path, tree: ast.AST, lines: List[str]) -> None:
        """
        Check the AST for more sophisticated path issues.
        
        Args:
            file_path: Path to the file
            tree: Parsed AST
            lines: File lines for context
        """
        for node in ast.walk(tree):
            # Check os.system() calls
            if isinstance(node, ast.Call):
                if self._is_os_system_call(node):
                    line_num = node.lineno
                    line_content = lines[line_num - 1].strip() if line_num <= len(lines) else ""
                    
                    self._add_issue(
                        file_path=file_path,
                        line_number=line_num,
                        line_content=line_content,
                        issue_type="OS_SYSTEM",
                        pattern_found="os.system()",
                        suggestion="Use subprocess.run() with shell=False for better cross-platform support",
                        severity="WARNING"
                    )
                
                # Check subprocess calls with shell=True
                if self._is_subprocess_shell_call(node):
                    line_num = node.lineno
                    line_content = lines[line_num - 1].strip() if line_num <= len(lines) else ""
                    
                    self._add_issue(
                        file_path=file_path,
                        line_number=line_num,
                        line_content=line_content,
                        issue_type="SUBPROCESS_SHELL",
                        pattern_found="subprocess with shell=True",
                        suggestion="Avoid shell=True for better cross-platform compatibility",
                        severity="INFO"
                    )
            
            # Check for os.sep usage (should use pathlib instead)
            if isinstance(node, ast.Attribute):
                if (isinstance(node.value, ast.Name) and 
                    node.value.id == 'os' and 
                    node.attr == 'sep'):
                    line_num = node.lineno
                    line_content = lines[line_num - 1].strip() if line_num <= len(lines) else ""
                    
                    self._add_issue(
                        file_path=file_path,
                        line_number=line_num,
                        line_content=line_content,
                        issue_type="OS_SEP",
                        pattern_found="os.sep",
                        suggestion="Use pathlib.Path() / operator instead of os.sep",
                        severity="INFO"
                    )
    
    def _is_os_system_call(self, node: ast.Call) -> bool:
        """Check if a call node is os.system()."""
        if isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Name) and 
                node.func.value.id == 'os' and 
                node.func.attr == 'system'):
                return True
        return False
    
    def _is_subprocess_shell_call(self, node: ast.Call) -> bool:
        """Check if a call node is subprocess with shell=True."""
        # Check if it's a subprocess call
        is_subprocess = False
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'subprocess':
                is_subprocess = True
        elif isinstance(node.func, ast.Name) and node.func.id in ['run', 'call', 'Popen']:
            is_subprocess = True
        
        if not is_subprocess:
            return False
        
        # Check for shell=True keyword argument
        for keyword in node.keywords:
            if keyword.arg == 'shell':
                if isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                    return True
        
        return False
    
    def _is_likely_path(self, text: str) -> bool:
        """
        Determine if a string with backslashes is likely a file path.
        
        Args:
            text: String to check
            
        Returns:
            True if likely a path, False otherwise
        """
        # Common path indicators
        path_indicators = [
            'users', 'program', 'windows', 'system', 'temp', 'documents',
            'desktop', 'downloads', 'appdata', 'local', 'roaming',
            'src', 'lib', 'bin', 'data', 'config', 'scripts'
        ]
        
        text_lower = text.lower()
        
        # Check for path indicators
        for indicator in path_indicators:
            if indicator in text_lower:
                return True
        
        # Check for multiple backslashes (likely a path)
        if text.count('\\') >= 2:
            return True
        
        # Check for file extensions
        if re.search(r'\.\w{2,4}$', text):
            return True
        
        return False
    
    def _add_issue(self, file_path: Path, line_number: int, line_content: str,
                   issue_type: str, pattern_found: str, suggestion: str,
                   severity: str) -> None:
        """
        Add a path issue to the list.
        
        Args:
            file_path: Path to the file
            line_number: Line number where issue was found
            line_content: Content of the line
            issue_type: Type of issue
            pattern_found: The problematic pattern
            suggestion: Suggested fix
            severity: Issue severity
        """
        try:
            relative_path = file_path.relative_to(self.project_root)
        except ValueError:
            relative_path = file_path
        
        issue = PathIssue(
            file_path=str(relative_path),
            line_number=line_number,
            line_content=line_content,
            issue_type=issue_type,
            pattern_found=pattern_found,
            suggestion=suggestion,
            severity=severity
        )
        
        self.issues.append(issue)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the path check results.
        
        Returns:
            Dictionary with summary information
        """
        critical_issues = [i for i in self.issues if i.severity == "CRITICAL"]
        warning_issues = [i for i in self.issues if i.severity == "WARNING"]
        info_issues = [i for i in self.issues if i.severity == "INFO"]
        
        # Group issues by type
        issues_by_type = {}
        for issue in self.issues:
            if issue.issue_type not in issues_by_type:
                issues_by_type[issue.issue_type] = []
            issues_by_type[issue.issue_type].append(issue)
        
        # Group issues by file
        issues_by_file = {}
        for issue in self.issues:
            if issue.file_path not in issues_by_file:
                issues_by_file[issue.file_path] = []
            issues_by_file[issue.file_path].append(issue)
        
        return {
            "total_issues": len(self.issues),
            "critical_issues": len(critical_issues),
            "warning_issues": len(warning_issues),
            "info_issues": len(info_issues),
            "issues_by_type": {k: len(v) for k, v in issues_by_type.items()},
            "issues_by_file": {k: len(v) for k, v in issues_by_file.items()},
            "files_with_issues": list(issues_by_file.keys()),
            "critical_files": list(set(i.file_path for i in critical_issues)),
        }
    
    def get_recommendations(self) -> List[str]:
        """
        Get general recommendations for cross-platform path handling.
        
        Returns:
            List of recommendation strings
        """
        recommendations = [
            "Use pathlib.Path() for all path operations - it's cross-platform by default",
            "Use Path('/') operator for joining paths instead of os.path.join()",
            "Use forward slashes in string literals - they work on all platforms",
            "Avoid os.system() - use subprocess.run() with a list of arguments",
            "Check sys.platform before running platform-specific code",
            "Use Path.home() instead of hardcoded user directories",
            "Use Path.cwd() instead of hardcoded working directories",
            "Test your code on multiple platforms before deployment",
        ]
        
        return recommendations
