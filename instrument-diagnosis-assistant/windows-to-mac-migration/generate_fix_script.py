#!/usr/bin/env python3
"""
Generate a fix script for permission issues.
This script creates a shell script that can be executed to fix all permission issues.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from checkers.permissions_checker import PermissionsChecker


def main():
    """Generate and save the fix script."""
    # Get the instrument-diagnosis-assistant directory
    project_root = Path(__file__).parent.parent
    
    # Create and run the checker
    checker = PermissionsChecker(str(project_root))
    result = checker.check()
    
    if not result.issues:
        print("✅ No permission issues found. All shell scripts have correct permissions!")
        return 0
    
    # Generate fix script
    fix_script = checker.get_fix_script()
    
    # Save to file
    output_file = Path(__file__).parent / "fix_permissions.sh"
    output_file.write_text(fix_script)
    
    # Make the fix script executable
    output_file.chmod(0o755)
    
    print(f"✅ Fix script generated: {output_file}")
    print(f"   Found {len(result.issues)} permission issues")
    print()
    print("To fix all issues, run:")
    print(f"   ./{output_file.relative_to(project_root)}")
    print()
    print("Or run from the project root:")
    print(f"   bash {output_file.relative_to(project_root)}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
