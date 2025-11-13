"""
Standalone test for dependency checker - tests the module directly.
"""

import sys
import os
from pathlib import Path

# Get the absolute path to the checkers directory
current_dir = Path(__file__).parent
checkers_dir = current_dir / "checkers"
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir.parent))

# Now import the checker
from checkers.dependency_checker import DependencyChecker


def main():
    """Run standalone tests."""
    print("=" * 70)
    print("Dependency Checker - Standalone Test")
    print("=" * 70)
    
    project_root = current_dir.parent
    print(f"\nProject root: {project_root}")
    
    # Initialize checker
    print("\n[1/7] Initializing checker...")
    checker = DependencyChecker(str(project_root))
    print(f"      ✓ Checker initialized")
    print(f"      ✓ Dev requirements path: {checker.dev_requirem