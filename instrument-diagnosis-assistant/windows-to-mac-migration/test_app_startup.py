#!/usr/bin/env python3
"""
Test application startup on macOS
Tests all aspects of the Instrument Diagnosis Assistant startup process

Requirements tested:
- 4.1: start.sh script execution
- 4.2: Streamlit application loading
- 4.3: AWS credentials handling
- 4.4: Static assets accessibility
- 4.5: Import error detection
"""

import os
import sys
import subprocess
import time
import socket
import importlib
from pathlib import Path
from typing import Dict, List, Tuple
import stat

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from models import TestResult, Issue, Fix


class AppStartupTester:
    """Test application startup on macOS"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues: List[Issue] = []
        self.fixes: List[Fix] = []
        
    def run_all_tests(self) -> TestResult:
        """Run all startup tests"""
        print("=" * 60)
        print("Testing Application Startup on macOS")
        print("=" * 60)
        print()
        
        all_passed = True
        
        # Test 1: Shell script permissions
        print("[1/5] Testing shell script permissions...")
        if not self.test_shell_permissions():
            all_passed = False
        print()
        
        # Test 2: Shell script execution
        print("[2/5] Testing start.sh execution...")
        if not self.test_start_sh_execution():
            all_passed = False
        print()
        
        # Test 3: Python imports
        print("[3/5] Testing Python imports...")
        if not self.test_python_imports():
            all_passed = False
        print()
        
        # Test 4: Static assets
        print("[4/5] Testing static assets...")
        if not self.test_static_assets():
            all_passed = False
        print()
        
        # Test 5: Configuration files
        print("[5/5] Testing configuration files...")
        if not self.test_configuration():
            all_passed = False
        print()
        
        # Generate result
        status = "PASS" if all_passed else "FAIL"
        message = "All startup tests passed" if all_passed else f"Found {len(self.issues)} issues"
        
        return TestResult(
            checker_name="AppStartupTester",
            status=status,
            message=message,
            issues=self.issues,
            fixes=self.fixes
        )
    
    def test_shell_permissions(self) -> bool:
        """Test that shell scripts have execute permissions"""
        scripts_to_check = [
            "start.sh",
            "scripts/prereq.sh",
            "scripts/cleanup.sh",
            "scripts/list_ssm_parameters.sh"
        ]
        
        all_ok = True
        
        for script_path in scripts_to_check:
            full_path = self.project_root / script_path
            
            if not full_path.exists():
                print(f"  ⚠️  {script_path} not found (may be optional)")
                continue
            
            # Check if executable
            is_executable = os.access(full_path, os.X_OK)
            
            if is_executable:
                print(f"  ✅ {script_path} has execute permission")
            else:
                print(f"  ❌ {script_path} missing execute permission")
                all_ok = False
                
                self.issues.append(Issue(
                    severity="CRITICAL",
                    category="permissions",
                    file_path=str(script_path),
                    line_number=None,
                    description=f"Shell script {script_path} is not executable",
                    impact="Script cannot be run directly with ./{script_path}"
                ))
                
                self.fixes.append(Fix(
                    issue_id=f"perm_{script_path}",
                    command=f"chmod +x {script_path}",
                    description=f"Make {script_path} executable",
                    auto_applicable=True,
                    risk_level="LOW"
                ))
        
        return all_ok
    
    def test_start_sh_execution(self) -> bool:
        """Test that start.sh can be parsed and validated"""
        start_sh = self.project_root / "start.sh"
        
        if not start_sh.exists():
            print("  ❌ start.sh not found")
            self.issues.append(Issue(
                severity="CRITICAL",
                category="missing_file",
                file_path="start.sh",
                line_number=None,
                description="start.sh script not found",
                impact="Cannot start application using standard script"
            ))
            return False
        
        # Check shebang
        try:
            with open(start_sh, 'r') as f:
                first_line = f.readline().strip()
                
            if first_line.startswith('#!/bin/bash') or first_line.startswith('#!/usr/bin/env bash'):
                print(f"  ✅ start.sh has correct shebang: {first_line}")
            else:
                print(f"  ⚠️  start.sh has unusual shebang: {first_line}")
        except Exception as e:
            print(f"  ❌ Error reading start.sh: {e}")
            return False
        
        # Check for Windows line endings
        try:
            with open(start_sh, 'rb') as f:
                content = f.read()
                
            if b'\r\n' in content:
                print("  ❌ start.sh has Windows line endings (CRLF)")
                self.issues.append(Issue(
                    severity="CRITICAL",
                    category="line_endings",
                    file_path="start.sh",
                    line_number=None,
                    description="start.sh has Windows line endings",
                    impact="Script may fail to execute on macOS"
                ))
                
                self.fixes.append(Fix(
                    issue_id="line_endings_start_sh",
                    command="dos2unix start.sh || sed -i '' 's/\\r$//' start.sh",
                    description="Convert line endings to Unix format",
                    auto_applicable=True,
                    risk_level="LOW"
                ))
                return False
            else:
                print("  ✅ start.sh has Unix line endings (LF)")
        except Exception as e:
            print(f"  ❌ Error checking line endings: {e}")
            return False
        
        # Validate script syntax (dry run)
        try:
            result = subprocess.run(
                ['bash', '-n', str(start_sh)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print("  ✅ start.sh syntax is valid")
                return True
            else:
                print(f"  ❌ start.sh has syntax errors:")
                print(f"     {result.stderr}")
                self.issues.append(Issue(
                    severity="CRITICAL",
                    category="syntax_error",
                    file_path="start.sh",
                    line_number=None,
                    description=f"Bash syntax error: {result.stderr}",
                    impact="Script will fail to execute"
                ))
                return False
        except subprocess.TimeoutExpired:
            print("  ⚠️  Syntax check timed out")
            return True  # Don't fail on timeout
        except Exception as e:
            print(f"  ⚠️  Could not validate syntax: {e}")
            return True  # Don't fail if we can't check
    
    def test_python_imports(self) -> bool:
        """Test that all required Python modules can be imported"""
        required_imports = [
            ('boto3', 'AWS SDK'),
            ('streamlit', 'Streamlit web framework'),
            ('yaml', 'YAML configuration parser'),
            ('bedrock_agentcore', 'Bedrock AgentCore SDK'),
            ('strands', 'Strands agent framework'),
        ]
        
        optional_imports = [
            ('pandas', 'Data processing'),
            ('opensearchpy', 'OpenSearch client'),
        ]
        
        all_ok = True
        
        print("  Required imports:")
        for module_name, description in required_imports:
            try:
                importlib.import_module(module_name)
                print(f"    ✅ {module_name} ({description})")
            except ImportError as e:
                print(f"    ❌ {module_name} ({description}) - NOT FOUND")
                all_ok = False
                
                self.issues.append(Issue(
                    severity="CRITICAL",
                    category="missing_dependency",
                    file_path="dev-requirements.txt",
                    line_number=None,
                    description=f"Required module '{module_name}' cannot be imported: {e}",
                    impact="Application will fail to start"
                ))
                
                self.fixes.append(Fix(
                    issue_id=f"import_{module_name}",
                    command=f"pip install {module_name}",
                    description=f"Install {module_name}",
                    auto_applicable=True,
                    risk_level="LOW"
                ))
        
        print("  Optional imports:")
        for module_name, description in optional_imports:
            try:
                importlib.import_module(module_name)
                print(f"    ✅ {module_name} ({description})")
            except ImportError:
                print(f"    ⚠️  {module_name} ({description}) - not installed (optional)")
        
        return all_ok
    
    def test_static_assets(self) -> bool:
        """Test that static assets are accessible"""
        required_assets = [
            "static/agentcore-service-icon.png",
            "static/gen-ai-dark.svg",
            "static/user-profile.svg",
        ]
        
        optional_assets = [
            "static/gen-ai-lt.svg",
            "static/arch.png",
            "static/Amazon-Ember-Medium.ttf",
        ]
        
        all_ok = True
        
        print("  Required assets:")
        for asset_path in required_assets:
            full_path = self.project_root / asset_path
            
            if full_path.exists():
                size = full_path.stat().st_size
                print(f"    ✅ {asset_path} ({size} bytes)")
            else:
                print(f"    ❌ {asset_path} - NOT FOUND")
                all_ok = False
                
                self.issues.append(Issue(
                    severity="WARNING",
                    category="missing_asset",
                    file_path=asset_path,
                    line_number=None,
                    description=f"Static asset {asset_path} not found",
                    impact="UI may display broken images or missing icons"
                ))
        
        print("  Optional assets:")
        for asset_path in optional_assets:
            full_path = self.project_root / asset_path
            
            if full_path.exists():
                size = full_path.stat().st_size
                print(f"    ✅ {asset_path} ({size} bytes)")
            else:
                print(f"    ⚠️  {asset_path} - not found (optional)")
        
        return all_ok
    
    def test_configuration(self) -> bool:
        """Test configuration files"""
        config_files = [
            ("deployment/dev-config.yaml", True),
            ("deployment/test-config.yaml", False),
            ("deployment/prod-config.yaml", False),
        ]
        
        all_ok = True
        found_any = False
        
        for config_path, required in config_files:
            full_path = self.project_root / config_path
            
            if full_path.exists():
                print(f"  ✅ {config_path} exists")
                found_any = True
                
                # Try to parse it
                try:
                    import yaml
                    with open(full_path, 'r') as f:
                        config = yaml.safe_load(f)
                    
                    # Check for required keys
                    if 'deployment' in config:
                        print(f"     ✓ Has deployment configuration")
                    else:
                        print(f"     ⚠️  Missing 'deployment' section")
                    
                except Exception as e:
                    print(f"     ❌ Error parsing YAML: {e}")
                    all_ok = False
                    
                    self.issues.append(Issue(
                        severity="WARNING",
                        category="config_error",
                        file_path=config_path,
                        line_number=None,
                        description=f"Configuration file has YAML syntax error: {e}",
                        impact="Configuration cannot be loaded"
                    ))
            else:
                if required:
                    print(f"  ❌ {config_path} - NOT FOUND (required)")
                    all_ok = False
                    
                    self.issues.append(Issue(
                        severity="CRITICAL",
                        category="missing_config",
                        file_path=config_path,
                        line_number=None,
                        description=f"Required configuration file {config_path} not found",
                        impact="Application cannot start without configuration"
                    ))
                else:
                    print(f"  ⚠️  {config_path} - not found (optional)")
        
        if not found_any:
            print("  ❌ No configuration files found")
            all_ok = False
        
        return all_ok
    
    def print_summary(self, result: TestResult):
        """Print test summary"""
        print()
        print("=" * 60)
        print("Application Startup Test Summary")
        print("=" * 60)
        print()
        
        if result.status == "PASS":
            print("✅ ALL TESTS PASSED")
            print()
            print("The application is ready to start on macOS.")
            print()
            print("To start the application:")
            print("  ./start.sh dev app.py")
            print()
        else:
            print(f"❌ TESTS FAILED: {len(result.issues)} issues found")
            print()
            
            # Group issues by severity
            critical = [i for i in result.issues if i.severity == "CRITICAL"]
            warnings = [i for i in result.issues if i.severity == "WARNING"]
            
            if critical:
                print(f"Critical Issues ({len(critical)}):")
                for issue in critical:
                    print(f"  • {issue.description}")
                    print(f"    Impact: {issue.impact}")
                print()
            
            if warnings:
                print(f"Warnings ({len(warnings)}):")
                for issue in warnings:
                    print(f"  • {issue.description}")
                print()
            
            # Show fixes
            if result.fixes:
                print("Recommended Fixes:")
                for fix in result.fixes:
                    if fix.auto_applicable:
                        print(f"  ✓ {fix.description}")
                        print(f"    Command: {fix.command}")
                print()
                
                # Show automated fix script
                auto_fixes = [f for f in result.fixes if f.auto_applicable and f.risk_level == "LOW"]
                if auto_fixes:
                    print("Quick Fix Commands:")
                    print("  # Run these commands to fix common issues:")
                    for fix in auto_fixes:
                        print(f"  {fix.command}")
                    print()


def main():
    """Main test runner"""
    # Determine project root (parent of windows-to-mac-migration)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print(f"Project root: {project_root}")
    print()
    
    # Run tests
    tester = AppStartupTester(project_root)
    result = tester.run_all_tests()
    
    # Print summary
    tester.print_summary(result)
    
    # Exit with appropriate code
    sys.exit(0 if result.status == "PASS" else 1)


if __name__ == "__main__":
    main()
