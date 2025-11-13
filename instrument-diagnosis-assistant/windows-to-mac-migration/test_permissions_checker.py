#!/usr/bin/env python3
"""
Simple test script for the permissions checker.
Run this to verify the permissions checker is working correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from checkers.permissions_checker import PermissionsChecker


def main():
    """Run a simple test of the permissions checker."""
    print("=" * 60)
    print("Testing Permissions Checker")
    print("=" * 60)
    print()
    
    # Get the instrument-diagnosis-assistant directory
    project_root = Path(__file__).parent.parent
    print(f"Project root: {project_root}")
    print()
    
    # Create and run the checker
    checker = PermissionsChecker(str(project_root))
    print("Running permissions check...")
    result = checker.check()
    
    # Display results
    print()
    print(f"Status: {result.status}")
    print(f"Files checked: {result.files_checked}")
    print(f"Message: {result.message}")
    print()
    
    if result.issues:
        print(f"Found {len(result.issues)} issues:")
        print("-" * 60)
        for i, issue in enumerate(result.issues, 1):
            print(f"\n{i}. {issue.file_path}")
            print(f"   Current:  {issue.current_mode}")
            print(f"   Expected: {issue.expected_mode}")
            print(f"   Fix:      {issue.fix_command}")
        
        print()
        print("=" * 60)
        print("Fix Script Preview:")
        print("=" * 60)
        print(checker.get_fix_script())
        
        print()
        print("Summary:")
        summary = checker.get_summary()
        for key, value in summary.items():
            print(f"  {key}: {value}")
    else:
        print("✅ All shell scripts have correct permissions!")
    
    print()
    return 0 if result.status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
