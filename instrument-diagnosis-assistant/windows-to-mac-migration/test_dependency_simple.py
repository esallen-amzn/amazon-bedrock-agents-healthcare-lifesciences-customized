"""
Simple test script for dependency checker (no pytest required).
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from windows_to_mac_migration.checkers.dependency_checker import DependencyChecker
from windows_to_mac_migration.checkers.dependency_checker_adapter import DependencyCheckerAdapter


def test_dependency_checker():
    """Test the dependency checker."""
    print("=" * 60)
    print("Testing Dependency Checker")
    print("=" * 60)
    
    # Test initialization
    print("\n1. Testing initialization...")
    checker = DependencyChecker(str(project_root))
    print(f"   ✓ Project root: {checker.project_root}")
    print(f"   ✓ Dev requirements: {checker.dev_requirements_path}")
    print(f"   ✓ Dev requirements exists: {checker.dev_requirements_path.exists()}")
    
    # Test Python version check
    print("\n2. Testing Python version check...")
    version_string, is_ok = checker._check_python_version()
    print(f"   ✓ Python version: {version_string}")
    print(f"   ✓ Version acceptable: {is_ok}")
    
    # Test quick mode
    print("\n3. Testing quick mode check...")
    result = checker.check(quick_mode=True)
    print(f"   ✓ Status: {result.status}")
    print(f"   ✓ Message: {result.message}")
    print(f"   ✓ Python version: {result.python_version}")
    print(f"   ✓ Issues found: {len(checker.issues)}")
    
    # Test venv creation
    print("\n4. Testing virtual environment creation...")
    checker2 = DependencyChecker(str(project_root))
    venv_ok = checker2._check_venv_creation()
    print(f"   ✓ Venv creation: {'SUCCESS' if venv_ok else 'FAILED'}")
    if not venv_ok and checker2.issues:
        print(f"   ! Issue: {checker2.issues[0].description}")
    
    # Test critical imports
    print("\n5. Testing critical package imports...")
    checker3 = DependencyChecker(str(project_root))
    all_ok, successful, failed = checker3._check_critical_imports()
    print(f"   ✓ All imports OK: {all_ok}")
    print(f"   ✓ Successful imports: {', '.join(successful) if successful else 'None'}")
    print(f"   ✓ Failed imports: {', '.join(failed) if failed else 'None'}")
    
    # Test summary
    print("\n6. Testing summary generation...")
    summary = checker.get_summary()
    print(f"   ✓ Total issues: {summary['total_issues']}")
    print(f"   ✓ Critical issues: {summary['critical_issues']}")
    print(f"   ✓ Warning issues: {summary['warning_issues']}")
    print(f"   ✓ Python version: {summary['python_version']}")
    
    # Test recommendations
    print("\n7. Testing recommendations...")
    recommendations = checker.get_recommendations()
    print(f"   ✓ Number of recommendations: {len(recommendations)}")
    if recommendations:
        print(f"   ✓ First recommendation: {recommendations[0][:60]}...")
    
    # Test adapter
    print("\n8. Testing adapter integration...")
    adapter = DependencyCheckerAdapter(str(project_root))
    test_result = adapter.check(quick_mode=True)
    print(f"   ✓ Checker name: {test_result.checker_name}")
    print(f"   ✓ Status: {test_result.status}")
    print(f"   ✓ Message: {test_result.message}")
    print(f"   ✓ Issues: {len(test_result.issues)}")
    print(f"   ✓ Fixes: {len(test_result.fixes)}")
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_dependency_checker()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
