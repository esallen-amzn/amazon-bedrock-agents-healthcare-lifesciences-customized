#!/usr/bin/env python3
"""
Generate a fix script for line ending issues.
This script creates a shell script that can be executed to fix all line ending issues.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from checkers.line_endings_checker import LineEndingsChecker


def main():
    """Generate and save the fix script."""
    # Get the instrument-diagnosis-assistant directory
    project_root = Path(__file__).parent.parent
    
    # Create and run the checker
    checker = LineEndingsChecker(str(project_root))
    result = checker.check()
    
    if not result.issues:
        print("✅ No line ending issues found. All files have Unix line endings (LF)!")
        return 0
    
    # Generate fix script
    fix_script = checker.get_fix_script()
    
    # Save to file
    output_file = Path(__file__).parent / "fix_line_endings_generated.sh"
    output_file.write_text(fix_script)
    
    # Make the fix script executable
    output_file.chmod(0o755)
    
    print(f"✅ Fix script generated: {output_file}")
    print(f"   Found {len(result.issues)} line ending issues")
    print()
    
    # Show breakdown by severity
    critical = [i for i in result.issues if i.severity == "CRITICAL"]
    warnings = [i for i in result.issues if i.severity == "WARNING"]
    
    if critical:
        print(f"   Critical issues: {len(critical)}")
        for issue in critical[:5]:  # Show first 5
            print(f"     - {issue.file_path}")
        if len(critical) > 5:
            print(f"     ... and {len(critical) - 5} more")
    
    if warnings:
        print(f"   Warning issues: {len(warnings)}")
        for issue in warnings[:5]:  # Show first 5
            print(f"     - {issue.file_path}")
        if len(warnings) > 5:
            print(f"     ... and {len(warnings) - 5} more")
    
    print()
    print("To fix all issues, run:")
    print(f"   ./{output_file.relative_to(project_root)}")
    print()
    print("Or run from the project root:")
    print(f"   bash {output_file.relative_to(project_root)}")
    print()
    print("For a safer approach, use the enhanced fix script:")
    print(f"   ./windows-to-mac-migration/fix_line_endings.sh --dry-run  # Preview changes")
    print(f"   ./windows-to-mac-migration/fix_line_endings.sh --backup   # Create backups")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
