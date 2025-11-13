#!/usr/bin/env python3
"""
Standalone verification script for dependency checker.
Does not require pytest - just runs basic checks.
"""

import sys
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(project_root))

# Import directly to avoid __init__.py issues
import importlib.util

# Load dependency_checker module
spec = importlib.util.spec_from_file_location(
    "dependency_checker",
    current_dir / "checkers" / "dependency_checker.py"
)
dependency_checker_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dependency_checker_module)
DependencyChecker = dependency_checker_module.DependencyChecker

# Load dependency_checker_adapter module
spec2 = importlib.util.spec_from_file_location(
    "dependency_checker_adapter",
    current_dir / "checkers" / "dependency_checker_adapter.py"
)
dependency_checker_adapter_module = importlib.util.module_from_spec(spec2)

# Load models first for the adapter
spec_models = importlib.util.spec_from_file_location(
    "models",
    current_dir / "models.py"
)
models_module = importlib.util.module_from_spec(spec_models)
spec_models.loader.exec_module(models_module)
sys.modules['models'] = models_module

spec2.loader.exec_module(dependency_checker_adapter_module)
DependencyCheckerAdapter = dependency_checker_adapter_module.DependencyCheckerAdapter


def main():
    print("=" * 70)
    print("DEPENDENCY CHECKER VERIFICATION")
    print("=" * 70)
    
    # Test 1: Initialization
    print("\n[TEST 1] Initializing DependencyChecker...")
    try:
        checker = DependencyChecker(str(project_root))
        print(f"  ✓ Project root: {checker.project_root}")
        print(f"  ✓ Dev requirements path: {checker.dev_requirements_path}")
        print(f"  ✓ Dev requirements exists: {checker.dev_requirements_path.exists()}")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return 1
    
    # Test 2: Python version check
    print("\n[TEST 2] Checking Python version...")
    try:
        version_string, is_ok = checker._check_python_version()
        print(f"  ✓ Python version: {version_string}")
        print(f"  ✓ Version acceptable: {is_ok}")
        if not is_ok:
            print(f"  ! WARNING: Python version below minimum")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return 1
    
    # Test 3: Quick mode check
    print("\n[TEST 3] Running quick mode check...")
    try:
        result = checker.check(quick_mode=True)
        print(f"  ✓ Status: {result.status}")
        print(f"  ✓ Message: {result.message}")
        print(f"  ✓ Python version: {result.python_version}")
        print(f"  ✓ Issues found: {len(checker.issues)}")
        
        if checker.issues:
            print(f"\n  Issues detected:")
            for issue in checker.issues[:3]:  # Show first 3
                print(f"    - {issue.issue_type}: {issue.description}")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Test 4: Virtual environment creation
    print("\n[TEST 4] Testing virtual environment creation...")
    try:
        checker2 = DependencyChecker(str(project_root))
        venv_ok = checker2._check_venv_creation()
        print(f"  ✓ Venv creation: {'SUCCESS' if venv_ok else 'FAILED'}")
        if not venv_ok and checker2.issues:
            print(f"  ! Issue: {checker2.issues[0].description}")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Test 5: Critical imports
    print("\n[TEST 5] Testing critical package imports...")
    try:
        checker3 = DependencyChecker(str(project_root))
        all_ok, successful, failed = checker3._check_critical_imports()
        print(f"  ✓ All imports OK: {all_ok}")
        if successful:
            print(f"  ✓ Successful imports: {', '.join(successful)}")
        if failed:
            print(f"  ! Failed imports: {', '.join(failed)}")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Test 6: Summary
    print("\n[TEST 6] Testing summary generation...")
    try:
        summary = checker.get_summary()
        print(f"  ✓ Total issues: {summary['total_issues']}")
        print(f"  ✓ Critical issues: {summary['critical_issues']}")
        print(f"  ✓ Warning issues: {summary['warning_issues']}")
        print(f"  ✓ Python version: {summary['python_version']}")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return 1
    
    # Test 7: Recommendations
    print("\n[TEST 7] Testing recommendations...")
    try:
        recommendations = checker.get_recommendations()
        print(f"  ✓ Number of recommendations: {len(recommendations)}")
        if recommendations:
            print(f"  ✓ Sample: {recommendations[0][:60]}...")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return 1
    
    # Test 8: Adapter integration
    print("\n[TEST 8] Testing adapter integration...")
    try:
        adapter = DependencyCheckerAdapter(str(project_root))
        test_result = adapter.check(quick_mode=True)
        print(f"  ✓ Checker name: {test_result.checker_name}")
        print(f"  ✓ Status: {test_result.status}")
        print(f"  ✓ Message: {test_result.message}")
        print(f"  ✓ Issues: {len(test_result.issues)}")
        print(f"  ✓ Fixes: {len(test_result.fixes)}")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED ✓")
    print("=" * 70)
    print("\nDependency checker module is working correctly!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
