"""
Test the path checker on sample files with known Windows patterns.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from checkers.path_checker import PathChecker


def main():
    """Test path checker on sample files."""
    print("=" * 70)
    print("Testing Path Checker on Sample Files")
    print("=" * 70)
    print()
    
    # Test on the test_samples directory
    test_samples_dir = Path(__file__).parent / "test_samples"
    
    if not test_samples_dir.exists():
        print(f"❌ Test samples directory not found: {test_samples_dir}")
        return 1
    
    print(f"Testing directory: {test_samples_dir}")
    print()
    
    # Create and run checker
    checker = PathChecker(str(test_samples_dir))
    result = checker.check()
    
    print(f"Status: {result.status}")
    print(f"Files checked: {result.files_checked}")
    print(f"Message: {result.message}")
    print()
    
    if result.issues:
        print(f"✅ Successfully detected {len(result.issues)} issues:")
        print("-" * 70)
        
        # Group by type
        issues_by_type = {}
        for issue in result.issues:
            if issue.issue_type not in issues_by_type:
                issues_by_type[issue.issue_type] = []
            issues_by_type[issue.issue_type].append(issue)
        
        for issue_type, issues in sorted(issues_by_type.items()):
            print(f"\n{issue_type} ({len(issues)} found):")
            for issue in issues:
                print(f"  Line {issue.line_number}: {issue.pattern_found}")
                print(f"  Severity: {issue.severity}")
                print(f"  Suggestion: {issue.suggestion}")
                print()
    else:
        print("❌ No issues detected (expected to find issues in sample file)")
        return 1
    
    # Verify expected patterns were found
    print("\n" + "=" * 70)
    print("Verification")
    print("=" * 70)
    
    expected_types = {
        "DRIVE_LETTER": 2,  # C: and D:
        "BACKSLASH": 2,     # logs\ and temp\
        "WINDOWS_EXE": 2,   # notepad.exe and cmd.exe
        "PATH_CONCAT": 1,   # base_path + "/"
        "OS_SEP": 2,        # os.sep usage
        "SUBPROCESS_SHELL": 1,  # shell=True
    }
    
    all_passed = True
    for issue_type, expected_count in expected_types.items():
        actual_count = len(issues_by_type.get(issue_type, []))
        status = "✅" if actual_count >= expected_count else "❌"
        print(f"{status} {issue_type}: expected >={expected_count}, found {actual_count}")
        if actual_count < expected_count:
            all_passed = False
    
    print()
    if all_passed:
        print("✅ All expected patterns detected successfully!")
        return 0
    else:
        print("⚠️  Some expected patterns were not detected")
        return 1


if __name__ == "__main__":
    sys.exit(main())
