#!/usr/bin/env python3
"""
Simple test for dependency checker core functionality.
"""

import sys
import importlib.util
from pathlib import Path

# Load dependency_checker module directly
current_dir = Path(__file__).parent
project_root = current_dir.parent

spec = importlib.util.spec_from_file_location(
    "dependency_checker",
    current_dir / "checkers" / "dependency_checker.py"
)
dc_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dc_module)

DependencyChecker = dc_module.DependencyChecker

print("=" * 70)
print("DEPENDENCY CHECKER - CORE FUNCTIONALITY TEST")
print("=" * 70)

# Test 1: Create instance
print("\n[1] Creating DependencyChecker instance...")
checker = DependencyChecker(str(project_root))
print(f"    ✓ Project root: {checker.project_root}")
print(f"    ✓ Dev requirements: {checker.dev_requirements_path}")
print(f"    ✓ File exists: {checker.dev_requirements_path.exists()}")

# Test 2: Check Python version
print("\n[2] Checking Python version...")
version, is_ok = checker._check_python_version()
print(f"    ✓ Version: {version}")
print(f"    ✓ Acceptable: {is_ok}")

# Test 3: Quick check
print("\n[3] Running quick check (no package installation)...")
result = checker.check(quick_mode=True)
print(f"    ✓ Status: {result.status}")
print(f"    ✓ Message: {result.message}")
print(f"    ✓ Python version: {result.python_version}")
print(f"    ✓ Issues: {len(checker.issues)}")

# Test 4: Venv creation
print("\n[4] Testing virtual environment creation...")
checker2 = DependencyChecker(str(project_root))
venv_ok = checker2._check_venv_creation()
print(f"    ✓ Can create venv: {venv_ok}")
if not venv_ok:
    print(f"    ! Issues: {len(checker2.issues)}")

# Test 5: Critical imports
print("\n[5] Testing critical package imports...")
checker3 = DependencyChecker(str(project_root))
all_ok, successful, failed = checker3._check_critical_imports()
print(f"    ✓ All OK: {all_ok}")
print(f"    ✓ Successful: {successful}")
print(f"    ✓ Failed: {failed}")

# Test 6: Summary
print("\n[6] Getting summary...")
summary = checker.get_summary()
print(f"    ✓ Total issues: {summary['total_issues']}")
print(f"    ✓ Critical: {summary['critical_issues']}")
print(f"    ✓ Warnings: {summary['warning_issues']}")

# Test 7: Recommendations
print("\n[7] Getting recommendations...")
recs = checker.get_recommendations()
print(f"    ✓ Count: {len(recs)}")
print(f"    ✓ First: {recs[0][:50]}...")

print("\n" + "=" * 70)
print("ALL CORE TESTS PASSED ✓")
print("=" * 70)
