# Windows-to-Mac Migration Testing Tools

This directory contains automated testing tools to identify and fix compatibility issues when migrating the Instrument Diagnosis Assistant from Windows to macOS.

## Architecture

### Core Components

- **models.py**: Data models for test results, issues, fixes, and reports
- **test_migration.py**: Main orchestrator that coordinates all checkers and generates reports
- **checkers/**: Individual checker modules for different compatibility aspects
- **test_infrastructure.py**: Verification tests for the infrastructure

### Data Models

- **Issue**: Represents a migration issue (severity, category, file path, description, impact)
- **Fix**: Represents a fix for an issue (command, description, auto-applicable flag, risk level)
- **TestResult**: Result from running a single checker (status, message, issues, fixes)
- **ReportSummary**: Summary statistics (total checks, passed/failed/warnings, issue counts)
- **ActionItem**: Prioritized action item with commands to execute
- **TestReport**: Complete test report with all results and action items

### Main Orchestrator

The `MigrationTester` class provides:
- **File Discovery**: Scans project for shell scripts, Python files, and config files
- **Checker Registration**: Manages multiple checker modules
- **Test Execution**: Runs all checkers and aggregates results
- **Report Generation**: Creates console and markdown formatted reports
- **Fix Application**: Applies automated fixes for common issues

## Usage

### Basic Usage

Run all migration tests on the current project:

```bash
python3 windows-to-mac-migration/test_migration.py
```

Run tests on a specific project directory:

```bash
python3 windows-to-mac-migration/test_migration.py /path/to/project
```

### Command-Line Options

```bash
# Show help
python3 windows-to-mac-migration/test_migration.py --help

# Run quick diagnostic checks only
python3 windows-to-mac-migration/test_migration.py --quick

# Generate markdown report
python3 windows-to-mac-migration/test_migration.py --output markdown

# Save report to file
python3 windows-to-mac-migration/test_migration.py --output-file reports/migration_report.md

# Apply automated fixes
python3 windows-to-mac-migration/test_migration.py --auto-fix
```

## Automated Fix Scripts

This toolkit includes safe, automated fix scripts for common migration issues. See [README_FIX_SCRIPTS.md](README_FIX_SCRIPTS.md) for detailed documentation.

### Quick Start

```bash
# 1. Preview what would be fixed (recommended)
./windows-to-mac-migration/fix_permissions.sh --dry-run
./windows-to-mac-migration/fix_line_endings.sh --dry-run

# 2. Apply fixes with backups (safe)
./windows-to-mac-migration/fix_permissions.sh --backup
./windows-to-mac-migration/fix_line_endings.sh --backup

# 3. Or apply fixes without backups (faster)
./windows-to-mac-migration/fix_permissions.sh
./windows-to-mac-migration/fix_line_endings.sh
```

### Available Fix Scripts

- **fix_permissions.sh**: Fixes execute permissions on shell scripts
- **fix_line_endings.sh**: Converts Windows line endings (CRLF) to Unix (LF)

Both scripts include:
- ✅ Dry-run mode to preview changes
- ✅ Optional backup creation
- ✅ Validation and error handling
- ✅ Detailed logging and statistics
- ✅ Colored output for easy reading

### Example Output

```
🔍 Windows-to-Mac Migration Test

[1/6] Checking file permissions... ❌ FAIL (5 issues)
[2/6] Checking line endings...     ✅ PASS
[3/6] Checking paths...            ⚠️  WARNING (2 issues)
[4/6] Checking dependencies...     ✅ PASS
[5/6] Checking AWS setup...        ⚠️  WARNING (credentials not configured)
[6/6] Generating report...         ✅ DONE

Summary:
--------------------------------------------------
Total Checks: 6
Passed: 2
Failed: 1
Warnings: 2
Skipped: 1

Critical Issues: 5
Warnings: 2
Info: 0

Next Steps:
--------------------------------------------------
1. Fix 5 issue(s) in File Permissions Checker
   chmod +x scripts/prereq.sh
   chmod +x scripts/cleanup.sh
   chmod +x start.sh
```

## Testing the Infrastructure

Verify the infrastructure is working correctly:

```bash
python3 windows-to-mac-migration/test_infrastructure.py
```

This will test:
- All data models can be instantiated
- File discovery works
- Checker registration works
- Test execution works
- Report generation works (console and markdown)

## Checkers

### Currently Implemented

- **permissions_checker.py**: Scans for shell scripts and verifies execute permissions
- **line_endings_checker.py**: Detects Windows line endings (CRLF) in shell scripts and Python files
- **path_checker.py**: Identifies Windows-specific path patterns in Python code

### Planned Checkers

Additional checkers will be added for:
- Python dependencies
- AWS connectivity

### Path Checker

The Path Checker scans Python files for Windows-specific patterns including:

- **Critical Issues**:
  - Windows drive letters (C:, D:, etc.)
  - Windows executables (.exe, .bat, .cmd)

- **Warning Issues**:
  - Hardcoded backslashes in paths
  - Path concatenation with + operator
  - os.system() calls

- **Info Issues**:
  - os.sep usage
  - subprocess with shell=True

See [checkers/README_PATH_CHECKER.md](checkers/README_PATH_CHECKER.md) for detailed documentation.

#### Testing the Path Checker

```bash
# Test on sample files with known patterns
python3 windows-to-mac-migration/test_path_samples.py

# Test on the full project
python3 windows-to-mac-migration/test_path_checker.py

# Integration test with migration tester
python3 windows-to-mac-migration/test_path_integration.py
```

## Requirements Addressed

This infrastructure addresses the following requirements:

- **Requirement 1.1-1.5**: Identify all Windows-to-Mac compatibility issues
- **Requirement 7.1-7.5**: Generate comprehensive test reports with categorized issues

## Development

### Adding a New Checker

1. Create a new checker class that inherits from `BaseChecker`:

```python
from checkers import BaseChecker
from models import TestResult, Issue, Fix

class MyChecker(BaseChecker):
    @property
    def name(self) -> str:
        return "My Checker"
    
    def check(self) -> TestResult:
        # Implement checking logic
        issues = []
        fixes = []
        
        # ... perform checks ...
        
        return TestResult(
            checker_name=self.name,
            status="PASS" if not issues else "FAIL",
            message="Check completed",
            issues=issues,
            fixes=fixes
        )
```

2. Register the checker in `test_migration.py`:

```python
from checkers.my_checker import MyChecker

# In main():
tester.register_checker(MyChecker(args.project_root))
```

## Next Steps

The infrastructure is now ready for implementing individual checkers in subsequent tasks.
