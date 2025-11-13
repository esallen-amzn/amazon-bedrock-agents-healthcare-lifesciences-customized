# Path Checker

The Path Checker scans Python files for Windows-specific path patterns and suggests cross-platform alternatives.

## What It Detects

### Critical Issues

1. **Windows Drive Letters** (e.g., `C:/`, `D:\`)
   - Pattern: `[A-Za-z]:[\\/]`
   - Example: `config_path = "C:/Users/Admin/config.yaml"`
   - Suggestion: Use `pathlib.Path()` or `os.path.join()` for cross-platform paths

2. **Windows Executables** (e.g., `.exe`, `.bat`, `.cmd`)
   - Pattern: Files ending with `.exe`, `.bat`, `.cmd`, `.ps1`
   - Example: `subprocess.run(["notepad.exe", "file.txt"])`
   - Suggestion: Use cross-platform executable names or check platform with `sys.platform`

### Warning Issues

3. **Hardcoded Backslashes** in path strings
   - Pattern: Backslashes in string literals (excluding escape sequences)
   - Example: `log_file = "logs\\application.log"`
   - Suggestion: Use forward slashes or `pathlib.Path()` for cross-platform compatibility

4. **Path Concatenation with +** operator
   - Pattern: String concatenation with path separators
   - Example: `full_path = base_path + "/documents"`
   - Suggestion: Use `os.path.join()` or `pathlib.Path()` / operator

5. **os.system() Calls**
   - Pattern: `os.system()` function calls
   - Example: `os.system("cmd.exe /c dir")`
   - Suggestion: Use `subprocess.run()` with `shell=False` for better cross-platform support

### Info Issues

6. **os.sep Usage**
   - Pattern: Direct use of `os.sep`
   - Example: `path = "folder" + os.sep + "file.txt"`
   - Suggestion: Use `pathlib.Path()` / operator instead

7. **subprocess with shell=True**
   - Pattern: subprocess calls with `shell=True`
   - Example: `subprocess.run("ls -la", shell=True)`
   - Suggestion: Avoid `shell=True` for better cross-platform compatibility

## Usage

### Standalone Usage

```python
from checkers.path_checker import PathChecker

# Create checker
checker = PathChecker("/path/to/project")

# Run check
result = checker.check()

# Display results
print(f"Status: {result.status}")
print(f"Files checked: {result.files_checked}")
print(f"Issues found: {len(result.issues)}")

# Get summary
summary = checker.get_summary()
print(f"Critical issues: {summary['critical_issues']}")
print(f"Warning issues: {summary['warning_issues']}")

# Get recommendations
recommendations = checker.get_recommendations()
for rec in recommendations:
    print(f"- {rec}")
```

### Integrated with Test Infrastructure

```python
from test_migration import MigrationTester
from checkers.path_checker_adapter import PathCheckerAdapter

# Create tester
tester = MigrationTester("/path/to/project")

# Register path checker
path_checker = PathCheckerAdapter("/path/to/project")
tester.register_checker(path_checker)

# Run all checks
report = tester.run_all_checks()
```

## Cross-Platform Best Practices

### ✅ Recommended Approaches

1. **Use pathlib.Path for all path operations**
   ```python
   from pathlib import Path
   
   config = Path.home() / "config" / "settings.yaml"
   data_dir = Path("/data/projects")
   ```

2. **Use forward slashes in string literals**
   ```python
   # Works on all platforms
   resource = "resources/images/logo.png"
   ```

3. **Use os.path.join() for dynamic paths**
   ```python
   import os
   log_path = os.path.join("logs", "application.log")
   ```

4. **Use subprocess.run() with list arguments**
   ```python
   import subprocess
   subprocess.run(["python", "script.py"], shell=False)
   ```

5. **Check platform before platform-specific code**
   ```python
   import sys
   if sys.platform == "win32":
       # Windows-specific code
   elif sys.platform == "darwin":
       # macOS-specific code
   ```

### ❌ Avoid These Patterns

1. **Hardcoded drive letters**
   ```python
   # Bad
   config = "C:/Users/Admin/config.yaml"
   
   # Good
   config = Path.home() / "config.yaml"
   ```

2. **Backslashes in paths**
   ```python
   # Bad
   log_file = "logs\\application.log"
   
   # Good
   log_file = Path("logs") / "application.log"
   ```

3. **String concatenation for paths**
   ```python
   # Bad
   full_path = base_path + "/" + filename
   
   # Good
   full_path = Path(base_path) / filename
   ```

4. **Platform-specific executables**
   ```python
   # Bad
   subprocess.run(["notepad.exe", "file.txt"])
   
   # Good
   import sys
   if sys.platform == "win32":
       subprocess.run(["notepad.exe", "file.txt"])
   else:
       subprocess.run(["nano", "file.txt"])
   ```

## Testing

Run the path checker tests:

```bash
# Test on sample files with known patterns
python test_path_samples.py

# Test on the full project
python test_path_checker.py

# Integration test with migration tester
python test_path_integration.py
```

## Output Example

```
======================================================================
Testing Path Checker for Windows-specific patterns
======================================================================

Project root: /path/to/project
Status: WARNING
Files checked: 45
Message: Found 12 potential path issues in Python files

Found 12 path issues:
----------------------------------------------------------------------

DRIVE_LETTER (2 issues):
----------------------------------------------------------------------
  File: app/config.py:15
  Pattern: C:/Users/Admin
  Line: config_path = "C:/Users/Admin/config.yaml"...
  Severity: CRITICAL
  Suggestion: Use pathlib.Path() or os.path.join() for cross-platform paths

BACKSLASH (3 issues):
----------------------------------------------------------------------
  File: utils/logger.py:23
  Pattern: logs\\application.log
  Line: log_file = "logs\\application.log"...
  Severity: WARNING
  Suggestion: Use forward slashes or pathlib.Path() for cross-platform compatibility

======================================================================
Summary
======================================================================
Total issues: 12
Critical issues: 4
Warning issues: 6
Info issues: 2

Issues by type:
  DRIVE_LETTER: 2
  BACKSLASH: 3
  WINDOWS_EXE: 2
  PATH_CONCAT: 3
  OS_SEP: 1
  SUBPROCESS_SHELL: 1

Files with issues: 8
  app/config.py: 2 issue(s)
  utils/logger.py: 3 issue(s)
  scripts/deploy.py: 1 issue(s)
  ...

======================================================================
Recommendations for Cross-Platform Path Handling
======================================================================
1. Use pathlib.Path() for all path operations - it's cross-platform by default
2. Use Path('/') operator for joining paths instead of os.path.join()
3. Use forward slashes in string literals - they work on all platforms
4. Avoid os.system() - use subprocess.run() with a list of arguments
5. Check sys.platform before running platform-specific code
6. Use Path.home() instead of hardcoded user directories
7. Use Path.cwd() instead of hardcoded working directories
8. Test your code on multiple platforms before deployment
```

## Requirements Addressed

This checker addresses the following requirements from the Windows-to-Mac migration spec:

- **1.3**: Identify any hardcoded Windows-style paths
- **5.1**: Scan for Windows path separators (backslash) in Python code
- **5.2**: Identify os.system() calls with Windows-specific commands
- **5.3**: Detect subprocess calls using Windows executables (.exe, .bat)
- **5.4**: Suggest cross-platform alternatives
- **5.5**: Verify all file I/O operations use os.path.join() or pathlib
